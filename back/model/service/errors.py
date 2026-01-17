from typing import Optional, Dict, Any, Iterable


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, extra: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.extra = extra or {}


class AuthError(AppError):
    def __init__(self, message: str = "Unauthorized", status: int = 401, code: str = "AUTH_ERROR"):
        super().__init__(code=code, message=message, status=status)


def ok(data: Any = None) -> Dict[str, Any]:
    return {"ok": True, "data": data, "error": None}


def err(code: str, message: str, status: int = 400, extra: Optional[Dict[str, Any]] = None):
    payload = {"ok": False, "data": None, "error": {"code": code, "message": message}}
    if extra:
        payload["error"].update(extra)
    return payload, status


_FIELD_LABELS = {
    "name": "이름",
    "email": "이메일",
    "password": "비밀번호",
    "gender": "성별",
    "age": "나이",
    "interest": "관심사",
}


def _translate_message(loc: Iterable[Any], msg: str) -> str:
    field = ""
    if loc:
        field = str(loc[-1])
    label = _FIELD_LABELS.get(field, field)
    lower = msg.lower()

    if "field required" in lower:
        core = "필수 입력 항목입니다."
    elif "value is not a valid email" in lower:
        core = "올바른 이메일 형식이 아닙니다."
    elif "ensure this value has at least" in lower:
        core = "최소 길이 조건을 만족하지 않습니다."
    elif "ensure this value has at most" in lower:
        core = "최대 길이 조건을 초과했습니다."
    elif "value_error.number.not_ge" in lower or "greater than or equal" in lower:
        core = "허용된 최소값보다 작습니다."
    elif "value_error.number.not_le" in lower or "less than or equal" in lower:
        core = "허용된 최대값을 초과했습니다."
    elif "type_error.int" in lower or "value is not a valid integer" in lower:
        core = "숫자 형식이 올바르지 않습니다."
    else:
        core = msg

    if label:
        return f"{label}: {core}"
    return core


def format_validation_errors(errors: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    details = []
    for item in errors:
        loc = item.get("loc", ())
        msg = item.get("msg", "Invalid value")
        translated = _translate_message(loc, msg)
        details.append(translated)
    message = details[0] if details else "입력값을 확인해주세요."
    return {"message": message, "details": details}


def validation_error_response(validation_error) -> Any:
    formatted = format_validation_errors(validation_error.errors())
    return (
        {
            "ok": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": formatted["message"],
                "details": formatted["details"],
            },
        },
        422,
    )
