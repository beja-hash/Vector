from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings


router = APIRouter(prefix="/settings", tags=["settings"])


class LlmSettingsRead(BaseModel):
    polza_enabled: bool
    llm_scoring_enabled: bool
    model: str
    threshold: int
    review_min_score: int


@router.get("/llm", response_model=LlmSettingsRead)
def get_llm_settings() -> LlmSettingsRead:
    return LlmSettingsRead(
        polza_enabled=settings.polza_enabled,
        llm_scoring_enabled=settings.llm_scoring_enabled,
        model=settings.polza_model,
        threshold=settings.llm_scoring_threshold,
        review_min_score=settings.llm_scoring_review_min_score,
    )
