"""
Seed Firestore user_logs with synthetic buy_click events for analytics/testing.
Usage:
    python back/tools/seed_buy_clicks.py
"""

from datetime import datetime
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from model.service.common import FIRESTORE_DB

SAMPLE_PRODUCTS = [
    {
        "gift_name": "프리미엄 휴대폰 케이스",
        "gift_category": "디지털 > 모바일액세서리",
        "price": "18,900원",
    },
    {
        "gift_name": "50W 고속 충전기 세트",
        "gift_category": "디지털 > 전원/케이블",
        "price": "24,900원",
    },
    {
        "gift_name": "스테인리스 텀블러 500ml",
        "gift_category": "리빙 > 주방/다이닝",
        "price": "15,000원",
    },
    {
        "gift_name": "마스크팩 10매 기획세트",
        "gift_category": "뷰티 > 스킨케어",
        "price": "22,000원",
    },
    {
        "gift_name": "프리미엄 드립백 커피",
        "gift_category": "식품 > 커피/음료",
        "price": "28,000원",
    },
    {
        "gift_name": "폼롤러 & 스트레칭 밴드",
        "gift_category": "스포츠 > 홈트레이닝",
        "price": "19,800원",
    },
    {
        "gift_name": "문구 세트(다이어리+펜)",
        "gift_category": "문구 > 노트/다이어리",
        "price": "13,500원",
    },
    {
        "gift_name": "반려견 영양간식 세트",
        "gift_category": "펫 > 간식",
        "price": "25,000원",
    },
]

USER_SAMPLES = [
    {"user_name": "홍길동", "email": "hong@example.com", "gender": "남성", "age": 29},
    {"user_name": "이영희", "email": "lee@example.com", "gender": "여성", "age": 32},
    {"user_name": "John", "email": "john@example.com", "gender": "남성", "age": 41},
    {"user_name": "Sara", "email": "sara@example.com", "gender": "여성", "age": 25},
]


def main(count: int = 50) -> None:
    collection = FIRESTORE_DB.collection("user_logs")
    created = 0
    for _ in range(count):
        product = random.choice(SAMPLE_PRODUCTS)
        user = random.choice(USER_SAMPLES)
        payload = {
            "event": "buy_click",
            "payload": {
                "gift_name": product["gift_name"],
                "gift_category": product["gift_category"],
                "price": product["price"],
                "user_name": user["user_name"],
                "gender": user["gender"],
                "age": user["age"],
                "timestamp": datetime.utcnow().isoformat(),
            },
            "created_at": datetime.utcnow(),
        }
        try:
            collection.add(payload)
            created += 1
        except Exception as exc:
            print(f"[⚠️] Failed to add buy_click log: {exc}")
    print(f"[✔] Inserted {created} synthetic buy_click events.")


if __name__ == "__main__":
    main()
