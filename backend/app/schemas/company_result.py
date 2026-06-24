from datetime import datetime

from pydantic import BaseModel


class CompanyResultRead(BaseModel):
    id: str
    search_id: str
    company_name: str
    full_company_name: str | None = None
    inn: str | None = None
    kpp: str | None = None
    ogrn: str | None = None
    status: str | None = None
    region: str | None = None
    city: str | None = None
    address: str | None = None
    okved_main: str | None = None
    okved_description: str | None = None
    revenue: int | None = None
    revenue_raw: str | None = None
    employees_count: int | None = None
    registration_date: str | None = None
    company_age: int | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    summary_text: str | None = None
    has_website: bool
    vacancies_total: int
    sales_vacancies: int
    marketing_vacancies: int
    business_type: str
    source_name: str
    source_url: str | None = None
    raw_snapshot_id: str | None = None
    icp_score: int | None = None
    icp_is_match: bool | None = None
    icp_confidence: str | None = None
    icp_fit_reason: str | None = None
    icp_mismatch_reason: str | None = None
    icp_matched_criteria: list[str] | None = None
    icp_failed_criteria: list[str] | None = None
    icp_recommended_action: str | None = None
    llm_model: str | None = None
    llm_scored_at: datetime | None = None
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
