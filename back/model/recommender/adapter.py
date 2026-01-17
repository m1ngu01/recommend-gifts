"""
``back/model/recommender`` 아래 추천 파이프라인을 감싸는 어댑터.

- 파이프라인 모듈(1_sample_data ~ 7_pipeline) 로드
- 환경(df, vectors) 준비 및 캐싱
- run_recommender와 비동기 워밍업 헬퍼 제공
"""

from __future__ import annotations

import importlib
import sys
from numbers import Number
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, Optional

RECOMMENDER_DIR = Path(__file__).resolve().parent
if str(RECOMMENDER_DIR) not in sys.path:
    sys.path.insert(0, str(RECOMMENDER_DIR))

_reco_pipeline = None
_reco_env_cache: Dict[str, Any] = {"df": None, "vectors": None}
_reco_env_lock = Lock()
_reco_warmup_started = False


def _get_recommender_pipeline():
    global _reco_pipeline
    if _reco_pipeline is not None:
        return _reco_pipeline
    _reco_pipeline = importlib.import_module("7_pipeline")
    return _reco_pipeline


def ensure_recommender_env(force_reload: bool = False, logger=None) -> Dict[str, Any]:
    """
    추천 파이프라인 실행에 필요한 df와 vectors를 준비하고 캐싱한다.
    """
    global _reco_env_cache
    if (
        not force_reload
        and _reco_env_cache.get("df") is not None
        and _reco_env_cache.get("vectors") is not None
    ):
        return _reco_env_cache

    with _reco_env_lock:
        if (
            not force_reload
            and _reco_env_cache.get("df") is not None
            and _reco_env_cache.get("vectors") is not None
        ):
            return _reco_env_cache

        pipeline = _get_recommender_pipeline()
        df, vectors = pipeline.prepare_environment()
        _reco_env_cache = {"df": df, "vectors": vectors}
        if logger:
            logger.info("[recommender] 환경 준비 완료: %s개 상품", len(df))
        return _reco_env_cache


def warm_recommender_env_async(logger=None) -> None:
    """
    서버 기동 시 별도 스레드에서 한 번 환경을 워밍업한다.
    """
    global _reco_warmup_started
    with _reco_env_lock:
        if _reco_warmup_started:
            return
        _reco_warmup_started = True

    def _target():
        try:
            ensure_recommender_env(logger=logger)
        except Exception as exc:  # pragma: no cover - 기동 로깅 용
            if logger:
                logger.error("[recommender] 환경 준비 실패: %s", exc, exc_info=True)

    Thread(target=_target, daemon=True).start()


def _serialize_recommender_payload(
    sentence: str,
    results,
    summary: Dict[str, Any],
    search_log_id: Optional[str],
) -> Dict[str, Any]:
    slots_raw = summary.get("slots", {}) if isinstance(summary, dict) else {}

    def _jsonable(val):
        if isinstance(val, set):
            return list(val)
        return val

    slots = {k: _jsonable(v) for k, v in (slots_raw or {}).items()}
    keywords = slots.get("core_keywords") or []
    budget = {
        "min": slots.get("budget_min") or 0,
        "max": slots.get("budget_max") or 0,
        "raw": "",
    }
    query_payload = {
        "sentence": sentence,
        "keywords": keywords,
        "intent_tags": [s for s in (slots.get("occasion"), slots.get("relation")) if s],
        "include_tags": [],
        "category_candidates": [],
        "budget": budget,
        "notes": "",
    }

    items = []
    for row in results.to_dict(orient="records") if hasattr(results, "to_dict") else []:
        price_val = row.get("price")
        cost_text = None
        if isinstance(price_val, Number) and not isinstance(price_val, bool):
            cost_text = f"{int(price_val):,}원"
        tags_val = row.get("tags")
        if isinstance(tags_val, (list, tuple)):
            tags_text = ", ".join(str(tag) for tag in tags_val if tag)
        else:
            tags_text = str(tags_val) if tags_val else ""
        items.append(
            {
                "id": row.get("product_id"),
                "name": row.get("title") or "",
                "image_url": row.get("image") or "",
                "cost": cost_text,
                "satisfaction": row.get("rating"),
                "review_count": row.get("popularity"),
                "tags": tags_text,
                "category_path": row.get("category_path"),
                "link": row.get("link") or "",
                "reason": row.get("reason"),
                "score": row.get("score"),
            }
        )

    payload = {
        "query": query_payload,
        "results": items,
        "slots": slots,
        "meta": {"engine": "recommender", "search_log_id": search_log_id},
        "path1": [],
        "path2": [],
    }
    return payload


def run_recommender(
    sentence: str,
    top_k: int,
    hard_budget: bool = False,
    search_log_id: Optional[str] = None,
    logger=None,
) -> Dict[str, Any]:
    """
    추천 파이프라인을 실행하고 직렬화된 결과를 반환한다.
    """
    pipeline = _get_recommender_pipeline()
    env = ensure_recommender_env(logger=logger)
    results, summary = pipeline.run_query(
        query=sentence,
        df=env["df"],
        vectors=env["vectors"],
        hard_budget=hard_budget,
        k=top_k,
    )
    return _serialize_recommender_payload(sentence, results, summary, search_log_id)
