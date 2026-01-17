import importlib
import json
import logging
import os
from datetime import timedelta
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, send_from_directory, make_response, g
from flask_cors import CORS
from dotenv import load_dotenv
from pydantic import ValidationError
from google.cloud import firestore

from model.service.common import *  # Firebase 초기화/클라이언트
from model.service.errors import ok, err, AppError, AuthError, validation_error_response
from model.service.schemas import (
    RegisterRequest,
    LoginRequest,
    RecommendRequest,
    GiftsByKeywordRequest,
    ChatMessageRequest,
    ChatbotEventRequest,
    LogActivityRequest,
    ProfileUpdateRequest,
    SearchLogRequest,
    SurveyAnswerRequest,
    FavoriteRequest,
    RegressionResultRequest,
    RatingRequest,
)
from model.service.auth.jwt_utils import create_jwt, jwt_required, decode_jwt
from model.service.auth.reg import add_user, check_user_exists
from model.service.auth.log import login_user
from model.service.auth.profile import fetch_user_profile, update_user_profile
from model.service.main.product import get_gifts_by_keyword
from model.service.log.log import insert_log
from model.recommender import run_recommender, warm_recommender_env_async
from model.service.chat.processor import handle_chat_message
from model.service.chatbot import handle_chatbot_event, ChatbotError
from model.service.admin import build_admin_insights
from model.service.search.logs import (
    record_search_log,
    update_search_log,
    fetch_random_search_prompt,
    store_survey_feedback,
    list_survey_feedback,
    approve_survey_feedback,
    reject_survey_feedback,
)


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)
app_logger = logging.getLogger("gift_app")

# Load env
load_dotenv()

# Flask app
app = Flask(__name__)
app.logger.handlers = []  # avoid duplicate logs when Flask auto-configures handlers
app.logger.propagate = True
app.logger.setLevel(logging.INFO)

default_cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
extra_cors_origins = os.getenv("CORS_EXTRA_ORIGINS")
if extra_cors_origins:
    default_cors_origins.extend(
        origin.strip()
        for origin in extra_cors_origins.split(",")
        if origin.strip()
    )

CORS(app, supports_credentials=True, origins=default_cors_origins)  # vite dev

BASE_URL = "http://localhost:8000/"
IMAGE_ROOT = os.path.abspath(os.getenv("IMAGE_ROOT", os.path.join("back", "data", "images")))
LABEL_DIR = os.path.abspath(os.getenv("LABEL_DIR", os.path.join("back", "data", "label_data")))


def _get_optional_user_email() -> Optional[str]:
    token = request.cookies.get("auth")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        claims = decode_jwt(token)
    except AuthError:
        return None
    return claims.get("sub")


def _get_user_claims() -> Dict[str, Any]:
    return getattr(g, "user_claims", {}) or {}


def _parse_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")


def _require_admin():
    claims = _get_user_claims()
    role = claims.get("role")
    if role != "admin":
        raise AuthError("Admin privileges required", status=403, code="ADMIN_ONLY")
    return claims


