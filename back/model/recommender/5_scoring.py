"""유사도 계산, 스코어 집계, 결과 표 렌더링, 가드 요약 기능."""

from __future__ import annotations

import importlib
from typing import Dict, List

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

_text_utils = importlib.import_module("2_text_processing")
normalize_text = _text_utils.normalize_text
tokenize = _text_utils.tokenize

_modeling = importlib.import_module("3_modeling")
cosine_sim_dense = _modeling.cosine_sim_dense
tfidf_weighted_embedding = _modeling.tfidf_weighted_embedding

_slot_helpers = importlib.import_module("4_slots_filters")
compute_budget_fit = _slot_helpers.compute_budget_fit
compute_context_score = _slot_helpers.compute_context_score
describe_guard = _slot_helpers.describe_guard
violates_forbidden = _slot_helpers.violates_forbidden


def score_items(
    query_terms: List[str],
    query_text: str,
    df: pd.DataFrame,
    vectors: Dict,
    slots: Dict,
    hard_budget: bool = False,
) -> pd.DataFrame:
    """TF-IDF·W2V 유사도와 룰 기반 보정을 합산해 전 상품을 스코어링한다."""
    vectorizer = vectors["tfidf_vectorizer"]
    tfidf_matrix = vectors["tfidf_matrix"]
    doc_embeddings = vectors["doc_embeddings"]
    doc_token_sets = vectors["doc_token_sets"]
    w2v = vectors["w2v"]
    features = vectorizer.get_feature_names_out()

    if not query_terms:
        query_terms = tokenize(query_text)[:6]
    joined = " ".join(query_terms) if query_terms else normalize_text(query_text)

    query_tfidf = vectorizer.transform([joined])
    query_embedding = tfidf_weighted_embedding(query_tfidf, features, w2v)
    sim_tfidf = cosine_similarity(query_tfidf, tfidf_matrix).ravel()
    sim_w2v = cosine_sim_dense(query_embedding, doc_embeddings)

    records = []
    for idx, row in df.iterrows():
        doc_text = row["text"]
        if violates_forbidden(doc_text, slots["forbidden"]):
            continue
        budget_fit, outside = compute_budget_fit(row["price"], slots["budget_min"], slots["budget_max"])
        if hard_budget and outside:
            continue
        context_score = compute_context_score(doc_text, slots)
        matched_keywords = [term for term in query_terms if term in doc_token_sets[idx]]
        final_score = (
            0.35 * sim_w2v[idx]
            + 0.25 * sim_tfidf[idx]
            + 0.20 * budget_fit
            + 0.10 * context_score
            + 0.10 * row["popularity_norm"]
        )
        if outside and not hard_budget:
            final_score -= 0.03
        records.append(
            {
                **row.to_dict(),
                "doc_index": idx,
                "score": float(final_score),
                "sim_w2v": float(sim_w2v[idx]),
                "sim_tfidf": float(sim_tfidf[idx]),
                "budget_fit": float(budget_fit),
                "budget_outside": outside,
                "context_score": float(context_score),
                "matched_keywords": matched_keywords,
                "query_terms": query_terms,
            }
        )
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)


def deduplicate_products(items: pd.DataFrame) -> pd.DataFrame:
    """
    product_id 기준으로 중복을 제거한다.
    점수가 높은 순으로 정렬 후 첫 항목만 남긴다.
    """
    if items.empty or "product_id" not in items:
        return items
    return (
        items.sort_values("score", ascending=False)
        .drop_duplicates(subset=["product_id"], keep="first")
        .reset_index(drop=True)
    )


def format_reason(row: pd.Series, slots: Dict) -> str:
    """추천 사유(매칭 키워드, 예산 적합, 평점/인기, 금기 충족)를 문자열로 만든다."""
    matched = row.get("matched_keywords", [])
    keyword_text = "/".join(matched[:3]) if matched else "취향 탐색"
    budget_band = max(1, int(round(row["price"] / 10000)))
    budget_desc = f"{budget_band}만 원대 예산"
    if not row.get("budget_outside") and row.get("budget_fit", 0) >= 0.6:
        budget_desc += " 적합"
    else:
        budget_desc += " 보완"
    rating_text = f"평점 {row['rating']:.1f}"
    popularity = row.get("popularity", 0)
    pop_text = f"인기 {int(popularity/1000)}k" if popularity >= 1000 else f"인기 {popularity}"
    guard = describe_guard(row["text"], slots.get("forbidden", set()))
    pieces = [f"{keyword_text} 키워드 매칭", budget_desc, f"{rating_text}·{pop_text}"]
    if guard:
        pieces.append(guard)
    return ", ".join(pieces)


def render_table(results: pd.DataFrame):
    """Top-K 추천 결과를 표 형태로 출력한다."""
    if results.empty:
        print("추천 가능한 상품이 없습니다.")
        return
    header = f"{'rank':<4} {'product_id':<8} {'title':<30} {'price':>8} {'S':>6}  reason"
    print(header)
    print("-" * len(header))
    for idx, row in results.iterrows():
        title = (row["title"][:27] + "...") if len(row["title"]) > 30 else row["title"]
        print(
            f"{idx+1:<4} {row['product_id']:<8} {title:<30} {row['price']:>8,} {row['score']:>6.3f}  {row['reason']}"
        )


def summarize_guards(results: pd.DataFrame, slots: Dict):
    """금기 위반 건수와 예산 이탈률을 집계해 요약 문장을 출력한다."""
    forbidden_hits = 0
    for row in results.itertuples():
        if violates_forbidden(getattr(row, "text"), slots.get("forbidden", set())):
            forbidden_hits += 1
    budget_out = int(results["budget_outside"].sum()) if not results.empty else 0
    total = len(results) or 1
    ratio = budget_out / total
    print(f"금기 위반: {forbidden_hits}건, 예산 이탈률: {ratio*100:>5.1f}% ({budget_out}/{total})")
