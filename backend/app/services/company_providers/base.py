from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class CompanyCandidate:
    company_name: str
    inn: str
    ogrn: str
    region: str
    city: str
    okved_main: str
    okved_description: str
    revenue: int | None
    employees_count: int | None
    company_age: int
    website: str | None
    has_website: bool
    vacancies_total: int
    sales_vacancies: int
    marketing_vacancies: int
    business_type: str
    source_name: str
    source_url: str | None
    comment: str | None


class CompanyProvider(ABC):
    @abstractmethod
    def search_companies(self, filters) -> list[CompanyCandidate]:
        raise NotImplementedError
