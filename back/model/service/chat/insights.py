from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB
from model.recommender.define_stopwords import STOPWORDS as RECO_STOPWORDS
from model.recommender.define_stopwords import nfkc_lower

log = logging.getLogger(__name__)

_COLLECTION = "search_logs"
_TOKEN_PATTERN = re.compile(r"[0-9]+만원|[가-힣A-Za-z0-9]+")
_STOPWORDS_CACHE: Optional[Set[str]] = None


def _get_stopwords() -> Set[str]:
    global _STOPWORDS_CACHE
    if _STOPWORDS_CACHE is None:
        _STOPWORDS_CACHE = set(RECO_STOPWORDS)
    return _STOPWORDS_CACHE


def bucket_age(age: Optional[Any]) -> str:
    if age is None:
        return "unknown-age"
    try:
        age_value = int(age)
    except (TypeError, ValueError):
        return "unknown-age"
    if age_value < 20:
        return "teen"
    if age_value < 30:
        return "twenties"
    if age_value < 40:
        return "thirties"
    if age_value < 50:
        return "forties"
    return "fifty-plus"


def build_segment_key(profile: Optional[Dict[str, Any]], slots: Dict[str, Any]) -> str:
    relationship = (slots.get("relationship") or "unknown-rel").lower()
    gender = (profile or {}).get("gender") or "unknown-gender"
    age_bucket = bucket_age((profile or {}).get("age"))
    interest = (profile or {}).get("interest") or "any-interest"
    return f"{gender}:{age_bucket}:{relationship}:{interest}"


def get_top_keywords_for_segment(segment_key: Optional[str], limit: int = 5) -> List[Dict[str, Any]]:
    if not segment_key:
        return get_global_keyword_trends(limit=limit)

    try:
        query = (
            FIRESTORE_DB.collection(_COLLECTION)
            .where(filter=FieldFilter("segment_key", "==", segment_key))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(200)
        )
        docs = list(query.stream())
    except Exception as exc:  # pragma: no cover - best effort
        log.debug("Failed to read keywords for %s: %s", segment_key, exc)
        return get_global_keyword_trends(limit=limit)

    if not docs:
        return get_global_keyword_trends(limit=limit)

    counter = Counter()
    for doc in docs:
        data = doc.to_dict() or {}
        sentence = data.get("sentence") or ""
        counter.update(_tokenize(sentence))
        slots = (data.get("metadata") or {}).get("slots") or {}
        counter.update(_tokenize(" ".join(str(v) for v in slots.values() if v)))

    return _counter_to_list(counter, limit)


def get_global_keyword_trends(limit: int = 5) -> List[Dict[str, Any]]:
    try:
        docs = (
            FIRESTORE_DB.collection(_COLLECTION)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(200)
            .stream()
        )
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to read global keyword trends: %s", exc)
        return []

    counter = Counter()
    for doc in docs:
        data = doc.to_dict() or {}
        counter.update(_tokenize(data.get("sentence") or ""))
    return _counter_to_list(counter, limit)


def _tokenize(text: str) -> List[str]:
    stopwords = _get_stopwords()
    tokens = []
    for match in _TOKEN_PATTERN.findall(text.lower()):
        token = nfkc_lower(match)
        if token in stopwords:
            continue
        tokens.append(token)
    return tokens


def _counter_to_list(counter: Counter, limit: int) -> List[Dict[str, Any]]:
    most = counter.most_common(limit)
    return [{"keyword": keyword, "count": count} for keyword, count in most if keyword]
