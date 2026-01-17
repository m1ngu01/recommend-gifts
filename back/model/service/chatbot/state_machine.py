from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from model.service.auth.profile import fetch_user_profile
from model.service.chat.insights import build_segment_key, get_top_keywords_for_segment
from model.service.chatbot import session_store
from model.service.chatbot.session_store import save_session
from model.service.search.logs import record_search_log
from model.recommender import run_recommender

log = logging.getLogger(__name__)

KEYWORD_SLOTS: List[Dict[str, Any]] = [
    {
        "key": "context",
        "label": "상황",
        "question": "어떤 상황인가요?",
        "helper": "예: 생일, 기념일, 위로 선물",
        "required": True,
        "suggestions": ["생일", "기념일", "입학", "승진", "감사"],
    },
    {
        "key": "relationship",
        "label": "관계",
        "question": "어떤 관계이신가요?",
        "helper": "예: 여자친구, 친구, 부모님, 동료",
        "required": True,
        "suggestions": ["여자친구", "남자친구", "친구", "동료", "부모님"],
    },
    {
        "key": "budget",
        "label": "예산",
        "question": "예산은 얼마인가요?",
        "helper": "예: 5만원, 10만원 이하, 20~30만원",
        "required": False,
        "suggestions": ["5만원", "10만원", "20만원", "예산 미정"],
    },
]

PROFILE_FIELDS: List[Dict[str, Any]] = [
    {
        "key": "gender",
        "question": "성별을 알려주세요.",
        "suggestions": ["여성", "남성", "비공개"],
    },
    {
        "key": "age",
        "question": "나이는 어떻게 되나요? (숫자로 입력)",
        "suggestions": ["20", "25", "30", "35", "40"],
    },
    {
        "key": "interest",
        "question": "요즘 관심 있는 취향이나 카테고리를 알려주세요.",
        "suggestions": ["테크", "패션", "여행", "취미", "라이프스타일"],
    },
]


class ChatbotError(ValueError):
    pass


def handle_chatbot_event(event: str, session_id: Optional[str], payload: Optional[Dict[str, Any]], user_email: Optional[str]) -> Dict[str, Any]:
    normalized_event = (event or "").strip().lower()
    if not normalized_event:
        raise ChatbotError("event가 필요합니다.")

    payload = payload or {}

    if normalized_event == "start":
        session_id, session = session_store.create_session(user_email)
        response = _build_flow_select_response(session_id, session)
        save_session(session_id, session)
        return response

    session_id, session = session_store.get_or_create_session(session_id, user_email)
    handlers = {
        "select_flow": _handle_select_flow,
        "submit_slot": _handle_submit_slot,
        "edit_slot": _handle_edit_slot,
        "confirm_keyword": _handle_confirm_keyword,
        "restart_keyword": _handle_restart_keyword,
        "provide_profile": _handle_profile_answer,
        "refresh_similar": _handle_refresh_similar,
    }
    handler = handlers.get(normalized_event)
    if not handler:
        raise ChatbotError(f"지원하지 않는 event 입니다: {event}")
    response = handler(session_id, session, payload, user_email)
    save_session(session_id, session)
    return response


# ---------------------------------------------------------------------------
# Flow selection


