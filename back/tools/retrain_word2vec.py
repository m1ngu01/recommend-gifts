"""
Retrain Word2Vec embeddings using exported log data (search_logs, search_feedback, user_logs).

Usage example:
    python back/tools/retrain_word2vec.py --inputs back/data/exports/search_logs_*.jsonl --out back/model/artifacts
"""

import argparse
import glob
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from gensim.models import Word2Vec

TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")

DEFAULT_KEYS = [
    "sentence",
    "search_sentence",
    "payload.sentence",
    "payload.input_sentence",
]


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    tokens = TOKEN_RE.findall(text.lower())
    return [tok for tok in tokens if tok]


def extract_from_dict(data: dict, key_path: str) -> str:
    current = data
    for part in key_path.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
    return current if isinstance(current, str) else ""


def load_corpus(paths: Iterable[str], min_length: int = 2) -> Tuple[List[List[str]], List[str]]:
    corpus: List[List[str]] = []
    seen: Set[str] = set()
    matched_files: Set[str] = set()
    for pattern in paths:
        for filename in glob.glob(pattern):
            matched_files.add(filename)
            with open(filename, "r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text_candidates = []
                    for key in DEFAULT_KEYS:
                        value = extract_from_dict(data, key)
                        if value:
                            text_candidates.append(value)
                    for text in text_candidates:
                        fingerprint = f"{filename}:{hash(text)}"
                        if fingerprint in seen:
                            continue
                        seen.add(fingerprint)
                        tokens = tokenize(text)
                        if len(tokens) >= min_length:
                            corpus.append(tokens)
    return corpus, sorted(matched_files)


def main():
    parser = argparse.ArgumentParser(description="Retrain Word2Vec from exported logs.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Glob patterns for JSONL files (e.g., back/data/exports/search_logs_*.jsonl)",
    )
    parser.add_argument(
        "--out",
        default=str(Path("back") / "model" / "artifacts"),
        help="Directory to store trained models",
    )
    parser.add_argument("--vector-size", type=int, default=100)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--sg", type=int, default=1, choices=[0, 1], help="Word2Vec training algorithm (0=CBOW,1=SG)")
    args = parser.parse_args()

    corpus, source_files = load_corpus(args.inputs)
    if not source_files:
        raise SystemExit("No input files matched the provided patterns.")
    if not corpus:
        raise SystemExit("Corpus is empty. Provide valid export files.")

    print(f"[retrain] Loaded {len(corpus)} sentences for training.")
    model = Word2Vec(
        sentences=corpus,
        vector_size=args.vector_size,
        window=args.window,
        min_count=args.min_count,
        sg=args.sg,
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    newest_mtime = 0.0
    for filename in source_files:
        try:
            newest_mtime = max(newest_mtime, Path(filename).stat().st_mtime)
        except OSError:
            continue
    if newest_mtime > 0:
        timestamp = datetime.utcfromtimestamp(newest_mtime).strftime("%Y%m%dT%H%M%S")
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    model_path = out_dir / f"word2vec_logs_{timestamp}.model"
    model.save(str(model_path))
    print(f"[retrain] Saved Word2Vec model → {model_path}")


if __name__ == "__main__":
    main()
