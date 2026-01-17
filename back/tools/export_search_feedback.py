"""
Firestore `search_feedback` 컬렉션을 JSONL로 덤프하는 도구.

사용법:
    python back/tools/export_search_feedback.py --status approved --limit 500 --out back/data/training/search_feedback.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys

BACK_DIR = Path(__file__).resolve().parents[1]
if str(BACK_DIR) not in sys.path:
    sys.path.insert(0, str(BACK_DIR))

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB


def fetch_feedback(status: Optional[str], limit: int) -> List[Dict[str, Any]]:
    col = FIRESTORE_DB.collection("search_feedback")
    query = col
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    try:
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        docs = list(query.stream())
    except Exception:
        # 인덱스가 없으면 정렬을 생략하고 단순 limit로 다시 시도
        query = query.limit(limit)
        docs = list(query.stream())
    results: List[Dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict() or {}
        # 타임스탬프 직렬화
        created_at = data.get("created_at")
        if hasattr(created_at, "isoformat"):
            data["created_at"] = created_at.isoformat()
        approved_at = data.get("approved_at")
        if hasattr(approved_at, "isoformat"):
            data["approved_at"] = approved_at.isoformat()
        rejected_at = data.get("rejected_at")
        if hasattr(rejected_at, "isoformat"):
            data["rejected_at"] = rejected_at.isoformat()
        data["id"] = doc.id
        results.append(data)
    return results


def dump_jsonl(items: List[Dict[str, Any]], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        for item in items:
            fp.write(json.dumps(item, ensure_ascii=False) + "\n")
    return len(items)


def main():
    parser = argparse.ArgumentParser(description="Export search_feedback collection to JSONL.")
    parser.add_argument("--status", default="approved", help="feedback status filter (default: approved, use empty for all)")
    parser.add_argument("--limit", type=int, default=500, help="max documents to export")
    parser.add_argument(
        "--out",
        default="back/data/training/search_feedback.jsonl",
        help="output JSONL path",
    )
    args = parser.parse_args()

    status = args.status if args.status else None
    records = fetch_feedback(status=status, limit=args.limit)
    count = dump_jsonl(records, Path(args.out))
    print(f"exported {count} feedback entries to {args.out}")


if __name__ == "__main__":
    main()
