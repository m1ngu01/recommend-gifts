"""질의 슬롯 추출, 금기 처리, 룰 기반 점수 보조 함수."""

from __future__ import annotations

import importlib
import re
from typing import Dict, List, Optional, Set, Tuple

from gensim.models import Word2Vec

_text_utils = importlib.import_module("2_text_processing")
normalize_text = _text_utils.normalize_text
tokenize = _text_utils.tokenize

_slots = importlib.import_module("define_slots")
OCCASION_MAP = _slots.OCCASION_MAP
RELATION_MAP = _slots.RELATION_MAP
FORBIDDEN_SYNONYMS = _slots.FORBIDDEN_SYNONYMS
OCCASION_HINTS = _slots.OCCASION_HINTS
RELATION_HINTS = _slots.RELATION_HINTS


def _find_slot_by_map(text: str, mapping: Dict[str, List[str]]) -> str:
    """미리 정의한 키워드 맵에서 일치하는 슬롯 값을 찾는다."""
    for slot, candidates in mapping.items():
        for candidate in candidates:
            if candidate in text:
                return slot
    return ""


def _parse_budget(text: str) -> Tuple[int, int]:
    """질의 문자열에서 예산 하한/상한을 추정한다."""
    pattern = re.finditer(r"(\d+)\s*(만|만원|천|천원)?", text)
    values = []
    for match in pattern:
        num = int(match.group(1))
        unit = match.group(2) or ""
        if unit.startswith("만"):
            amount = num * 10000
        elif unit.startswith("천"):
            amount = num * 1000
        elif num < 200:
            amount = num * 10000
        else:
            amount = num
        window = text[max(0, match.start() - 5) : match.end() + 5]
        indicator = "auto"
        for word in ("이하", "이내", "언더", "아래", "밑", "까지"):
            if word in window:
                indicator = "max"
        for word in ("이상", "이후", "부터", "넘", "초과"):
            if word in window:
                indicator = "min"
        values.append((amount, indicator))
    budget_min = None
    budget_max = None
    for amount, indicator in values:
        if indicator == "min":
            budget_min = max(budget_min or 0, amount)
        elif indicator == "max":
            budget_max = amount if budget_max is None else min(budget_max, amount)
    plain_amounts = [v[0] for v in values]
    if not budget_min and not budget_max and plain_amounts:
        if len(plain_amounts) >= 2:
            budget_min, budget_max = plain_amounts[0], plain_amounts[1]
            if budget_min > budget_max:
                budget_min, budget_max = budget_max, budget_min
        else:
            budget_max = plain_amounts[0]
    return budget_min, budget_max


def extract_slots(query: str) -> Dict:
    """질의에서 예산, 상황, 관계, 금기, 핵심 키워드를 추출한다."""
    normalized = normalize_text(query)
    budget_min, budget_max = _parse_budget(normalized)
    occasion = _find_slot_by_map(normalized, OCCASION_MAP) or ""
    relation = _find_slot_by_map(normalized, RELATION_MAP) or ""

    forbidden = set()
    for canonical, patterns in FORBIDDEN_SYNONYMS.items():
        for pattern in patterns:
            if pattern in normalized:
                forbidden.add(canonical)
                break

    tokens = tokenize(query)
    special_tokens = set()
    for mapping in (OCCASION_MAP, RELATION_MAP):
        for names in mapping.values():
            special_tokens.update(names)
    special_tokens.update(["이상", "이하", "만원", "만", "천", "예산", "budget"])
    special_tokens.update(item for pats in FORBIDDEN_SYNONYMS.values() for item in pats)

    core = []
    seen = set()
    for token in tokens:
        if token in special_tokens:
            continue
        if re.search(r"\d", token):
            continue
        if token in seen:
            continue
        seen.add(token)
        core.append(token)
    core = core[:6]

    return {
        "budget_min": budget_min,
        "budget_max": budget_max,
        "occasion": occasion,
        "relation": relation,
        "forbidden": forbidden,
        "core_keywords": core,
    }


def expand_keywords(core: List[str], model: Optional[Word2Vec], forbidden: Set[str]) -> List[str]:
    """핵심 키워드를 Word2Vec 유사 단어로 확장한다."""
    if model is None:  # Word2Vec 학습을 건너뛰는 경우 코어만 사용
        return list(dict.fromkeys(core))
    expanded = list(dict.fromkeys(core))
    if not core:
        return expanded
    for keyword in core:
        if keyword not in model.wv:
            continue
        added = 0
        for candidate, score in model.wv.most_similar(keyword, topn=5):
            if score < 0.4:
                continue
            if candidate in expanded or candidate in forbidden:
                continue
            expanded.append(candidate)
            added += 1
            if added >= 3:
                break
        if len(expanded) >= 12:
            break
    return expanded


def violates_forbidden(text: str, forbidden: Set[str]) -> bool:
    """상품 텍스트가 금기어 집합과 충돌하는지 여부를 반환한다."""
    for canonical in forbidden:
        for pattern in FORBIDDEN_SYNONYMS.get(canonical, []):
            if pattern in text:
                return True
    return False


def describe_guard(text: str, forbidden: Set[str]) -> str:
    """금기 조건을 만족하는 특징이 있으면 한 줄 설명을 만든다."""
    guard_terms = {
        "무향": ["무향", "무향료", "향없음"],
        "무알코올": ["무알코올", "논알코올", "alcoholfree"],
        "무카페인": ["무카페인", "디카페인"],
        "저자극": ["저자극", "민감"],
    }
    hits = []
    for label, terms in guard_terms.items():
        for term in terms:
            if term in text:
                hits.append(label)
                break
    if not hits or not forbidden:
        return ""
    return "금기 충족: " + "/".join(hits[:2])


def compute_budget_fit(price: int, budget_min: int, budget_max: int) -> Tuple[float, bool]:
    """가격이 예산 범위와 얼마나 가까운지 (및 이탈 여부)를 계산한다."""
    if budget_min is None and budget_max is None:
        return 1.0, False
    lo = budget_min if budget_min is not None else 0
    hi = budget_max if budget_max is not None else max(price, lo)
    mid = (lo + hi) / 2 if (budget_min is not None and budget_max is not None) else (hi if budget_max else lo)
    mid = max(mid, 1.0)
    diff = abs(price - mid)
    score = max(0.0, 1 - diff / max(mid, 1.0))
    outside = False
    if budget_min is not None and price < budget_min:
        outside = True
    if budget_max is not None and price > budget_max:
        outside = True
    if outside:
        score *= 0.4
    return score, outside


def compute_context_score(text: str, slots: Dict) -> float:
    """occasion/relation이 상품 텍스트에 드러나면 추가 가점을 준다."""
    score = 0.0
    occasion = slots.get("occasion")
    relation = slots.get("relation")
    if occasion:
        hints = OCCASION_HINTS.get(occasion, [occasion])
        if any(hint in text for hint in hints):
            score += 0.06
    if relation:
        hints = RELATION_HINTS.get(relation, [relation])
        if any(hint in text for hint in hints):
            score += 0.06
    return min(score, 0.12)
