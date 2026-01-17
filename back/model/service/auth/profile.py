from typing import Optional, Dict, Any

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB


def _get_user_docs_by_email(email: str):
    users_ref = FIRESTORE_DB.collection("users")
    return list(users_ref.where(filter=FieldFilter("email", "==", email)).stream())


def _snapshot_to_profile(snapshot) -> Optional[Dict[str, Any]]:
    if snapshot is None or not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    data.pop("password", None)

    def _serialize_datetime(value):
        if value is None:
            return None
        try:
            return value.isoformat()
        except AttributeError:
            return str(value)

    created_at = data.get("created_at") or getattr(snapshot, "create_time", None)
    updated_at = data.get("updated_at") or getattr(snapshot, "update_time", None)

    data["created_at"] = _serialize_datetime(created_at)
    data["updated_at"] = _serialize_datetime(updated_at)
    data.setdefault("role", "user")
    return data


def fetch_user_profile(email: str) -> Optional[Dict[str, Any]]:
    docs = _get_user_docs_by_email(email)
    if not docs:
        return None
    return _snapshot_to_profile(docs[0])


def update_user_profile(email: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    docs = _get_user_docs_by_email(email)
    if not docs:
        return None
    doc = docs[0]
    payload = {k: v for k, v in updates.items() if v is not None}
    if not payload:
        return _snapshot_to_profile(doc)
    payload["updated_at"] = firestore.SERVER_TIMESTAMP
    doc.reference.update(payload)
    refreshed = doc.reference.get()
    return _snapshot_to_profile(refreshed)
