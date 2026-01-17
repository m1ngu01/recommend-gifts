from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Optional

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB

_COLLECTION_SEARCH_LOGS = "search_logs"
_COLLECTION_SURVEY_FEEDBACK = "search_feedback"

_TRAINING_DIR = Path("back") / "data" / "training"
_TRAINING_FILE = _TRAINING_DIR / "search_feedback.jsonl"


def _normalize_sentence(text: str) -> str:
    return " ".join(text.split())


def record_search_log(
    sentence: str,
    user_email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> str:
    clean_sentence = _normalize_sentence(sentence)
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SEARCH_LOGS).document()
    payload: Dict[str, Any] = {
        "sentence": clean_sentence,
        "user_email": user_email,
        "metadata": metadata or {},
        "created_at": firestore.SERVER_TIMESTAMP,
        "annotated": False,
    }
    if extra_fields:
        payload.update(extra_fields)
    doc_ref.set(payload)
    return doc_ref.id


def update_search_log(log_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, extra_fields: Optional[Dict[str, Any]] = None) -> None:
    """
    Append/merge metadata or extra fields into an existing search_log.
    Gracefully no-op if log_id is falsy.
    """
    if not log_id:
        return
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SEARCH_LOGS).document(log_id)
    payload: Dict[str, Any] = {}
    if metadata is not None:
        payload["metadata"] = metadata
    if extra_fields:
        payload.update(extra_fields)
    if payload:
        doc_ref.set(payload, merge=True)


def fetch_random_search_prompt() -> Optional[Dict[str, Any]]:
    collection = FIRESTORE_DB.collection(_COLLECTION_SEARCH_LOGS)
    try:
        query = (
            collection.where(filter=FieldFilter("annotated", "==", False))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(50)
        )
        candidates = list(query.stream())
    except Exception:
        candidates = list(
            collection.where(filter=FieldFilter("annotated", "==", False)).limit(50).stream()
        )
    if not candidates:
        return None
    chosen = random.choice(candidates)
    data = chosen.to_dict() or {}
    sentence = data.get("sentence", "")
    if not sentence:
        return None
    return {
        "id": chosen.id,
        "sentence": sentence,
        "metadata": data.get("metadata") or {},
    }


def mark_search_log_annotated(log_id: str) -> None:
    if not log_id:
        return
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SEARCH_LOGS).document(log_id)
    doc_ref.set(
        {
            "annotated": True,
            "annotated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def store_survey_feedback(
    search_log_id: Optional[str],
    search_sentence: str,
    answer: str,
    user_email: Optional[str] = None,
    reason: Optional[str] = None,
) -> str:
    clean_sentence = _normalize_sentence(search_sentence)
    clean_answer = answer.strip()
    clean_reason = reason.strip() if reason else None
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SURVEY_FEEDBACK).document()
    doc_ref.set(
        {
            "search_log_id": search_log_id,
            "search_sentence": clean_sentence,
            "answer": clean_answer,
            "reason": clean_reason,
            "user_email": user_email,
            "status": "pending",
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
    if search_log_id:
        mark_search_log_annotated(search_log_id)
    return doc_ref.id


def list_survey_feedback(status: Optional[str] = None, limit: int = 50):
    col = FIRESTORE_DB.collection(_COLLECTION_SURVEY_FEEDBACK)
    query = col
    if status:
        query = query.where(filter=FieldFilter("status", "==", status))
    docs = list(query.stream())
    enriched = []
    for doc in docs:
        data = doc.to_dict() or {}
        enriched.append({"id": doc.id, **data})
    enriched.sort(key=lambda d: d.get("created_at"), reverse=True)
    return enriched[:limit]


def approve_survey_feedback(feedback_id: str) -> Dict[str, Any]:
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SURVEY_FEEDBACK).document(feedback_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ValueError("feedback not found")
    data = snapshot.to_dict() or {}
    if data.get("status") == "approved":
        return data
    payload = {
        "search_log_id": data.get("search_log_id"),
        "search_sentence": data.get("search_sentence"),
        "answer": data.get("answer"),
        "user_email": data.get("user_email"),
        "reason": data.get("reason"),
    }
    _append_training_example(payload)
    doc_ref.set(
        {
            "status": "approved",
            "approved_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )
    return payload


def reject_survey_feedback(feedback_id: str, reason: Optional[str] = None):
    doc_ref = FIRESTORE_DB.collection(_COLLECTION_SURVEY_FEEDBACK).document(feedback_id)
    snapshot = doc_ref.get()
    if not snapshot.exists:
        raise ValueError("feedback not found")
    doc_ref.set(
        {
            "status": "rejected",
            "rejected_at": firestore.SERVER_TIMESTAMP,
            "rejection_reason": reason,
        },
        merge=True,
    )


def _append_training_example(example: Dict[str, Any]) -> None:
    _TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(example, ensure_ascii=False)
    with _TRAINING_FILE.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")
