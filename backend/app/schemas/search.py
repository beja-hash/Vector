from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.schemas.project import ProjectCreate, ProjectRead


class SearchBase(BaseModel):
    industry: str | None = None
    okved: str | None = None
    region: str | None = None
    city: str | None = None
    revenue_min: int | None = Field(default=None, ge=0)
    revenue_max: int | None = Field(default=None, ge=0)
    employees_min: int | None = Field(default=None, ge=0)
    employees_max: int | None = Field(default=None, ge=0)
    company_age_min: int | None = Field(default=None, ge=0)
    active_only: bool = True
    business_type: str = "Любой"
    website_requirement: str = "any"
    vacancies_requirement: str = "any"
    vacancy_categories: list[str] = Field(default_factory=list)
    sales_department_requirement: str = "any"
    check_website: bool = False
    exclude_ip: bool = True
    exclude_liquidated: bool = True
    exclude_no_revenue: bool = False
    exclude_microbusiness: bool = False
    exclude_government: bool = False
    exclude_marketplace_sellers: bool = False
    requested_companies_count: int = Field(default=50, ge=1, le=5000)
    data_completeness: str = "partial_allowed"
    export_format: str = "CSV"

    @model_validator(mode="after")
    def validate_ranges(self) -> "SearchBase":
        if self.revenue_min is not None and self.revenue_max is not None and self.revenue_min > self.revenue_max:
            raise ValueError("revenue_min must be less than or equal to revenue_max")
        if self.employees_min is not None and self.employees_max is not None and self.employees_min > self.employees_max:
            raise ValueError("employees_min must be less than or equal to employees_max")
        return self


class SearchCreate(SearchBase):
    project_id: str | None = None
    project: ProjectCreate | None = None


class SearchRead(SearchBase):
    id: str
    project_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    requested_companies_count: int
    found_companies_count: int = 0
    project: ProjectRead | None = None

    model_config = {"from_attributes": True}
