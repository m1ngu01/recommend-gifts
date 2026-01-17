"""카탈로그 임베딩 생성을 위한 TF-IDF·Word2Vec 보조 함수."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


class _EpochLogger(CallbackAny2Vec):
    """에폭 종료 시 진행률을 퍼센트로 로그 출력하는 콜백."""

    def __init__(self, total_epochs: int, enabled: bool = True):
        self.total_epochs = total_epochs
        self.enabled = enabled
        self._current = 0

    def on_epoch_end(self, model):
        if not self.enabled:
            return
        self._current += 1
        percent = (self._current / self.total_epochs) * 100
        print(f"[progress] Word2Vec 학습 {percent:5.1f}% ({self._current}/{self.total_epochs})")


def train_word2vec(corpus_tokens: List[List[str]], show_progress: bool = True) -> Word2Vec:
    """카탈로그 코퍼스 토큰으로 소규모 skip-gram Word2Vec을 학습한다."""
    epochs = 50
    model = Word2Vec(
        vector_size=100,
        window=5,
        min_count=1,
        sg=1,
        workers=1,
        seed=42,
    )
    model.build_vocab(corpus_tokens)
    model.train(
        corpus_tokens,
        total_examples=model.corpus_count,
        epochs=epochs,
        callbacks=[_EpochLogger(epochs, enabled=show_progress)],
    )
    return model


def build_tfidf(texts: Sequence[str]) -> Tuple[TfidfVectorizer, sparse.spmatrix]:
    """제목+태그를 묶은 문서들에 TF-IDF 벡터라이저를 학습한다."""
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def tfidf_weighted_embedding(
    row_vec: sparse.spmatrix, features: np.ndarray, model: Optional[Word2Vec]
) -> np.ndarray:
    """TF-IDF 가중치를 활용해 토큰 임베딩 평균을 구한다."""
    if model is None:  # Word2Vec 학습을 건너뛴 경우
        return np.zeros(1, dtype=np.float32)
    vec = np.zeros(model.vector_size, dtype=np.float32)
    if row_vec.nnz == 0:
        return vec
    coo = row_vec.tocoo()
    weight_sum = 0.0
    for idx, value in zip(coo.col, coo.data):
        token = features[idx]
        if token in model.wv:
            vec += model.wv[token] * float(value)
            weight_sum += float(value)
    if weight_sum > 0:
        vec /= weight_sum
    return vec


def cosine_sim_dense(query_vec: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    """밀집 쿼리 벡터와 모든 문서 임베딩의 코사인 유사도를 계산한다."""
    if not doc_embeddings.size:
        return np.zeros(0, dtype=np.float32)
    q_norm = np.linalg.norm(query_vec)
    if q_norm == 0:
        return np.zeros(doc_embeddings.shape[0], dtype=np.float32)
    doc_norms = np.linalg.norm(doc_embeddings, axis=1)
    denom = doc_norms * q_norm
    denom[denom == 0] = 1e-8
    sims = doc_embeddings.dot(query_vec) / denom
    sims[doc_norms == 0] = 0.0
    return sims.astype(np.float32)


def build_item_vectors(
    df: pd.DataFrame,
    w2v: Optional[Word2Vec],
    vectorizer: TfidfVectorizer,
    tfidf_matrix: sparse.spmatrix,
) -> Dict:
    """카탈로그 아이템마다 TF-IDF·W2V 기반 임베딩/토큰 집합을 캐시한다."""
    features = vectorizer.get_feature_names_out()
    embeddings = []
    token_sets = []
    for idx in range(len(df)):
        tokens = set(df.iloc[idx]["tokens"])
        token_sets.append(tokens)
        row_vec = tfidf_matrix[idx]
        embedding = tfidf_weighted_embedding(row_vec, features, w2v)
        embeddings.append(embedding)
    if not embeddings:
        doc_embeddings = np.zeros((0, 1), dtype=np.float32)
    else:
        doc_embeddings = np.vstack(embeddings)
    return {
        "tfidf_vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "doc_embeddings": doc_embeddings,
        "doc_token_sets": token_sets,
        "w2v": w2v,
    }
