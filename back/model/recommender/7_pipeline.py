"""CLI에서 사용할 파이프라인 조립·실행 보조 함수."""

from __future__ import annotations

import importlib
from typing import Dict, Tuple

import pandas as pd

_sample_module = importlib.import_module("1_sample_data")
sample_data = _sample_module.sample_data

_text_utils = importlib.import_module("2_text_processing")
enrich_dataframe = _text_utils.enrich_dataframe
tokenize = _text_utils.tokenize

_modeling = importlib.import_module("3_modeling")
build_item_vectors = _modeling.build_item_vectors
build_tfidf = _modeling.build_tfidf
train_word2vec = _modeling.train_word2vec

_slot_helpers = importlib.import_module("4_slots_filters")
expand_keywords = _slot_helpers.expand_keywords
extract_slots = _slot_helpers.extract_slots

_scoring = importlib.import_module("5_scoring")
format_reason = _scoring.format_reason
render_table = _scoring.render_table
score_items = _scoring.score_items
summarize_guards = _scoring.summarize_guards
deduplicate_products = _scoring.deduplicate_products

_mmr_module = importlib.import_module("6_mmr")
mmr = _mmr_module.mmr


def _log(message: str):
    """간단한 진행 로그 출력 헬퍼."""
    print(f"[progress] {message}")


SAMPLE_QUERIES = [
    "여사친 생일 3만 이하, 향 강한 건 싫어",
    "집들이 선물 5만원대 무드등 무인양품 느낌",
    "직장 동료 감사 2~4만, 견과류 빼고 실용적으로",
]


def prepare_environment() -> Tuple[pd.DataFrame, Dict]:
    """샘플 데이터를 불러와 전처리·임베딩·TF-IDF 모델을 준비한다."""
    _log("샘플 데이터 로드 및 전처리 시작")
    # 상품 카탈로그는 규칙 기반 토큰화만 적용해 전처리 속도를 높인다.
    df = enrich_dataframe(sample_data(), use_nouns=False)
    _log(f"데이터 로드 완료: {len(df)}개 상품")

    # Word2Vec 추가 학습은 현재 건너뛴다.
    # w2v = train_word2vec(df["tokens"].tolist())
    w2v = None
    _log("Word2Vec 학습 건너뜀")

    _log("TF-IDF 벡터라이저 학습 중")
    vectorizer, tfidf_matrix = build_tfidf(df["text"].tolist())
    _log("TF-IDF 학습 완료")

    _log("상품 임베딩 캐시 구성 중")
    vectors = build_item_vectors(df, w2v, vectorizer, tfidf_matrix)
    _log("환경 준비 완료")
    return df, vectors


def run_query(
    query: str,
    df: pd.DataFrame,
    vectors: Dict,
    hard_budget: bool,
    k: int,
) -> Tuple[pd.DataFrame, Dict]:
    """단일 질의를 실행해 슬롯 추출→확장→스코어링→MMR→사유 생성을 수행한다."""
    _log(f"질의 처리 시작: {query}")
    slots = extract_slots(query)
    if not slots["core_keywords"]:
        slots["core_keywords"] = tokenize(query)[:4]
    _log(f"슬롯 추출 완료: core={slots['core_keywords']}, forbidden={slots['forbidden']}")
    expanded = expand_keywords(slots["core_keywords"], vectors["w2v"], slots["forbidden"])
    query_terms = list(dict.fromkeys(expanded))
    _log(f"키워드 확장 완료 ({len(query_terms)}개): {query_terms}")
    scored = score_items(query_terms, query, df, vectors, slots, hard_budget)
    _log(f"스코어링 완료: {len(scored)}개 후보")

    # product_id 기준 중복 제거 후 Top-K MMR
    deduped = deduplicate_products(scored)
    _log(f"중복 제거 완료: {len(deduped)}개 후보")
    selected = mmr(deduped, vectors["doc_embeddings"], K=k).copy()
    _log(f"MMR 선택 완료: {len(selected)}개 Top-K")
    if not selected.empty:
        selected["reason"] = selected.apply(lambda row: format_reason(row, slots), axis=1)
    summary = {"slots": slots, "results": selected}
    _log("질의 처리 종료")
    return selected, summary


def display_results(results: pd.DataFrame, slots: Dict):
    """추천 표와 품질 가드 요약을 함께 출력한다."""
    render_table(results)
    summarize_guards(results, slots)


def run_samples(df: pd.DataFrame, vectors: Dict, hard_budget: bool, k: int):
    """사전에 정의된 샘플 질의 3개를 자동으로 실행한다."""
    print("\n=== Auto Sample Queries ===")
    for idx, query in enumerate(SAMPLE_QUERIES, start=1):
        print(f"\n[SAMPLE {idx}] {query}")
        results, summary = run_query(
            query=query,
            df=df,
            vectors=vectors,
            hard_budget=hard_budget,
            k=min(k, 8),
        )
        display_results(results, summary["slots"])
