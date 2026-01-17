from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    gender: Optional[str] = Field(default=None, max_length=20)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    interest: Optional[str] = Field(default="", max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RecommendRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=500)
    top_n: Optional[int] = Field(default=50, ge=1, le=200)
    expand_k: Optional[int] = Field(default=5, ge=0, le=20)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    session_id: Optional[str] = Field(default=None, max_length=64)
    top_n: Optional[int] = Field(default=10, ge=1, le=50)
    skip_slots: bool = Field(default=False)
    force_recommend: bool = Field(default=False)


class ChatbotEventRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    event: str = Field(min_length=1, max_length=50)
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GiftsByKeywordRequest(BaseModel):
    category: str = Field(min_length=1, max_length=50)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    gender: Optional[str] = Field(default=None, max_length=20)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    interest: Optional[str] = Field(default=None, max_length=200)

    def has_changes(self) -> bool:
        return any(
            getattr(self, field) is not None
            for field in ("name", "gender", "age", "interest")
        )


class LogActivityRequest(BaseModel):
    event: str = Field(min_length=1, max_length=50)
    payload: Optional[dict] = Field(default_factory=dict)


class SearchLogRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=500)
    context: Optional[str] = Field(default=None, max_length=200)
    source: Optional[str] = Field(default="recommend", max_length=50)


class SurveyAnswerRequest(BaseModel):
    search_log_id: Optional[str] = Field(default=None, max_length=128)
    search_sentence: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=500)
    reason: Optional[str] = Field(default=None, min_length=1, max_length=500)


class FavoriteRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=300)
    image_url: Optional[str] = Field(default=None, max_length=1024)
    price: Optional[str] = Field(default=None, max_length=100)
    link: Optional[str] = Field(default=None, max_length=1024)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    liked: bool = Field(default=True)


class RegressionResultRequest(BaseModel):
    model_version: str = Field(min_length=1, max_length=50)
    run_id: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(pattern="^(passed|failed|warning)$")
    metrics: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = Field(default=None, max_length=500)


class RatingRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    rating: float = Field(ge=0.0, le=5.0)
