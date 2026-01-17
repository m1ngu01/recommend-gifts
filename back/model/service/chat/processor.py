from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from model.service.auth.profile import fetch_user_profile
from model.service.chat import session_store
from model.service.chat.insights import build_segment_key, get_top_keywords_for_segment
from model.service.search.logs import record_search_log
from model.recommender import run_recommender

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlotDefinition:
    key: str
    question: str
    required: bool = True


SLOT_DEFINITIONS: List[SlotDefinition] = [
    SlotDefinition("relationship", "어떤 관계인가요? (예: 남자친구, 친구, 동료)", True),
    SlotDefinition("occasion", "어떤 상황인가요? (예: 생일, 기념일, 위로 선물)", True),
    SlotDefinition("budget", "예산은 어느 정도인가요? (예: 3~5만원, 10만원 이하)", False),
]

RELATIONSHIP_MAP = {
    "남자친구": "남자친구",
    "여자친구": "여자친구",
    "연인": "연인",
    "친구": "친구",
    "동료": "직장동료",
    "부모": "부모님",
    "엄마": "어머니",
    "아빠": "아버지",
    "형": "형제",
    "누나": "누나",
    "언니": "언니",
    "동생": "동생",
}

OCCASION_MAP = {
    "생일": "생일",
    "기념일": "기념일",
    "졸업": "졸업",
    "입학": "입학",
    "승진": "승진",
    "위로": "위로",
    "감사": "감사",
    "발렌타인": "발렌타인",
    "화이트": "화이트데이",
    "크리스마스": "크리스마스",
}

BUDGET_PATTERN = re.compile(r"(\d+)\s*(?:만원|만\s*원|만원대|만\s*원대|원)")
RANGE_PATTERN = re.compile(r"(\d+)\s*~\s*(\d+)\s*만원")
SKIP_TOKENS = {"건너뛰", "pass", "skip", "몰라", "없어", "굳이", "나중에"}


def handle_chat_message(
    message: str,
    user_email: Optional[str],
    session_id: Optional[str],
    *,
    top_n: int,
    skip_slots: bool,
    force_recommend: bool,
) -> Dict[str, Any]:
    session_id, session_doc = session_store.get_or_create_session(session_id, user_email)
    state = session_doc.get("state") or {}
    slots = dict(state.get("slots") or {})
    awaiting_slot = state.get("awaiting_slot")
    skipped_slots = set(state.get("skipped_slots") or [])

    session_store.append_message(session_id, "user", message, {"source": "chatbot"})

    skip_intent = skip_slots or _has_skip_intent(message)
    if skip_intent and awaiting_slot:
        skipped_slots.add(awaiting_slot)

    extracted = _extract_slots_from_message(message)
    for key, value in extracted.items():
        if value:
            slots[key] = value
            skipped_slots.discard(key)

    missing_slots = _missing_required_slots(slots, skipped_slots)
    next_slot_key = missing_slots[0] if missing_slots else None

    if missing_slots and not (force_recommend or skip_intent):
        prompt = _build_question(next_slot_key)
        _persist_state(session_id, slots, next_slot_key, skipped_slots)
        session_store.append_message(
            session_id,
            "assistant",
            prompt,
            {"type": "slot_question", "slot": next_slot_key},
        )
        return {
            "session_id": session_id,
            "status": "ASKING_SLOT",
            "reply": prompt,
            "slots": slots,
            "missing_slots": missing_slots,
        }

    _persist_state(session_id, slots, None, skipped_slots)

    search_sentence = _compose_sentence(slots, message)
    profile = _safe_fetch_profile(user_email)
    segment_key = build_segment_key(profile, slots) if profile or slots else None

    metadata = {
        "source": "chatbot",
        "channel": "chatbot",
        "slots": slots,
        "skipped_slots": list(skipped_slots),
    }

    log_id = None
    try:
        log_id = record_search_log(
            search_sentence,
            user_email=user_email,
            metadata=metadata,
            extra_fields={
                "channel": "chatbot",
                "segment_key": segment_key,
            },
        )
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to record chat search log: %s", exc)

    recommendations = None
    try:
        recommendations = run_recommender(
            search_sentence,
            top_k=min(top_n, 40),
            hard_budget=False,
            search_log_id=log_id,
            logger=log,
        )
    except Exception as exc:  # pragma: no cover
        log.error("Chat recommendation failed: %s", exc)

    insights = get_top_keywords_for_segment(segment_key, limit=5)

    reply = _build_recommendation_reply(slots, recommendations, insights)
    payload: Dict[str, Any] = {
        "session_id": session_id,
        "status": "RECOMMENDATION",
        "reply": reply,
        "slots": slots,
        "missing_slots": [],
        "keyword_insights": insights,
        "search_log_id": log_id,
        "segment_key": segment_key,
    }
    if recommendations:
        payload["recommendations"] = recommendations

    session_store.append_message(
        session_id,
        "assistant",
        reply,
        {
            "type": "recommendation",
            "search_log_id": log_id,
            "segment_key": segment_key,
        },
    )
    return payload


