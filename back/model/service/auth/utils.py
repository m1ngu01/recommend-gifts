import hashlib
import bcrypt
from typing import Tuple


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def is_legacy_sha256(stored: str) -> bool:
    # 64-char hex
    return isinstance(stored, str) and len(stored) == 64 and all(c in "0123456789abcdef" for c in stored)


def bcrypt_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def bcrypt_check(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def verify_password_and_migrate(plain: str, stored_hash: str) -> Tuple[bool, str, bool]:
    """
    Returns (ok, new_hash, migrated)
    - If legacy sha256 and matches, return True and new bcrypt hash with migrated=True
    - If bcrypt and matches, return True and original hash, migrated=False
    - Else return False
    """
    if is_legacy_sha256(stored_hash):
        if sha256_hex(plain) == stored_hash:
            new_hash = bcrypt_hash(plain)
            return True, new_hash, True
        return False, stored_hash, False
    # bcrypt path
    if bcrypt_check(plain, stored_hash):
        return True, stored_hash, False
    return False, stored_hash, False


def hash_password(password: str) -> str:
    # keep name for compatibility; now bcrypt
    return bcrypt_hash(password)
