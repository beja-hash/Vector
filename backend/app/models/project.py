import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    client_offer = Column(Text, nullable=False)
    average_deal_size = Column(Integer, nullable=True)
    sales_type = Column(String(32), nullable=False, default="B2B")
    usual_customers = Column(Text, nullable=True)
    excluded_customers = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    searches = relationship("Search", back_populates="project", cascade="all, delete-orphan")