def _build_flow_select_response(session_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    session.update(
        {
            "state": "FLOW_SELECT",
            "flow": None,
            "slots": {},
            "skipped_slots": [],
            "profile_inputs": {},
            "pending_slot": None,
            "pending_profile_field": None,
            "last_recommendations": None,
        }
    )
    message = "안녕하세요! 선물 추천을 도와드릴게요. 어떤 방식으로 진행할까요?"
    actions = [
        _action("키워드로 추천 받기", "select_flow", {"flow": "keyword"}),
        _action("비슷한 사람 인기템 보기", "select_flow", {"flow": "similar"}),
    ]
    return _response(session_id, session, message, actions)


def _handle_select_flow(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    flow = (payload.get("flow") or "").lower()
    if flow not in {"keyword", "similar"}:
        raise ChatbotError("flow 값이 잘못되었습니다.")
    session["flow"] = flow
    if flow == "keyword":
        session["slots"] = session.get("slots") or {}
        session["state"] = "ASK_CONTEXT"
        session["pending_slot"] = "context"
        return _response(
            session_id,
            session,
            _question_for_slot("context"),
            [_action("건너뛰기", "submit_slot", {"slot": "context", "skip": True})],
            extra={"expected_slot": "context"},
        )
    profile_context = _merge_profile(user_email, session)
    missing = _missing_profile_fields(profile_context)
    if missing:
        next_field = missing[0]
        session["state"] = "PROFILE_GATHER"
        session["pending_profile_field"] = next_field
        return _profile_question_response(session_id, session, next_field)
    return _run_similar_flow(session_id, session, profile_context, user_email)


# ---------------------------------------------------------------------------
# Keyword flow


def _handle_submit_slot(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    if session.get("flow") != "keyword":
        raise ChatbotError("키워드 플로우를 먼저 선택해주세요.")
    slot_key = payload.get("slot")
    slot_def = _slot_def(slot_key)
    if not slot_def:
        raise ChatbotError("slot 정보가 잘못되었습니다.")

    skip = bool(payload.get("skip"))
    value = (payload.get("value") or "").strip()
    if not value and not skip and slot_def["required"]:
        raise ChatbotError(f"{slot_def['label']}을 입력해주세요.")
    slots = session.setdefault("slots", {})
    skipped = set(session.get("skipped_slots") or [])
    if skip:
        skipped.add(slot_key)
        slots.pop(slot_key, None)
    else:
        slots[slot_key] = value
        skipped.discard(slot_key)
    session["skipped_slots"] = list(skipped)

    next_slot = _next_slot(slots, skipped)
    if next_slot:
        session["state"] = f"ASK_{next_slot.upper()}"
        session["pending_slot"] = next_slot
        return _response(
            session_id,
            session,
            _question_for_slot(next_slot),
            [_action("건너뛰기", "submit_slot", {"slot": next_slot, "skip": True})],
            extra={"expected_slot": next_slot},
        )
    session["state"] = "CONFIRM_KEYWORD"
    session["pending_slot"] = None
    return _keyword_confirmation(session_id, session)


def _handle_edit_slot(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    slot_key = payload.get("slot")
    slot_def = _slot_def(slot_key)
    if not slot_def:
        raise ChatbotError("수정할 slot이 올바르지 않습니다.")
    skipped = set(session.get("skipped_slots") or [])
    skipped.discard(slot_key)
    session["skipped_slots"] = list(skipped)
    session["state"] = f"ASK_{slot_key.upper()}"
    session["pending_slot"] = slot_key
    return _response(
        session_id,
        session,
        _question_for_slot(slot_key),
        [_action("건너뛰기", "submit_slot", {"slot": slot_key, "skip": True})],
        extra={"expected_slot": slot_key},
    )


def _handle_confirm_keyword(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    confirm = bool(payload.get("confirmed"))
    if not confirm:
        slot_to_edit = payload.get("slot") or _next_slot(session.get("slots") or {}, set(session.get("skipped_slots") or []))
        if slot_to_edit:
            return _handle_edit_slot(session_id, session, {"slot": slot_to_edit}, user_email)
        return _keyword_confirmation(session_id, session)
    try:
        recommendation = _run_keyword_recommendation(session, user_email)
    except Exception as exc:  # pragma: no cover
        log.error("Keyword recommendation failed: %s", exc)
        session["state"] = "RETRY_OR_ABORT"
        return _response(
            session_id,
            session,
            "추천을 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            [
                _action("다시 시도", "confirm_keyword", {"confirmed": True}),
                _action("처음으로", "start"),
            ],
        )
    session["state"] = "SHOW_RESULTS"
    session["last_recommendations"] = recommendation
    message = recommendation["message"]
    actions = [
        _action("다시 추천 받기", "restart_keyword"),
        _action("비슷한 사람 보기", "select_flow", {"flow": "similar"}),
        _action("처음으로", "start"),
    ]
    extra = {
        "items": recommendation.get("items"),
        "meta": recommendation.get("meta"),
        "insights": recommendation.get("insights"),
        "query_sentence": recommendation.get("query_sentence"),
    }
    return _response(session_id, session, message, actions, extra=extra)


def _handle_restart_keyword(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    session["slots"] = {}
    session["skipped_slots"] = []
    session["state"] = "ASK_CONTEXT"
    session["pending_slot"] = "context"
    session["last_recommendations"] = None
    return _response(
        session_id,
        session,
        _question_for_slot("context"),
        [_action("건너뛰기", "submit_slot", {"slot": "context", "skip": True})],
        extra={"expected_slot": "context"},
    )


def _keyword_confirmation(session_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    slots = session.get("slots") or {}
    summary_tokens = []
    for slot in KEYWORD_SLOTS:
        value = slots.get(slot["key"])
        summary_tokens.append(f"[{slot['label']}: {value or '입력 없음'}]")
    message = "입력해주신 정보를 확인해주세요.\n" + " ".join(summary_tokens)
    actions = [
        _action("응, 추천 보여줘", "confirm_keyword", {"confirmed": True}),
    ]
    for slot in KEYWORD_SLOTS:
        actions.append(_action(f"{slot['label']} 수정", "edit_slot", {"slot": slot["key"]}))
    actions.append(_action("처음으로", "start"))
    return _response(session_id, session, message, actions)


def _run_keyword_recommendation(session: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    slots = session.get("slots") or {}
    sentence = _compose_sentence(slots)
    profile = _safe_fetch_profile(user_email)
    segment_key = build_segment_key(profile, {"relationship": slots.get("relationship") or ""})
    metadata = {
        "flow": "keyword",
        "slots": slots,
        "segment_key": segment_key,
    }
    log_id = None
    try:
        log_id = record_search_log(sentence, user_email=user_email, metadata=metadata)
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to log keyword recommendation: %s", exc)

    fusion_payload = run_recommender(sentence, top_k=12, hard_budget=False) or {}
    items, meta = _extract_items_and_meta(fusion_payload)
    if log_id:
        meta["search_log_id"] = log_id

    insights = get_top_keywords_for_segment(segment_key, limit=5)
    message_lines = ["조건에 맞는 상품 추천을 준비했습니다."]
    for slot in KEYWORD_SLOTS:
        value = slots.get(slot["key"])
        if value:
            message_lines.append(f"- {slot['label']}: {value}")
    if insights:
        top_keywords = ", ".join(f"{item['keyword']}({item['count']})" for item in insights if item.get("keyword"))
        if top_keywords:
            message_lines.append(f"비슷한 이용자들이 찾은 키워드: {top_keywords}")
    if not items:
        message_lines.append("추천 상품이 아직 없어요. 다른 조건으로 다시 시도해보세요.")
    else:
        message_lines.append(f"총 {len(items)}개의 후보를 찾았습니다. 상위 상품을 아래 카드에서 확인해보세요.")

    return {
        "message": "\n".join(message_lines),
        "items": items,
        "meta": meta,
        "insights": insights,
        "query_sentence": sentence,
    }


# ---------------------------------------------------------------------------
# Similar user flow


def _handle_profile_answer(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    if session.get("flow") != "similar":
        raise ChatbotError("비슷한 사람 보기 플로우를 먼저 선택해주세요.")
    field = payload.get("field")
    field_def = _profile_field(field)
    if not field_def:
        raise ChatbotError("field 값이 잘못되었습니다.")
    value = (payload.get("value") or "").strip()
    if not value:
        raise ChatbotError("값을 입력해주세요.")
    profile_inputs = session.setdefault("profile_inputs", {})
    if field == "age":
        profile_inputs[field] = _normalize_age(value)
    else:
        profile_inputs[field] = value

    profile_context = _merge_profile(user_email, session)
    missing = _missing_profile_fields(profile_context)
    if missing:
        next_field = missing[0]
        session["state"] = "PROFILE_GATHER"
        session["pending_profile_field"] = next_field
        return _profile_question_response(session_id, session, next_field)

    return _run_similar_flow(session_id, session, profile_context, user_email)


def _handle_refresh_similar(session_id: str, session: Dict[str, Any], payload: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    if session.get("flow") != "similar":
        raise ChatbotError("비슷한 사람 보기 플로우를 먼저 선택해주세요.")
    profile_context = _merge_profile(user_email, session)
    if _missing_profile_fields(profile_context):
        session["state"] = "PROFILE_GATHER"
        return _profile_question_response(session_id, session, session.get("pending_profile_field") or "gender")
    return _run_similar_flow(session_id, session, profile_context, user_email)


def _profile_question_response(session_id: str, session: Dict[str, Any], field_key: str) -> Dict[str, Any]:
    field_def = _profile_field(field_key)
    question = field_def["question"]
    suggestions = field_def.get("suggestions") or []
    actions = [_action(value, "provide_profile", {"field": field_key, "value": value}) for value in suggestions]
    actions.append(_action("처음으로", "start"))
    session["pending_profile_field"] = field_key
    return _response(
        session_id,
        session,
        question,
        actions,
        extra={"expected_field": field_key},
    )


def _run_similar_flow(session_id: str, session: Dict[str, Any], profile_context: Dict[str, Any], user_email: Optional[str]) -> Dict[str, Any]:
    segment_key = build_segment_key(profile_context, {})
    keywords = get_top_keywords_for_segment(segment_key, limit=3)
    seed_query = _select_seed_query(keywords, profile_context)

    metadata = {
        "flow": "similar",
        "profile": profile_context,
        "segment_key": segment_key,
    }
    log_id = None
    try:
        log_id = record_search_log(seed_query, user_email=user_email, metadata=metadata)
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to log similar flow query: %s", exc)

    fusion_payload = run_recommender(seed_query, top_k=12, hard_budget=False) or {}
    items, meta = _extract_items_and_meta(fusion_payload)
    if log_id:
        meta["search_log_id"] = log_id

    if not items:
        session["state"] = "SIMILAR_FALLBACK"
        message = "아직 비슷한 이용자 데이터를 찾지 못했어요. 키워드로 다시 시도해볼까요?"
        actions = [
            _action("키워드 플로우로 이동", "select_flow", {"flow": "keyword"}),
            _action("처음으로", "start"),
        ]
        return _response(session_id, session, message, actions, extra={"keywords": keywords})

    session["state"] = "SHOW_SIMILAR"
    session["last_recommendations"] = {"items": items, "meta": meta}
    session["last_segment_key"] = segment_key
    summary = _summarize_profile(profile_context)
    message = f"{summary} 이용자들이 자주 찾은 인기 상품입니다."
    actions = [
        _action("다시 불러오기", "refresh_similar"),
        _action("키워드 질문으로 전환", "select_flow", {"flow": "keyword"}),
        _action("처음으로", "start"),
    ]
    extra = {
        "keywords": keywords,
        "items": items,
        "meta": meta,
        "profile_summary": summary,
        "query_sentence": seed_query,
    }
    return _response(session_id, session, message, actions, extra=extra)


# ---------------------------------------------------------------------------
# Helpers


def _response(session_id: str, session: Dict[str, Any], message: str, actions: List[Dict[str, Any]], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "session_id": session_id,
        "state": session.get("state"),
        "flow": session.get("flow"),
        "message": message,
        "slots": session.get("slots") or {},
        "profile": session.get("profile_inputs") or {},
        "actions": actions,
    }
    if extra:
        payload["data"] = extra
    return payload


def _action(label: str, event: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {"label": label, "event": event}
    if payload:
        data["payload"] = payload
    return data


def _question_for_slot(slot_key: str) -> str:
    slot_def = _slot_def(slot_key)
    if not slot_def:
        return "원하는 정보를 입력해주세요."
    helper = f" ({slot_def['helper']})" if slot_def.get("helper") else ""
    return f"{slot_def['question']}{helper}"


def _slot_def(slot_key: Optional[str]) -> Optional[Dict[str, Any]]:
    for slot in KEYWORD_SLOTS:
        if slot["key"] == slot_key:
            return slot
    return None


def _next_slot(slots: Dict[str, Any], skipped: Optional[set[str]] = None) -> Optional[str]:
    skipped = skipped or set()
    for slot in KEYWORD_SLOTS:
        if slot["key"] in skipped:
            continue
        if not slots.get(slot["key"]):
            return slot["key"]
    return None


def _compose_sentence(slots: Dict[str, Any]) -> str:
    parts: List[str] = []
    context = slots.get("context")
    if context:
        parts.append(context)
    relationship = slots.get("relationship")
    if relationship:
        parts.append(f"{relationship}에게 줄 선물")
    budget = slots.get("budget")
    if budget:
        parts.append(f"(예산 {budget})")
    return " ".join(parts) or "선물 추천"


def _extract_items_and_meta(fusion_payload: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not isinstance(fusion_payload, dict):
        return [], {}
    items = fusion_payload.get("results")
    if items is None:
        items = fusion_payload.get("items")
    if not isinstance(items, list):
        items = []
    meta = {}
    for key in ("query", "path1", "path2"):
        value = fusion_payload.get(key)
        if value is not None:
            meta[key] = value
    return items, meta


def _safe_fetch_profile(user_email: Optional[str]) -> Optional[Dict[str, Any]]:
    if not user_email:
        return None
    try:
        return fetch_user_profile(user_email)
    except Exception as exc:  # pragma: no cover
        log.debug("Failed to fetch profile for %s: %s", user_email, exc)
        return None


def _merge_profile(user_email: Optional[str], session: Dict[str, Any]) -> Dict[str, Any]:
    profile: Dict[str, Any] = {}
    base = _safe_fetch_profile(user_email) or {}
    for field in (field_def["key"] for field_def in PROFILE_FIELDS):
        value = base.get(field)
        if value not in (None, ""):
            profile[field] = value
    overrides = session.get("profile_inputs") or {}
    for key, value in overrides.items():
        if value in (None, ""):
            continue
        profile[key] = value
    return profile


def _missing_profile_fields(profile: Dict[str, Any]) -> List[str]:
    missing = []
    for field in PROFILE_FIELDS:
        if profile.get(field["key"]) in (None, ""):
            missing.append(field["key"])
    return missing


def _profile_field(field_key: Optional[str]) -> Optional[Dict[str, Any]]:
    for field in PROFILE_FIELDS:
        if field["key"] == field_key:
            return field
    return None


def _normalize_age(value: str) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _select_seed_query(keywords: List[Dict[str, Any]], profile: Dict[str, Any]) -> str:
    if keywords:
        top_keyword = keywords[0].get("keyword")
        if top_keyword:
            return f"{top_keyword} 인기 선물 추천"
    interest = profile.get("interest")
    if interest:
        return f"{interest} 선물 인기 순위"
    return "인기 선물 추천"


def _summarize_profile(profile: Dict[str, Any]) -> str:
    parts = []
    gender = profile.get("gender")
    if gender:
        parts.append(f"{gender}")
    age = profile.get("age")
    if age:
        parts.append(f"{age}세")
    interest = profile.get("interest")
    if interest:
        parts.append(f"{interest} 취향")
    summary = " · ".join(parts)
    return summary or "비슷한 이용자"
