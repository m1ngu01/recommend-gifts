"""
Seed script to populate Firestore 'users' collection with dummy accounts.

Usage:
    python back/tools/seed_users.py
"""

import random
import string
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from model.service.common import FIRESTORE_DB
from model.service.auth.utils import hash_password

N_USERS = 50


def random_name():
    first = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
    last = ["민수", "서연", "지후", "서준", "하린", "지민", "가은", "시우", "예은", "도윤"]
    return random.choice(first) + random.choice(last)


def random_interest():
    topics = ["여행", "게임", "카메라", "헬스", "요리", "음악", "패션", "코딩", "영화", "독서"]
    return random.choice(topics)


def random_email(idx):
    domain = random.choice(["giftstandard.com", "example.com", "mail.com"])
    return f"user{idx}@{domain}"


def main():
    users_ref = FIRESTORE_DB.collection("users")
    for i in range(N_USERS):
        email = random_email(i)
        payload = {
            "name": random_name(),
            "email": email,
            "password": hash_password("Passw0rd!"),
            "gender": random.choice(["남성", "여성"]),
            "age": random.randint(18, 35),
            "interest": random_interest(),
            "role": "user",
        }
        users_ref.add(payload)
    print(f"Inserted {N_USERS} dummy users.")


if __name__ == "__main__":
    main()
