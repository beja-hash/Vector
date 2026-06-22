import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CompanyResult(Base):
    __tablename__ = "company_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_id = Column(String(36), ForeignKey("searches.id"), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    inn = Column(String(10), nullable=False, index=True)
    ogrn = Column(String(13), nullable=False)
    region = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    okved_main = Column(String(32), nullable=True)
    okved_description = Column(String(255), nullable=True)
    revenue = Column(Integer, nullable=True)
    employees_count = Column(Integer, nullable=True)
    company_age = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    has_website = Column(Boolean, nullable=False, default=False)
    vacancies_total = Column(Integer, nullable=False, default=0)
    sales_vacancies = Column(Integer, nullable=False, default=0)
    marketing_vacancies = Column(Integer, nullable=False, default=0)
    business_type = Column(String(32), nullable=False, default="B2B")
    source_name = Column(String(128), nullable=False, default="MockProvider")
    source_url = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    search = relationship("Search", back_populates="results")
