from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional, Tuple

from google.cloud import firestore

from model.service.common import FIRESTORE_DB

log = logging.getLogger(__name__)

_COLLECTION = "chatbot_sessions"


def _collection():
    return FIRESTORE_DB.collection(_COLLECTION)


def _default_state(user_email: Optional[str], session_id: str) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "user_email": user_email,
        "state": "START",
        "flow": None,
        "slots": {},
        "skipped_slots": [],
        "profile_inputs": {},
        "pending_slot": None,
        "pending_profile_field": None,
        "last_recommendations": None,
        "last_segment_key": None,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }


def _normalize_state(session: Dict[str, Any], session_id: str, user_email: Optional[str]) -> Dict[str, Any]:
    normalized = {
        "session_id": session.get("session_id") or session_id,
        "user_email": session.get("user_email") or user_email,
        "state": session.get("state") or "START",
        "flow": session.get("flow"),
        "slots": session.get("slots") or {},
        "skipped_slots": session.get("skipped_slots") or [],
        "profile_inputs": session.get("profile_inputs") or {},
        "pending_slot": session.get("pending_slot"),
        "pending_profile_field": session.get("pending_profile_field"),
        "last_recommendations": session.get("last_recommendations"),
        "last_segment_key": session.get("last_segment_key"),
    }
    return normalized


def create_session(user_email: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    session_id = uuid.uuid4().hex
    payload = _default_state(user_email, session_id)
    try:
        _collection().document(session_id).set(payload)
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to create chatbot session %s: %s", session_id, exc)
        payload["created_at"] = None
        payload["updated_at"] = None
    return session_id, _normalize_state(payload, session_id, user_email)


def get_session(session_id: str, user_email: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        snapshot = _collection().document(session_id).get()
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to fetch chatbot session %s: %s", session_id, exc)
        return None
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    return _normalize_state(data, session_id, user_email)


def get_or_create_session(session_id: Optional[str], user_email: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    if session_id:
        existing = get_session(session_id, user_email)
        if existing is not None:
            return session_id, existing
    return create_session(user_email)


def save_session(session_id: str, state: Dict[str, Any]) -> None:
    payload = {
        **state,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        _collection().document(session_id).set(payload, merge=True)
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to persist chatbot session %s: %s", session_id, exc)


def reset_session(session_id: str, user_email: Optional[str]) -> Dict[str, Any]:
    new_state = _default_state(user_email, session_id)
    try:
        _collection().document(session_id).set(new_state)
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to reset chatbot session %s: %s", session_id, exc)
        new_state["created_at"] = None
        new_state["updated_at"] = None
    return _normalize_state(new_state, session_id, user_email)
