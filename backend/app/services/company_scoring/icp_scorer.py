import logging
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.services.company_scoring.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from app.services.company_scoring.schemas import CompanyForScoring, IcpProfile, IcpScoreResult
from app.services.llm import PolzaClient

logger = logging.getLogger(__name__)


class CompanyIcpScorer:
    def __init__(
        self,
        *,
        client: PolzaClient | None = None,
        threshold: int | None = None,
        review_min_score: int | None = None,
        max_input_chars: int | None = None,
    ) -> None:
        self.client = client or PolzaClient()
        self.threshold = threshold if threshold is not None else settings.llm_scoring_threshold
        self.review_min_score = review_min_score if review_min_score is not None else settings.llm_scoring_review_min_score
        self.max_input_chars = max_input_chars if max_input_chars is not None else settings.llm_scoring_max_input_chars

    async def score_company(self, icp: IcpProfile, company: CompanyForScoring) -> IcpScoreResult:
        logger.info("[LLM][ICP] scoring company: %s inn=%s", company.company_name or company.full_company_name, company.inn)
        logger.info("[LLM][ICP] model=%s", self.client.model)
        user_prompt = build_user_prompt(icp, company, self.max_input_chars)
        raw_result = await self.client.complete_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=220,
        )
        result = self._parse_result(raw_result)
        result = self.apply_score_policy(result)
        logger.info("[LLM][ICP] result score=%s action=%s", result.score, result.recommended_action)
        return result

    def apply_score_policy(self, result: IcpScoreResult) -> IcpScoreResult:
        if result.score >= self.threshold:
            return result.model_copy(update={"is_match": True, "recommended_action": "add_to_results"})
        if result.score >= self.review_min_score:
            return result.model_copy(update={"recommended_action": "manual_review"})
        return result.model_copy(update={"is_match": False, "recommended_action": "skip"})

    def _parse_result(self, raw_result: dict[str, Any]) -> IcpScoreResult:
        score = _coerce_score(raw_result.get("score"))
        payload = {
            "is_match": bool(raw_result.get("is_match", score >= self.threshold)),
            "score": score,
            "confidence": _coerce_confidence(raw_result.get("confidence")),
            "fit_reason": _optional_str(raw_result.get("fit_reason")),
            "mismatch_reason": _optional_str(raw_result.get("mismatch_reason")),
            "matched_criteria": _as_list(raw_result.get("matched_criteria")),
            "failed_criteria": _as_list(raw_result.get("failed_criteria")),
            "recommended_action": _coerce_action(raw_result.get("recommended_action")),
        }
        try:
            return IcpScoreResult.model_validate(payload)
        except ValidationError as exc:
            logger.warning("[LLM][ICP] invalid json response")
            raise ValueError("Invalid ICP scoring payload") from exc


def hard_prefilter_company(icp: IcpProfile, company: CompanyForScoring) -> str | None:
    region_reason = _region_mismatch(icp, company)
    if region_reason:
        return region_reason
    if icp.revenue_min is not None and company.revenue is not None and company.revenue < icp.revenue_min:
        return f"revenue {company.revenue} below minimum {icp.revenue_min}"
    if icp.revenue_max is not None and company.revenue is not None and company.revenue > icp.revenue_max:
        return f"revenue {company.revenue} above maximum {icp.revenue_max}"
    if icp.employees_min is not None and company.employees_count is not None and company.employees_count < icp.employees_min:
        return f"employees {company.employees_count} below minimum {icp.employees_min}"
    if icp.employees_max is not None and company.employees_count is not None and company.employees_count > icp.employees_max:
        return f"employees {company.employees_count} above maximum {icp.employees_max}"
    return None


def hard_skip_result(reason: str) -> IcpScoreResult:
    return IcpScoreResult(
        is_match=False,
        score=0,
        confidence="high",
        fit_reason=None,
        mismatch_reason=reason,
        matched_criteria=[],
        failed_criteria=[reason],
        recommended_action="skip",
    )


def manual_review_result(reason: str) -> IcpScoreResult:
    return IcpScoreResult(
        is_match=False,
        score=settings.llm_scoring_review_min_score,
        confidence="low",
        fit_reason=None,
        mismatch_reason=reason,
        matched_criteria=[],
        failed_criteria=[reason],
        recommended_action="manual_review",
    )


def _region_mismatch(icp: IcpProfile, company: CompanyForScoring) -> str | None:
    expected = _normalize_region(icp.region)
    if not expected:
        return None
    actual_values = [company.region, company.city, company.address]
    actual_text = " ".join(value for value in actual_values if value).lower()
    if not actual_text:
        return None
    if expected.lower() in actual_text:
        return None
    return f"region mismatch: expected {icp.region}, got {company.region or company.city or company.address}"


def _normalize_region(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text or text.lower() in {"вся рф", "любой", "другой регион"}:
        return None
    return text


def _coerce_score(value: Any) -> int:
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        score = 0
    return max(0, min(100, score))


def _coerce_confidence(value: Any) -> str:
    return value if value in {"low", "medium", "high"} else "low"


def _coerce_action(value: Any) -> str:
    return value if value in {"add_to_results", "manual_review", "skip"} else "manual_review"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
