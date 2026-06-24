import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class RawCompanySnapshot(Base):
    __tablename__ = "raw_company_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_id = Column(String(36), ForeignKey("searches.id"), nullable=False, index=True)
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(512), nullable=True)
    raw_company_name = Column(String(512), nullable=True)
    raw_inn = Column(String(16), nullable=True, index=True)
    raw_ogrn = Column(String(20), nullable=True)
    raw_summary_text = Column(Text, nullable=True)
    raw_page_text = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="collected")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    search = relationship("Search", back_populates="raw_snapshots")
    result = relationship("CompanyResult", back_populates="raw_snapshot", uselist=False)
