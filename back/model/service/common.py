import os

import firebase_admin
from firebase_admin import credentials, firestore, db

# [1] Firebase 초기화
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.getenv("FIREBASE_CREDENTIALS", os.path.join(BASE_DIR, "api_key.json"))
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "recommendgift-67d70")
DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL",
    "https://recommendgift-67d70-default-rtdb.firebaseio.com/",
)

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(
        cred,
        {
            "projectId": PROJECT_ID,
            "databaseURL": DATABASE_URL,
        },
    )

# [2] 클라이언트 참조
FIRESTORE_DB = firestore.client()
REALTIME_ROOT = db.reference("/")

if __name__ == "__main__":
    print("Firebase initialized successfully.")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Firestore client: {FIRESTORE_DB}")
    print(f"Realtime DB root reference: {REALTIME_ROOT}")
    print(f"Realtime DB URL: {DATABASE_URL}")
