import os

from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB
from model.service.auth.utils import verify_password_and_migrate

_ADMIN_IDS = {"admin", "admin@giftstandard.local"}


def _try_admin_login(email: str, password: str):
    normalized = (email or "").strip().lower()
    if normalized not in _ADMIN_IDS:
        return None
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    if password != admin_password:
        return None
    return {
        "name": "Administrator",
        "email": "admin",
        "age": None,
        "gender": None,
        "interest": "operations",
        "role": "admin",
    }


def login_user(email, password):
    admin_profile = _try_admin_login(email, password)
    if admin_profile:
        return admin_profile

    users_ref = FIRESTORE_DB.collection("users")
    users = list(users_ref.where(filter=FieldFilter("email", "==", email)).stream())
    for user in users:
        data = user.to_dict()
        stored = data.get("password", "")
        ok, new_hash, migrated = verify_password_and_migrate(password, stored)
        if ok:
            if migrated:
                try:
                    user.reference.update({"password": new_hash})
                except Exception:
                    pass
            return {
                "name": data.get("name"),
                "email": data.get("email"),
                "age": data.get("age"),
                "gender": data.get("gender"),
                "interest": data.get("interest"),
                "role": data.get("role", "user"),
            }
    return None  # 로그인 실패 시 None 반환
