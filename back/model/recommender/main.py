"""
사용법:
    pip install pandas numpy scikit-learn gensim
    python main.py --query "여사친 생일 3만 이하, 향 강한 건 싫어" [--k 12 --hard_budget]

이 스크립트는 샘플 카탈로그 → 전처리 → 임베딩 학습 → 스코어링 → 리포팅까지의
전체 추천 파이프라인을 한 번에 실행하는 진입점을 제공합니다.
"""

from __future__ import annotations

import argparse
import importlib
import random
import sys

import numpy as np

_pipeline = importlib.import_module("7_pipeline")
display_results = _pipeline.display_results
prepare_environment = _pipeline.prepare_environment
run_query = _pipeline.run_query
run_samples = _pipeline.run_samples


random.seed(42)
np.random.seed(42)


def parse_args():
    parser = argparse.ArgumentParser(description="선물 추천 알고리즘 샌드박스 CLI")
    parser.add_argument(
        "--query",
        type=str,
        default="여사친 생일 3만 이하, 향 강한 건 싫어요",
        help="추천을 받고 싶은 질의 문장 (기본값: 샘플 질의)",
    )
    parser.add_argument("--k", type=int, default=10, help="표시할 Top-K 개수 (기본=10)")
    parser.add_argument(
        "--hard_budget",
        action="store_true",
        help="True이면 예산 범위를 벗어난 상품을 완전히 제외",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    df, vectors = prepare_environment()
    print(f"질의: {args.query}")
    results, summary = run_query(
        query=args.query,
        df=df,
        vectors=vectors,
        hard_budget=args.hard_budget,
        k=args.k,
    )
    display_results(results, summary["slots"])
    run_samples(df, vectors, args.hard_budget, args.k)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
