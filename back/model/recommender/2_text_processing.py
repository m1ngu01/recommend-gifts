"""텍스트 정규화·토크나이즈 및 데이터프레임 보조 전처리 함수."""

from __future__ import annotations

import re
import unicodedata
from typing import List, Sequence

import pandas as pd
import importlib

stopwords_module = importlib.import_module("define_stopwords")
STOPWORDS = set(stopwords_module.STOPWORDS)
nfkc_lower = stopwords_module.nfkc_lower

try:
    from konlpy.tag import Okt
except Exception:  # pragma: no cover - optional dependency guard
    Okt = None

_OKT = Okt() if Okt is not None else None

_KOREAN_ONLY = re.compile(r"^[가-힣]+$")
_KOREAN_PARTICLE_SUFFIXES = [
    # 긴 것부터 매칭
    "에게서", "에게만", "에게로", "에서만", "으로부터", "으로서", "으로써",
    "에게도", "에서도", "에게", "에서", "으로", "로부터", "까지",
    "부터", "부터도", "부터는", "부터의",
    "으로는", "으로도", "로는", "로도",
    "라도", "마저", "조차", "만큼", "보다", "처럼",
    "에게도", "한테서", "한테도", "한테", "께서",
    "들은", "들은지", "들은가", "들은걸",
    "들은가요", "들은거", "들은건",
    "들", "는", "은", "이", "가", "을", "를", "와", "과",
    "도", "만", "랑", "하고",
]
_KOREAN_VERB_SUFFIXES = [
    "하는", "하는지", "하면서", "하지만", "하려고", "하려는", "하려니", "하려면",
    "해줘", "해줘요", "해서", "해서요", "해서는", "해서라도",
    "했어요", "했구요", "했는데", "했더니", "했더라", "했다",
    "되나요", "되었어요", "되는데", "되는지", "되는", "되게",
    "해요", "해라", "하라", "해라니", "하라니",
    "되니", "되냐", "되나", "되면", "되네", "된다", "되는거", "되는건",
]


def _strip_korean_suffix(token: str) -> str:
    """조사/어미를 단순 제거해 어간만 남긴다."""
    if not _KOREAN_ONLY.match(token):
        return token
    base = token
    for suffix in _KOREAN_PARTICLE_SUFFIXES:
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[: -len(suffix)]
            break
    for suffix in _KOREAN_VERB_SUFFIXES:
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[: -len(suffix)]
            break
    return base


def _extract_nouns_ko(text: str) -> List[str]:
    """Okt 명사 추출 기반 한국어 형태소 분리(실패 시 빈 리스트)."""
    if _OKT is None:
        return []
    try:
        nouns = _OKT.nouns(text)
    except Exception:
        return []
    cleaned = []
    for noun in nouns:
        n = nfkc_lower(noun)
        if not n or n in STOPWORDS:
            continue
        if re.search(r"\d", n):
            continue
        cleaned.append(n)
    return cleaned


def normalize_text(text: str) -> str:
    """NFKC 정규화와 소문자화, 간단한 공백/기호 정리를 수행한다."""
    if text is None:
        return ""
    norm = unicodedata.normalize("NFKC", str(text))
    norm = norm.lower()
    norm = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def tokenize(text: str, *, use_nouns: bool = True) -> List[str]:
    """
    공백 단위 토큰화 후 불용어·숫자 토큰을 제거한다.

    use_nouns=True이면 한국어 명사 추출(Okt)로 우선 필터링하고,
    False이면 규칙 기반 토큰화만 수행한다.
    """
    norm = normalize_text(text)
    tokens: List[str] = []

    # 1) 한국어 명사 우선 추출 (옵션)
    if use_nouns:
        nouns = _extract_nouns_ko(norm)
        if nouns:
            tokens.extend(nouns)

    # 2) fallback/보완: 공백 기반 토큰 + 조사/어미 제거
    for token in norm.split():
        if token in STOPWORDS:
            continue
        if token.isdigit():
            continue
        if re.search(r"\d", token):
            continue
        core = _strip_korean_suffix(token)
        if core and core not in STOPWORDS:
            tokens.append(core)
    # 순서 보존 중복 제거
    return list(dict.fromkeys(tokens))


def flatten_text(values: Sequence) -> str:
    """리스트/튜플 등을 펼쳐 하나의 문자열로 이어 붙인다."""
    parts = []
    for value in values:
        if isinstance(value, (list, tuple)):
            parts.extend(value)
        elif pd.notna(value):
            parts.append(str(value))
    return " ".join(parts)


def enrich_dataframe(df: pd.DataFrame, *, use_nouns: bool = True) -> pd.DataFrame:
    """정규화된 텍스트/토큰/인기도 컬럼을 추가한 데이터프레임을 만든다."""
    df = df.copy().reset_index(drop=True)
    df["text"] = df.apply(
        lambda row: normalize_text(
            flatten_text([row["title"], row.get("tags", []), row.get("category_path", [])])
        ),
        axis=1,
    )
    df["tokens"] = df["text"].apply(lambda s: tokenize(s, use_nouns=use_nouns))
    pops = df["popularity"].astype(float)
    pop_min, pop_max = pops.min(), pops.max()
    if pop_max == pop_min:
        df["popularity_norm"] = 0.5
    else:
        df["popularity_norm"] = (pops - pop_min) / (pop_max - pop_min)
    return df