def _persist_state(session_id: str, slots: Dict[str, Any], awaiting_slot: Optional[str], skipped_slots: set[str]) -> None:
    session_store.update_session_state(
        session_id,
        {
            "state": {
                "slots": slots,
                "awaiting_slot": awaiting_slot,
                "skipped_slots": list(skipped_slots),
            }
        },
    )


def _missing_required_slots(slots: Dict[str, Any], skipped_slots: set[str]) -> List[str]:
    missing = []
    for slot in SLOT_DEFINITIONS:
        if not slot.required:
            continue
        value = slots.get(slot.key)
        if value:
            continue
        if slot.key in skipped_slots:
            continue
        missing.append(slot.key)
    return missing


def _build_question(slot_key: Optional[str]) -> str:
    target = next((slot for slot in SLOT_DEFINITIONS if slot.key == slot_key), None)
    if not target:
        return "조금 더 자세히 알려주시면 추천을 도와드릴게요. (건너뛰려면 '건너뛰기'라고 답해주세요)"
    return f"{target.question} (건너뛰려면 '건너뛰기'라고 답해주세요)"


def _build_recommendation_reply(slots: Dict[str, Any], recommendations: Optional[Dict[str, Any]], insights: List[Dict[str, Any]]) -> str:
    lines = ["조건에 맞춰 추천 목록을 준비했어요."]
    for label, key in (("관계", "relationship"), ("상황", "occasion"), ("예산", "budget")):
        value = slots.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    if insights:
        top_words = ", ".join(f"{item['keyword']}({item['count']})" for item in insights if item.get("keyword"))
        if top_words:
            lines.append(f"비슷한 이용자들이 찾은 키워드: {top_words}")
    if not recommendations:
        lines.append("추천 엔진이 잠시 응답하지 않아 기본 키워드를 안내드렸어요.")
    else:
        meta = recommendations.get("meta") or {}
        items = recommendations.get("results") or recommendations.get("items") or []
        lines.append(f"총 {len(items)}개의 후보를 찾았습니다. 상위 카드에서 바로 확인하세요.")
        if meta.get("search_log_id"):
            lines.append("카드에서 만족도를 눌러주시면 다음 추천이 더 정확해집니다.")
    return "\n".join(lines)


def _extract_slots_from_message(message: str) -> Dict[str, str]:
    text = message.strip()
    extracted: Dict[str, str] = {}
    lowered = text.lower()
    for keyword, normalized in RELATIONSHIP_MAP.items():
        if keyword in text:
            extracted["relationship"] = normalized
            break
    for keyword, normalized in OCCASION_MAP.items():
        if keyword in text:
            extracted["occasion"] = normalized
            break
    range_match = RANGE_PATTERN.search(text)
    if range_match:
        start, end = range_match.groups()
        extracted["budget"] = f"{start}~{end}만원대"
        return extracted
    match = BUDGET_PATTERN.search(text)
    if match:
        value = match.group(1)
        extracted["budget"] = f"{value}만원대"
    elif "만원" in text or "원" in text:
        extracted["budget"] = "예산 미정(원 언급)"

    if not extracted.get("relationship"):
        if "boyfriend" in lowered:
            extracted["relationship"] = "남자친구"
        elif "girlfriend" in lowered:
            extracted["relationship"] = "여자친구"

    if not extracted.get("occasion"):
        if "anniversary" in lowered:
            extracted["occasion"] = "기념일"
        elif "birthday" in lowered:
            extracted["occasion"] = "생일"
    return extracted


def _compose_sentence(slots: Dict[str, Any], message: str) -> str:
    parts = []
    if slots.get("relationship"):
        parts.append(f"{slots['relationship']}에게 줄")
    if slots.get("occasion"):
        parts.append(f"{slots['occasion']} 맞춤")
    if slots.get("budget"):
        parts.append(f"예산 {slots['budget']}")
    parts.append(message)
    return " ".join(parts)


def _has_skip_intent(message: str) -> bool:
    lowered = message.lower()
    for token in SKIP_TOKENS:
        if token in message or token in lowered:
            return True
    return False


def _safe_fetch_profile(user_email: Optional[str]) -> Optional[Dict[str, Any]]:
    if not user_email:
        return None
    try:
        return fetch_user_profile(user_email)
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to fetch profile for %s: %s", user_email, exc)
        return None
