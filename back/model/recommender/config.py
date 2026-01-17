"""
Reusable vocab/config for the recommender pipeline.

- STOPWORDS: 공통 불용어 집합(define_stopwords.py)
- OCCASION/RELATION: 상황/관계 슬롯 매핑(define_slots.py, 역매핑 포함)
- FORBIDDEN_SYNONYMS: 금기 키워드 패턴(define_slots.py)
- HINTS: 슬롯/스타일/카테고리 보조 힌트
- BRAND_ALIASES: 브랜드/별칭 매핑(의미 통합)
- NORMALIZATION: 단위/숫자 표기 정규화 힌트
- BUDGET_PATTERNS: 예산 표현 인식용 정규식(만원대/이하/이내 등)

유틸 함수:
- extract_budget_kr, normalize_units_kr, brand_canonical
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Pattern, Optional
import os
import re

from define_slots import (
    FORBIDDEN_SYNONYMS,
    OCCASION_HINTS,
    OCCASION_MAP,
    RELATION_HINTS,
    RELATION_MAP,
    compile_forbidden_regex,
    make_reverse_map,
)
from define_stopwords import STOPWORDS, nfkc_lower, simple_tokenize_ko

# ---------------------------------------------------------------------
# 카테고리/스타일 힌트 (랭킹/설명/탐색 다양화에 가중치로 사용)
# ---------------------------------------------------------------------
CATEGORY_HINTS: Dict[str, List[str]] = {
    "전자/웨어러블": ["워치", "스마트워치", "밴드", "이어폰", "무선이어폰", "버즈", "가습기", "무드등"],
    "문구/데스크": ["문구", "노트", "다이어리", "펜", "책상정리", "데스크", "타이머"],
    "주방/리빙": ["텀블러", "머그", "밀폐용기", "프라이팬", "주방", "수납", "정리함"],
    "뷰티/바디": ["핸드크림", "스킨", "로션", "선크림", "클렌저", "무향", "저자극"],
    "간식/식품": ["초콜릿", "쿠키", "캔디", "라면", "간식", "커피", "티"],
}

STYLE_HINTS: Dict[str, List[str]] = {
    "미니멀": ["미니멀", "심플", "뉴트럴", "무지", "무인양품", "우드톤", "베이지"],
    "레트로": ["레트로", "빈티지", "아날로그"],
    "게이밍": ["게이밍", "rgb", "저지연", "로우레이트", "게임"],
    "힐링": ["힐링", "무드", "아로마", "캔들워머", "코지"],
    "러블리": ["러블리", "핑크", "하트", "플라워"],
}

AGE_HINTS: Dict[str, List[str]] = {
    "10대": ["중학생", "고1", "고2", "고3", "고등학생", "학생"],
    "20대": ["대학생", "캠퍼스", "자취"],
    "30대": ["직장인", "신혼"],
    "40대+": ["엄마", "아빠", "부모님", "건강"],
}

# ---------------------------------------------------------------------
# 브랜드 별칭(동일 개념 통합)
# ---------------------------------------------------------------------
BRAND_ALIASES: Dict[str, List[str]] = {
    "무인양품": ["무인양품", "muji", "무지"],
    "삼성": ["삼성", "samsung", "갤럭시"],
    "애플": ["애플", "apple"],
    "샤오미": ["샤오미", "xiaomi", "mi"],
    "핏빗": ["핏빗", "fitbit"],
}

# ---------------------------------------------------------------------
# 숫자/단위 표기 정규화 (임베딩/매칭 일관성)
# ---------------------------------------------------------------------
UNIT_NORMALIZATION: List[Tuple[Pattern, str]] = [
    # BT version → bt5_4
    (re.compile(r"\b(?:bt|bluetooth)\s*5[.\s]?4\b", re.I), "bt5_4"),
    (re.compile(r"\b(?:bt|bluetooth)\s*5[.\s]?3\b", re.I), "bt5_3"),
    # 인치/센치
    (re.compile(r"(\d+(?:\.\d+)?)\s*인치"), r"\1인치"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*inch", re.I), r"\1인치"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*mm"), r"\1mm"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*cm"), r"\1cm"),
    # 배터리/용량
    (re.compile(r"(\d+)\s*mah", re.I), r"\1mAh"),
    # ip등급
    (re.compile(r"\bip\s*([0-9]{2})\b", re.I), r"ip\1"),
    # 시간/거리
    (re.compile(r"(\d+)\s*시간"), r"\1시간"),
    (re.compile(r"(\d+)\s*일"), r"\1일"),
]

# ---------------------------------------------------------------------
# 예산 인식 (만원/천원/원, 이하/이내/대/~선/언더)
# ---------------------------------------------------------------------
BUDGET_PATTERNS = {
    "RANGE_~만원대": re.compile(r"(\d+)\s*만\s*원?\s*대"),
    "LTE_만원": re.compile(r"(\d+)\s*만\s*원?\s*(?:이하|이내|언더|밑)"),
    "GTE_만원": re.compile(r"(\d+)\s*만\s*원?\s*(?:이상|부터)"),
    "EXACT_만원": re.compile(r"(\d+)\s*만\s*원?$"),
    "RAW_원": re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\s*원"),
}

# ---------------------------------------------------------------------
# 유틸 함수
# ---------------------------------------------------------------------
def normalize_units_kr(text: str) -> str:
    s = nfkc_lower(text)
    for pat, rep in UNIT_NORMALIZATION:
        s = pat.sub(rep, s)
    return s

def extract_budget_kr(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    한국어 예산 표현을 정수 KRW 하한/상한으로 변환.
    우선순위: RANGE → LTE/GTE → EXACT → RAW
    반환: (min_krw, max_krw)
    """
    s = nfkc_lower(text)
    # ① "~만원대"
    m = BUDGET_PATTERNS["RANGE_~만원대"].search(s)
    if m:
        base = int(m.group(1)) * 10_000
        return (int(base * 0.9), int(base * 1.1))
    # ② "N만원 이하/이내/언더"
    m = BUDGET_PATTERNS["LTE_만원"].search(s)
    if m:
        mx = int(m.group(1)) * 10_000
        return (0, mx)
    # ③ "N만원 이상/부터"
    m = BUDGET_PATTERNS["GTE_만원"].search(s)
    if m:
        mn = int(m.group(1)) * 10_000
        return (mn, None)
    # ④ "정확 N만원"
    m = BUDGET_PATTERNS["EXACT_만원"].search(s)
    if m:
        val = int(m.group(1)) * 10_000
        return (int(val * 0.9), int(val * 1.1))
    # ⑤ "숫자원"
    m = BUDGET_PATTERNS["RAW_원"].search(s)
    if m:
        raw = int(m.group(1).replace(",", ""))
        # 10% 폭
        return (int(raw * 0.9), int(raw * 1.1))
    return (None, None)

def brand_canonical(token: str) -> str:
    """브랜드 별칭을 표준명으로 정규화."""
    t = nfkc_lower(token)
    for canon, aliases in BRAND_ALIASES.items():
        if t == nfkc_lower(canon) or t in {nfkc_lower(a) for a in aliases}:
            return canon
    return token

# ---------------------------------------------------------------------
# 역매핑/정규식 컴파일 (초기화 편의)
# ---------------------------------------------------------------------
OCCASION_REVERSE = make_reverse_map(OCCASION_MAP)
RELATION_REVERSE = make_reverse_map(RELATION_MAP)
FORBIDDEN_REGEX = compile_forbidden_regex(FORBIDDEN_SYNONYMS)

# ---------------------------------------------------------------------
# 플래그/버전 (운영에 노출하면 유용)
# ---------------------------------------------------------------------
CONFIG_VERSION = "v2025-11-26"
USE_QTPP = bool(int(os.getenv("RECO_USE_QTPP", "1")))
USE_W2V  = bool(int(os.getenv("RECO_USE_W2V",  "1")))
SOFT_BUDGET = bool(int(os.getenv("RECO_SOFT_BUDGET", "0")))
