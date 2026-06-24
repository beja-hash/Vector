from typing import Literal

from pydantic import BaseModel, Field


class CompanyForScoring(BaseModel):
    company_name: str | None = None
    full_company_name: str | None = None
    inn: str | None = None
    ogrn: str | None = None
    region: str | None = None
    city: str | None = None
    address: str | None = None
    okved_main: str | None = None
    okved_description: str | None = None
    revenue: int | None = None
    revenue_raw: str | None = None
    employees_count: int | None = None
    website: str | None = None
    business_type: str | None = None
    activity_description: str | None = None
    summary_text: str | None = None


class IcpProfile(BaseModel):
    project_name: str | None = None
    offer: str | None = None
    average_check: int | None = None
    business_type: str | None = None
    industry: str | None = None
    okved_code: str | None = None
    region: str | None = None
    city: str | None = None
    revenue_min: int | None = None
    revenue_max: int | None = None
    employees_min: int | None = None
    employees_max: int | None = None
    company_age_min: int | None = None
    must_have_website: bool | None = None
    must_have_vacancies: bool | None = None
    good_signals: list[str] = Field(default_factory=list)
    bad_signals: list[str] = Field(default_factory=list)
    exclude_rules: list[str] = Field(default_factory=list)


class IcpScoreResult(BaseModel):
    is_match: bool
    score: int = Field(ge=0, le=100)
    confidence: Literal["low", "medium", "high"]
    fit_reason: str | None = None
    mismatch_reason: str | None = None
    matched_criteria: list[str] = Field(default_factory=list)
    failed_criteria: list[str] = Field(default_factory=list)
    recommended_action: Literal["add_to_results", "manual_review", "skip"]
