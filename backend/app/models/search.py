import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Search(Base):
    __tablename__ = "searches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)

    industry = Column(String(128), nullable=True)
    okved = Column(String(32), nullable=True)
    region = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    revenue_min = Column(Integer, nullable=True)
    revenue_max = Column(Integer, nullable=True)
    employees_min = Column(Integer, nullable=True)
    employees_max = Column(Integer, nullable=True)
    company_age_min = Column(Integer, nullable=True)
    active_only = Column(Boolean, nullable=False, default=True)
    business_type = Column(String(32), nullable=False, default="Любой")

    website_requirement = Column(String(32), nullable=False, default="any")
    vacancies_requirement = Column(String(32), nullable=False, default="any")
    vacancy_categories = Column(JSON, nullable=False, default=list)
    sales_department_requirement = Column(String(32), nullable=False, default="any")
    check_website = Column(Boolean, nullable=False, default=False)

    exclude_ip = Column(Boolean, nullable=False, default=True)
    exclude_liquidated = Column(Boolean, nullable=False, default=True)
    exclude_no_revenue = Column(Boolean, nullable=False, default=False)
    exclude_microbusiness = Column(Boolean, nullable=False, default=False)
    exclude_government = Column(Boolean, nullable=False, default=False)
    exclude_marketplace_sellers = Column(Boolean, nullable=False, default=False)

    requested_companies_count = Column(Integer, nullable=False, default=50)
    data_completeness = Column(String(64), nullable=False, default="partial_allowed")
    export_format = Column(String(16), nullable=False, default="CSV")
    data_source = Column(String(32), nullable=False, default="mock")
    visible_browser = Column(Boolean, nullable=False, default=True)
    human_mode = Column(Boolean, nullable=False, default=True)
    llm_scoring_enabled = Column(Boolean, nullable=False, default=True)
    llm_scoring_threshold = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="searches")
    results = relationship("CompanyResult", back_populates="search", cascade="all, delete-orphan")
    raw_snapshots = relationship("RawCompanySnapshot", back_populates="search", cascade="all, delete-orphan")
