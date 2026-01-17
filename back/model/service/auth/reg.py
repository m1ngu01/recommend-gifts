from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from model.service.common import FIRESTORE_DB
from model.service.auth.utils import hash_password


def _email_doc_id(email: str) -> str:
    return (email or "").strip().lower()


def add_user(name, email, password, gender, age, interest):
    normalized_email = (email or "").strip()
    email_doc_id = _email_doc_id(email)
    if not normalized_email or not email_doc_id:
        return False

    users_ref = FIRESTORE_DB.collection("users")

    # 기존 랜덤 document id 사용자 중복을 막기 위해 한 번 더 검사
    existing_user = users_ref.where(filter=FieldFilter("email", "==", normalized_email)).limit(1).stream()
    if any(existing_user):
        return False

    payload = {
        "name": name,
        "email": normalized_email,
        "password": hash_password(password),
        "gender": gender,
        "age": age,
        "interest": interest,
        "role": "user",
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    doc_ref = users_ref.document(email_doc_id)
    try:
        doc_ref.create(payload)
        return True
    except AlreadyExists:
        return False


def check_user_exists(email):
    normalized_email = (email or "").strip()
    email_doc_id = _email_doc_id(email)
    if not normalized_email or not email_doc_id:
        return False

    users_ref = FIRESTORE_DB.collection("users")
    doc_ref = users_ref.document(email_doc_id)
    if doc_ref.get().exists:
        return False

    existing_user = users_ref.where(filter=FieldFilter("email", "==", normalized_email)).limit(1).stream()
    if any(existing_user):
        return False
    return True
