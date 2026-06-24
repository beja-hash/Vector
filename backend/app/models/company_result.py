import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CompanyResult(Base):
    __tablename__ = "company_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_id = Column(String(36), ForeignKey("searches.id"), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    full_company_name = Column(String(512), nullable=True)
    inn = Column(String(16), nullable=True, index=True)
    kpp = Column(String(16), nullable=True)
    ogrn = Column(String(20), nullable=True)
    status = Column(String(32), nullable=True)
    region = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    address = Column(Text, nullable=True)
    okved_main = Column(String(32), nullable=True)
    okved_description = Column(String(255), nullable=True)
    revenue = Column(Integer, nullable=True)
    revenue_raw = Column(String(128), nullable=True)
    employees_count = Column(Integer, nullable=True)
    registration_date = Column(String(10), nullable=True)
    company_age = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    summary_text = Column(Text, nullable=True)
    has_website = Column(Boolean, nullable=False, default=False)
    vacancies_total = Column(Integer, nullable=False, default=0)
    sales_vacancies = Column(Integer, nullable=False, default=0)
    marketing_vacancies = Column(Integer, nullable=False, default=0)
    business_type = Column(String(32), nullable=False, default="B2B")
    source_name = Column(String(128), nullable=False, default="MockProvider")
    source_url = Column(String(512), nullable=True)
    raw_snapshot_id = Column(String(36), ForeignKey("raw_company_snapshots.id"), nullable=True)
    icp_score = Column(Integer, nullable=True)
    icp_is_match = Column(Boolean, nullable=True)
    icp_confidence = Column(String(16), nullable=True)
    icp_fit_reason = Column(Text, nullable=True)
    icp_mismatch_reason = Column(Text, nullable=True)
    icp_matched_criteria = Column(JSON, nullable=True)
    icp_failed_criteria = Column(JSON, nullable=True)
    icp_recommended_action = Column(String(32), nullable=True)
    llm_model = Column(String(128), nullable=True)
    llm_scored_at = Column(DateTime, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    search = relationship("Search", back_populates="results")
    raw_snapshot = relationship("RawCompanySnapshot", back_populates="result")
