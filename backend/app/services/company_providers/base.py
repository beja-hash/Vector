from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class CompanyCandidate:
    company_name: str
    inn: str | None
    ogrn: str | None
    region: str | None
    city: str | None
    okved_main: str | None
    okved_description: str | None
    revenue: int | None
    employees_count: int | None
    company_age: int | None
    website: str | None
    has_website: bool
    vacancies_total: int
    sales_vacancies: int
    marketing_vacancies: int
    business_type: str
    source_name: str
    source_url: str | None
    comment: str | None
    full_company_name: str | None = None
    kpp: str | None = None
    status: str | None = None
    address: str | None = None
    revenue_raw: str | None = None
    registration_date: str | None = None
    phone: str | None = None
    email: str | None = None
    summary_text: str | None = None
    raw_snapshot_id: str | None = None


class CompanyProvider(ABC):
    @abstractmethod
    def search_companies(self, filters) -> list[CompanyCandidate]:
        raise NotImplementedError
