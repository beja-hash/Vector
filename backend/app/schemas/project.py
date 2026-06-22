from datetime import datetime

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    client_offer: str = Field(..., min_length=1)
    average_deal_size: int | None = Field(default=None, ge=0)
    sales_type: str = "B2B"
    usual_customers: str | None = None
    excluded_customers: str | None = None
    comment: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    search_count: int = 0
    companies_count: int = 0
    status: str = "active"

    model_config = {"from_attributes": True}
