from datetime import datetime

from pydantic import BaseModel


class CompanyResultRead(BaseModel):
    id: str
    search_id: str
    company_name: str
    inn: str
    ogrn: str
    region: str | None = None
    city: str | None = None
    okved_main: str | None = None
    okved_description: str | None = None
    revenue: int | None = None
    employees_count: int | None = None
    company_age: int | None = None
    website: str | None = None
    has_website: bool
    vacancies_total: int
    sales_vacancies: int
    marketing_vacancies: int
    business_type: str
    source_name: str
    source_url: str | None = None
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
