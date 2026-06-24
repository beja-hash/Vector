from dataclasses import dataclass, field

from app.services.company_providers.base import CompanyCandidate


@dataclass(slots=True)
class RusprofileSearchFilters:
    active_only: bool = True
    industry: str | None = None
    okved_code: str | None = None
    region: str | None = None
    revenue_min: int | None = None
    revenue_max: int | None = None
    employees_min: int | None = None
    employees_max: int | None = None
    limit: int = 50
    visible_browser: bool = True
    human_mode: bool = True


@dataclass(slots=True)
class RusprofileSearchItem:
    company_name: str | None
    source_url: str
    revenue_raw: str | None = None
    revenue_growth_raw: str | None = None
    activity_description: str | None = None
    address_raw: str | None = None
    inn: str | None = None
    ogrn: str | None = None
    registration_date_raw: str | None = None
    status_label: str | None = None
    raw_text: str | None = None


@dataclass(slots=True)
class RusprofileRawCompanySnapshot:
    source_name: str
    source_url: str | None
    raw_company_name: str | None = None
    raw_inn: str | None = None
    raw_ogrn: str | None = None
    raw_summary_text: str | None = None
    raw_page_text: str | None = None
    raw_payload: dict = field(default_factory=dict)
    status: str = "collected"
    error_message: str | None = None


@dataclass(slots=True)
class RusprofileParsedCompany:
    candidate: CompanyCandidate


@dataclass(slots=True)
class RusprofileRunResult:
    raw_snapshots: list[RusprofileRawCompanySnapshot] = field(default_factory=list)
    parsed_companies: list[RusprofileParsedCompany] = field(default_factory=list)
    collected: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
