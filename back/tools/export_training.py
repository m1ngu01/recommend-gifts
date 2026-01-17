"""
Export training-ready records by joining search_logs and search_feedback.

Usage:
    python back/tools/export_training.py --out back/data/training --limit 5000 --status approved
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from model.service.common import FIRESTORE_DB  # noqa: E402


def _load_search_logs(limit: int) -> Dict[str, Dict[str, Any]]:
    logs: Dict[str, Dict[str, Any]] = {}
    query = (
        FIRESTORE_DB.collection("search_logs")
        .order_by("created_at", direction=2)  # firestore.Query.DESCENDING == 2
        .limit(limit)
    )
    for doc in query.stream():
        payload = doc.to_dict() or {}
        payload["id"] = doc.id
        logs[doc.id] = payload
    return logs


def _iter_feedback(status: Optional[str]) -> Iterable[Dict[str, Any]]:
    col = FIRESTORE_DB.collection("search_feedback")
    query = col
    if status:
        query = query.where("status", "==", status)
    for doc in query.stream():
        payload = doc.to_dict() or {}
        payload["id"] = doc.id
        yield payload


def build_training_rows(logs: Dict[str, Dict[str, Any]], status: Optional[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for fb in _iter_feedback(status):
        log_id = fb.get("search_log_id")
        log_entry = logs.get(log_id) if log_id else None
        row = {
            "search_log_id": log_id,
            "feedback_id": fb.get("id"),
            "feedback": {
                "answer": fb.get("answer"),
                "reason": fb.get("reason"),
                "status": fb.get("status"),
                "user_email": fb.get("user_email"),
                "created_at": fb.get("created_at"),
            },
            "query": None,
            "slots": {},
            "results": [],
            "user_email": None,
            "created_at": None,
        }
        if log_entry:
            row["query"] = log_entry.get("sentence")
            row["slots"] = (log_entry.get("metadata") or {}).get("slots") or {}
            row["results"] = (log_entry.get("metadata") or {}).get("results") or []
            row["user_email"] = log_entry.get("user_email")
            row["created_at"] = log_entry.get("created_at")
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Export training records from Firestore logs/feedback")
    parser.add_argument("--out", type=Path, default=Path("back/data/training"), help="Output directory")
    parser.add_argument("--limit", type=int, default=5000, help="Max search logs to read for joins")
    parser.add_argument(
        "--status",
        type=str,
        default="approved",
        help="Filter feedback status (approved/pending). Use empty string for all.",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outfile = args.out / f"training_{ts}.jsonl"

    logs = _load_search_logs(limit=args.limit)
    rows = build_training_rows(logs, status=args.status or None)

    with outfile.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"exported {len(rows)} rows -> {outfile}")


if __name__ == "__main__":
    main()
