from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from google.cloud import firestore

from model.service.common import FIRESTORE_DB

log = logging.getLogger(__name__)

_COLLECTION = "chat_sessions"


def _collection():
    return FIRESTORE_DB.collection(_COLLECTION)


def generate_session_id() -> str:
    return uuid.uuid4().hex


def get_or_create_session(session_id: Optional[str], user_email: Optional[str]) -> tuple[str, Dict[str, Any]]:
    if session_id:
        snapshot = _fetch_session(session_id)
        if snapshot is not None:
            return session_id, snapshot

    new_session_id = generate_session_id()
    initial_state = {
        "session_id": new_session_id,
        "user_email": user_email,
        "state": {
            "slots": {},
            "awaiting_slot": None,
        },
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        _collection().document(new_session_id).set(initial_state)
    except Exception as exc:  # pragma: no cover - best-effort persistence
        log.warning("Failed to create chat session %s: %s", new_session_id, exc)
        # Ensure timestamps exist even if Firestore write fails
        initial_state["created_at"] = None
        initial_state["updated_at"] = None
    return new_session_id, initial_state


def _fetch_session(session_id: str) -> Optional[Dict[str, Any]]:
    try:
        snapshot = _collection().document(session_id).get()
    except Exception as exc:  # pragma: no cover - best-effort read
        log.warning("Failed to fetch chat session %s: %s", session_id, exc)
        return None
    if not snapshot.exists:
        return None
    return snapshot.to_dict() or {"state": {"slots": {}, "awaiting_slot": None}}


def update_session_state(session_id: str, partial_state: Dict[str, Any]) -> None:
    payload = {
        **partial_state,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        _collection().document(session_id).set(payload, merge=True)
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to update chat session %s: %s", session_id, exc)


def append_message(session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    try:
        _collection().document(session_id).collection("messages").add(
            {
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to persist chat message for %s: %s", session_id, exc)
