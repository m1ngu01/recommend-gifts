from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from google.cloud import firestore

from model.service.chat.insights import get_global_keyword_trends
from model.service.common import FIRESTORE_DB

UserBucket = Dict[str, Any]


def _fetch_recent_docs(collection: str, limit: int = 500):
    try:
        return (
            FIRESTORE_DB.collection(collection)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
    except Exception:
        return []


def get_popular_products(limit: int = 5) -> List[Dict[str, Any]]:
    docs = _fetch_recent_docs("user_logs", limit=1000)
    counter: Counter[Tuple[str, str]] = Counter()
    for doc in docs:
        data = doc.to_dict() or {}
        if data.get("event") != "buy_click":
            continue
        payload = data.get("payload") or {}
        name = payload.get("gift_name") or payload.get("product_name")
        if not name:
            continue
        category = payload.get("gift_category") or payload.get("category") or ""
        counter[(name, category)] += 1
    popular = []
    for (name, category), count in counter.most_common(limit):
        popular.append({"name": name, "category": category, "count": count})
    return popular


def get_gender_breakdown() -> List[UserBucket]:
    try:
        docs = FIRESTORE_DB.collection("users").limit(1000).stream()
    except Exception:
        return []
    counter: Counter[str] = Counter()
    for doc in docs:
        data = doc.to_dict() or {}
        gender = (data.get("gender") or "기타").strip()
        counter[gender or "기타"] += 1
    total = sum(counter.values()) or 1
    return [
        {"label": gender, "count": count, "ratio": count / total}
        for gender, count in counter.most_common()
    ]


def _bucket_age(age_value: Any) -> str:
    try:
        age = int(age_value)
    except (TypeError, ValueError):
        return "미기재"
    if age < 20:
        return "10대 이하"
    if age < 30:
        return "20대"
    if age < 40:
        return "30대"
    if age < 50:
        return "40대"
    return "50대 이상"


def get_age_distribution() -> List[UserBucket]:
    try:
        docs = FIRESTORE_DB.collection("users").limit(1000).stream()
    except Exception:
        return []
    counter: Counter[str] = Counter()
    for doc in docs:
        data = doc.to_dict() or {}
        bucket = _bucket_age(data.get("age"))
        counter[bucket] += 1
    total = sum(counter.values()) or 1
    return [
        {"label": bucket, "count": count, "ratio": count / total}
        for bucket, count in counter.most_common()
    ]


def build_admin_insights() -> Dict[str, Any]:
    return {
        "popular_products": get_popular_products(),
        "popular_keywords": get_global_keyword_trends(limit=10),
        "gender_breakdown": get_gender_breakdown(),
        "age_distribution": get_age_distribution(),
    }