def _update_rating_summary(product_id: str, user_email: str, rating_value: float) -> Dict[str, Any]:
    transaction = FIRESTORE_DB.transaction()
    detail_ref = FIRESTORE_DB.collection("product_ratings").document(f"{product_id}__{user_email}")
    summary_ref = FIRESTORE_DB.collection("product_rating_summary").document(product_id)

    @firestore.transactional
    def _tx(transaction):
        prev_snapshot_iter = transaction.get(detail_ref)
        prev_snapshot = next(prev_snapshot_iter, None)
        prev_rating = (
            prev_snapshot.get("rating")
            if prev_snapshot is not None and prev_snapshot.exists
            else None
        )

        summary_snapshot_iter = transaction.get(summary_ref)
        summary_snapshot = next(summary_snapshot_iter, None)
        has_summary = summary_snapshot is not None and summary_snapshot.exists
        current_sum = float(summary_snapshot.get("sum", 0.0)) if has_summary else 0.0
        current_count = int(summary_snapshot.get("count", 0)) if has_summary else 0

        if prev_rating is None:
            new_count = current_count + 1
            new_sum = current_sum + rating_value
        else:
            new_count = current_count
            new_sum = current_sum - float(prev_rating) + rating_value

        average = new_sum / new_count if new_count > 0 else 0.0

        transaction.set(
            detail_ref,
            {
                "product_id": product_id,
                "user_email": user_email,
                "rating": rating_value,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
        )

        transaction.set(
            summary_ref,
            {
                "product_id": product_id,
                "sum": new_sum,
                "count": new_count,
                "average": average,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        return {"product_id": product_id, "average": average, "count": new_count}

    return _tx(transaction)


def log_current_model_metrics():
    try:
        docs = (
            FIRESTORE_DB.collection("model_regressions")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        latest = next(docs, None)
    except Exception as exc:
        app_logger.warning("Failed to read regression metrics: %s", exc)
        return

    if not latest:
        app_logger.info("[model] regression 기록이 아직 없습니다.")
        return

    data = latest.to_dict() or {}
    app_logger.info(
        "[model] version=%s status=%s metrics=%s",
        data.get("model_version", "unknown"),
        data.get("status", "n/a"),
        data.get("metrics") or {},
    )


def _should_run_startup() -> bool:
    """
    디버그 리로더(werkzeug)가 부모/자식 프로세스를 두 번 띄우는 것을 감지해
    실제 서비스 프로세스에서만 초기화가 실행되도록 한다.
    """
    run_main = os.environ.get("WERKZEUG_RUN_MAIN")
    # debug=False인 경우 run_main은 None → 실행, debug=True인 경우 자식 프로세스에서 "true"
    return run_main in (None, "true")


# Initialize recommendation once
if _should_run_startup():
    try:
        log_current_model_metrics()
        warm_recommender_env_async(app_logger)
    except Exception as e:
        print(f"[⚠️] 추천 환경 초기화 실패: {e}")

# -------------------- Static Files --------------------
# 이미지 파일 제공 엔드포인트
@app.route('/data/images/<path:filename>')
def serve_image(filename):
    # 안전한 디렉토리 제공
    return send_from_directory(IMAGE_ROOT, filename)

# -------------------- Auth --------------------
# 로그인 API (DB 사용자 인증)
@app.route('/api/login', methods=['POST'])
def login():
    try:
        body = LoginRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        app_logger.warning("Login validation failed: %s", ve.errors())
        return validation_error_response(ve)

    app_logger.info("Login attempt email=%s", body.email)
    user_info = login_user(body.email, body.password)
    if not user_info:
        app_logger.warning("Login failed email=%s", body.email)
        return err("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)

    token = create_jwt({"sub": user_info["email"], "role": user_info.get("role", "user")})
    resp = make_response(ok({
        "token": token,
        "profile": user_info,
    }))
    app_logger.info("Login success email=%s", body.email)
    # Cookie for browser usage
    resp.set_cookie("auth", token, httponly=True, samesite="Lax", max_age=int(os.getenv("JWT_EXPIRES_MIN", "1440"))*60)
    return resp

# 회원가입 API
@app.route('/api/register', methods=['POST'])
def register():
    try:
        body = RegisterRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        app_logger.warning("Register validation failed: %s", ve.errors())
        return validation_error_response(ve)

    app_logger.info("Register attempt email=%s", body.email)
    if not check_user_exists(body.email):
        app_logger.warning("Register duplicate email=%s", body.email)
        return err("ALREADY_EXISTS", "이미 존재하는 이메일입니다.", 400)

    ok_created = add_user(body.name, body.email, body.password, body.gender, body.age, body.interest)
    if not ok_created:
        app_logger.error("Register create failed email=%s", body.email)
        return err("CREATE_FAILED", "사용자 생성에 실패했습니다.", 500)
    app_logger.info("Register success email=%s", body.email)
    return ok({"email": body.email})

# 임시 비밀번호 찾기 (테스트용)
@app.route("/api/find-password", methods=["POST"])
def find_password():
    return err("NOT_IMPLEMENTED", "지원 예정입니다.", 501)

# -------------------- Recommendation --------------------
# 추천 API
@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        body = RecommendRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    app_logger.info("recommend request: sentence=%s top_n=%s", body.sentence, body.top_n)

    hard_budget = _parse_bool(request.args.get("hard_budget"))

    log_id = None
    try:
        log_id = record_search_log(
            body.sentence,
            user_email=_get_optional_user_email(),
            metadata={
                "top_n": body.top_n,
                "expand_k": body.expand_k,
            },
        )
    except Exception as exc:
        app_logger.warning("Search log write failed: %s", exc)

    # 항상 Top-K 50개를 반환해 UI에 충분한 후보를 제공한다.
    top_k = 50

    try:
        payload = run_recommender(
            sentence=body.sentence,
            top_k=top_k,
            hard_budget=hard_budget,
            search_log_id=log_id,
            logger=app_logger,
        )
        app_logger.info(
            "recommender response: sentence=%s top_k=%s log_id=%s results=%s",
            body.sentence,
            top_k,
            log_id,
            len(payload.get("results") or []),
        )
        # 학습/분석용으로 추천 상위 일부를 검색 로그 메타데이터에 저장
        try:
            if log_id:
                results = payload.get("results") or []
                slim_results = [
                    {"id": item.get("id"), "score": item.get("score")}
                    for item in results[:20]
                ]
                update_search_log(
                    log_id,
                    metadata={
                        "top_k": top_k,
                        "slots": payload.get("slots") or {},
                        "results": slim_results,
                    },
                )
        except Exception as exc:
            app_logger.debug("Search log enrichment skipped: %s", exc)
        return ok(payload)
    except Exception as exc:  # pragma: no cover - 방어적 폴백
        app_logger.error("recommender failed: %s", exc, exc_info=True)
        fallback_payload = {
            "results": [],
            "slots": {},
            "meta": {"engine": "recommender", "search_log_id": log_id},
            "path1": [],
            "path2": [],
        }
        return ok(fallback_payload)


@app.route("/api/chat", methods=["POST"])
def chat_message():
    try:
        body = ChatMessageRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    user_email = _get_optional_user_email()
    payload = handle_chat_message(
        message=body.message,
        user_email=user_email,
        session_id=body.session_id,
        top_n=body.top_n or 10,
        skip_slots=body.skip_slots,
        force_recommend=body.force_recommend,
    )
    return ok(payload)


@app.route("/api/chatbot/events", methods=["POST"])
def chatbot_events():
    try:
        body = ChatbotEventRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    user_email = _get_optional_user_email()
    try:
        payload = handle_chatbot_event(body.event, body.session_id, body.payload, user_email)
    except ChatbotError as exc:
        return err("CHATBOT_VALIDATION_FAILED", str(exc), 400)
    except Exception as exc:  # pragma: no cover - defensive
        app_logger.error("Chatbot event failed: %s", exc, exc_info=True)
        return err("CHATBOT_EVENT_FAILED", "챗봇 요청을 처리하지 못했습니다.", 500)
    return ok(payload)


@app.route("/api/search-logs", methods=["POST"])
def create_search_log():
    try:
        body = SearchLogRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    metadata = {"source": body.source}
    if body.context:
        metadata["context"] = body.context

    try:
        log_id = record_search_log(
            body.sentence,
            user_email=_get_optional_user_email(),
            metadata=metadata,
        )
    except Exception as exc:
        app_logger.error("Search log endpoint failed: %s", exc)
        return err("LOG_WRITE_FAILED", "검색 로그 저장에 실패했습니다.", 500)
    return ok({"id": log_id})


@app.route("/api/survey/search-prompt", methods=["GET"])
def survey_search_prompt():
    prompt = fetch_random_search_prompt()
    if not prompt:
        return ok(None)
    return ok(prompt)


@app.route("/api/survey/answers", methods=["POST"])
def survey_answers():
    try:
        body = SurveyAnswerRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    try:
        feedback_id = store_survey_feedback(
            search_log_id=body.search_log_id,
            search_sentence=body.search_sentence,
            answer=body.answer,
            user_email=_get_optional_user_email(),
            reason=body.reason,
        )
    except Exception as exc:
        app_logger.error("Survey feedback store failed: %s", exc)
        return err("SURVEY_STORE_FAILED", "설문 응답 저장에 실패했습니다.", 500)
    return ok({"feedback_id": feedback_id})


@app.route("/api/admin/regressions", methods=["GET", "POST"])
@jwt_required
def admin_regressions():
    _require_admin()
    if request.method == "POST":
        try:
            body = RegressionResultRequest(**(request.get_json() or {}))
        except ValidationError as ve:
            return validation_error_response(ve)
        doc = FIRESTORE_DB.collection("model_regressions").document()
        payload = {
            "model_version": body.model_version,
            "run_id": body.run_id,
            "status": body.status,
            "metrics": body.metrics,
            "notes": body.notes,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        doc.set(payload)
        return ok({"id": doc.id})

    limit = min(int(request.args.get("limit", 50)), 200)
    docs = (
        FIRESTORE_DB.collection("model_regressions")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    results = [{"id": doc.id, **(doc.to_dict() or {})} for doc in docs]
    return ok({"items": results})


@app.route("/api/admin/search-feedback", methods=["GET"])
@jwt_required
def admin_search_feedback():
    _require_admin()
    status = request.args.get("status") or "pending"
    entries = list_survey_feedback(status=status if status else None, limit=100)
    return ok({"items": entries})


@app.route("/api/admin/search-feedback/<feedback_id>/approve", methods=["POST"])
@jwt_required
def approve_feedback(feedback_id: str):
    _require_admin()
    try:
        payload = approve_survey_feedback(feedback_id)
    except ValueError:
        return err("NOT_FOUND", "피드백을 찾을 수 없습니다.", 404)
    return ok(payload)


@app.route("/api/admin/search-feedback/<feedback_id>/reject", methods=["POST"])
@jwt_required
def reject_feedback(feedback_id: str):
    _require_admin()
    reason = (request.get_json() or {}).get("reason")
    try:
        reject_survey_feedback(feedback_id, reason=reason)
    except ValueError:
        return err("NOT_FOUND", "피드백을 찾을 수 없습니다.", 404)
    return ok({"rejected": True})


@app.route("/api/admin/insights", methods=["GET"])
@jwt_required
def admin_insights():
    _require_admin()
    data = build_admin_insights()
    return ok(data)

# -------------------- Gifts by Keyword --------------------
# 키워드별 선물 리스트 API
@app.route("/api/gifts-by-keyword", methods=["POST"])
def gifts_by_keyword_route():
    try:
        body = GiftsByKeywordRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)

    gifts = get_gifts_by_keyword(body.category.strip())
    for gift in gifts:
        image_file = str(gift.get("image") or "").replace("\\", "/")
        direct_url = gift.get("image_url") or ""
        if image_file:
            gift["image_url"] = f"{BASE_URL}data/images/{image_file}"
        elif direct_url:
            gift["image_url"] = direct_url
        else:
            gift["image_url"] = ""
    return ok(gifts)

# -------------------- USER LOG DATA --------------------
@app.route("/api/log-activity", methods=["POST"])
def log_activity():
    try:
        body = LogActivityRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        app_logger.warning("Log activity validation failed: %s", ve.errors())
        return validation_error_response(ve)
    insert_log(body.model_dump())
    payload_keys = list((body.payload or {}).keys())
    app_logger.info(
        "User activity logged event=%s payload_keys=%s",
        body.event,
        payload_keys,
    )
    return ok({"logged": True})


@app.route('/api/logout', methods=['POST'])
def logout():
    resp = make_response(ok({"logout": True}))
    resp.set_cookie('auth', '', expires=0)
    return resp


@app.route('/api/me', methods=['GET'])
@jwt_required
def me():
    claims = getattr(g, "user_claims", {}) or {}
    email = claims.get("sub")
    if not email:
        raise AuthError("Invalid token payload", status=401, code="TOKEN_INVALID")
    profile = fetch_user_profile(email)
    if not profile and claims.get("role") == "admin":
        profile = {
            "name": "Administrator",
            "email": "admin",
            "role": "admin",
        }
    if not profile:
        return err("NOT_FOUND", "사용자를 찾을 수 없습니다.", 404)
    return ok(profile)


@app.route('/api/me', methods=['PATCH'])
@jwt_required
def update_me():
    claims = getattr(g, "user_claims", {}) or {}
    email = claims.get("sub")
    if not email:
        raise AuthError("Invalid token payload", status=401, code="TOKEN_INVALID")
    try:
        body = ProfileUpdateRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        app_logger.warning("Profile update validation failed email=%s errors=%s", email, ve.errors())
        return validation_error_response(ve)

    if not body.has_changes():
        return err("NO_CHANGES", "변경할 항목을 입력해주세요.", 400)

    updates = body.model_dump(exclude_none=True)
    updated_profile = update_user_profile(email, updates)
    if not updated_profile:
        return err("NOT_FOUND", "사용자를 찾을 수 없습니다.", 404)

    app_logger.info(
        "Profile updated email=%s fields=%s",
        email,
        list(updates.keys()),
    )
    return ok(updated_profile)


@app.route("/api/favorites", methods=["POST"])
@jwt_required
def upsert_favorite():
    claims = getattr(g, "user_claims", {}) or {}
    email = claims.get("sub")
    if not email:
        raise AuthError("Invalid token payload", status=401, code="TOKEN_INVALID")

    try:
        body = FavoriteRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        app_logger.warning("Favorite request validation failed email=%s errors=%s", email, ve.errors())
        return validation_error_response(ve)

    favorites_ref = FIRESTORE_DB.collection("users").document(email).collection("favorites")
    doc_ref = favorites_ref.document(body.product_id)
    if body.liked:
        payload = {
            "product_id": body.product_id,
            "name": body.name,
            "image_url": body.image_url,
            "price": body.price,
            "link": body.link,
            "metadata": body.metadata or {},
            "liked": True,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.set(payload)
    else:
        doc_ref.delete()
    return ok({"liked": body.liked})


@app.route("/api/me/favorites", methods=["GET"])
@jwt_required
def list_favorites():
    claims = getattr(g, "user_claims", {}) or {}
    email = claims.get("sub")
    if not email:
        raise AuthError("Invalid token payload", status=401, code="TOKEN_INVALID")

    favorites_ref = FIRESTORE_DB.collection("users").document(email).collection("favorites")
    try:
        docs = favorites_ref.order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
    except Exception:
        docs = favorites_ref.stream()

    favorites = []
    for doc in docs:
        data = doc.to_dict() or {}
        data.setdefault("product_id", doc.id)
        favorites.append(data)
    return ok({"items": favorites})


@app.route("/api/ratings", methods=["POST"])
@jwt_required
def submit_rating():
    claims = _get_user_claims()
    email = claims.get("sub")
    if not email:
        raise AuthError("Invalid token payload", status=401, code="TOKEN_INVALID")
    try:
        body = RatingRequest(**(request.get_json() or {}))
    except ValidationError as ve:
        return validation_error_response(ve)
    result = _update_rating_summary(body.product_id, email, float(body.rating))
    return ok(result)


@app.route("/api/ratings/<product_id>", methods=["GET"])
def get_rating(product_id: str):
    doc = FIRESTORE_DB.collection("product_rating_summary").document(product_id).get()
    if not doc.exists:
        return ok({"product_id": product_id, "average": 0.0, "count": 0})
    data = doc.to_dict() or {}
    return ok(
        {
            "product_id": product_id,
            "average": data.get("average", 0.0),
            "count": data.get("count", 0),
        }
    )


# -------------------- Main --------------------
# 서버 실행
if __name__ == '__main__':
    app.run(port=8000, debug=False)

# Global error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(e: ValidationError):
    return validation_error_response(e)


@app.errorhandler(AuthError)
def handle_auth_error(e: AuthError):
    return err(e.code, e.message, e.status)


@app.errorhandler(404)
def handle_404(e):
    return err("NOT_FOUND", "요청한 자원을 찾을 수 없습니다.", 404)


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    # 개발 편의를 위해 메시지 노출
    return err("INTERNAL_ERROR", str(e), 500)
