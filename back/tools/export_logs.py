"""
Export Firestore logs (user_logs, search_logs, search_feedback) to JSONL files.

Usage:
    python back/tools/export_logs.py --out back/data/exports --limit 5000
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from model.service.common import FIRESTORE_DB  # noqa: E402

DEFAULT_COLLECTIONS = ["user_logs", "search_logs", "search_feedback"]


def serialize_value(value: Any) -> Any:
    try:
        from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
    except ImportError:
        DatetimeWithNanoseconds = tuple()

    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialize_value(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if DatetimeWithNanoseconds and isinstance(value, DatetimeWithNanoseconds):
        return value.isoformat()
    return value


def export_collection(name: str, output_dir: Path, limit: int | None):
    collection = FIRESTORE_DB.collection(name)
    docs = collection.stream()
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = output_dir / f"{name}_{ts}.jsonl"
    count = 0
    with out_path.open("w", encoding="utf-8") as fp:
        for doc in docs:
            data = doc.to_dict() or {}
            row: Dict[str, Any] = {"id": doc.id, **serialize_value(data)}
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
            if limit and count >= limit:
                break
    print(f"[export] {name}: wrote {count} rows → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Export Firestore log collections.")
    parser.add_argument(
        "--collections",
        nargs="+",
        default=DEFAULT_COLLECTIONS,
        help="List of collections to export",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "exports"),
        help="Output directory for JSONL files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of documents per collection",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    for name in args.collections:
        export_collection(name, out_dir, args.limit)


if __name__ == "__main__":
    main()
