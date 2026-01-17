"""MMR(Maximal Marginal Relevance) 기반 다양화 로직."""

from __future__ import annotations

import math
from typing import List

import numpy as np
import pandas as pd


def mmr(items_df: pd.DataFrame, doc_embeddings: np.ndarray, lam: float = 0.7, K: int = 12) -> pd.DataFrame:
    """관련성과 중복 패널티를 균형 있게 반영해 다양한 후보를 고른다."""
    if items_df.empty:
        return items_df
    # pandas 인덱싱 반복 대신 넘파이 배열로 변환해 루프 비용을 줄인다.
    scores = items_df["score"].to_numpy()
    doc_idx = items_df["doc_index"].to_numpy()
    emb = doc_embeddings[doc_idx]
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    norms[norms == 0] = 1e-8
    emb_norm = emb / norms

    candidates: List[int] = list(range(len(items_df)))
    selected: List[int] = []

    while candidates and len(selected) < min(K, len(items_df)):
        if not selected:
            # 첫 선택: relevance만으로 결정
            best_idx = max(candidates, key=lambda idx: scores[idx])
            selected.append(best_idx)
            candidates.remove(best_idx)
            continue

        # 선택된 임베딩과의 최대 유사도를 벡터화 계산
        selected_emb = emb_norm[selected]  # shape: (len(selected), dim)
        cand_array = np.array(candidates, dtype=int)
        cand_emb = emb_norm[cand_array]  # shape: (len(candidates), dim)
        sims = cand_emb @ selected_emb.T  # (cand, selected)
        penalty = sims.max(axis=1)
        relevance = scores[cand_array]
        mmr_scores = lam * relevance - (1 - lam) * penalty

        best_pos = int(np.argmax(mmr_scores))
        best_idx = int(cand_array[best_pos])
        selected.append(best_idx)
        candidates.remove(best_idx)

    return items_df.loc[selected].reset_index(drop=True)
