# log.py
from model.service.common import FIRESTORE_DB 

def insert_log(data):
    FIRESTORE_DB.collection("user_logs").add(data)
    return None  # 로그인 실패 시 None 반환
