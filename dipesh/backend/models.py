from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.sql import func
from database import Base

class Build(Base):
    __tablename__ = "builds"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), index=True)   # github, jenkins
    pipeline = Column(String(100), index=True)
    repo = Column(String(200), index=True)
    branch = Column(String(100), index=True)
    status = Column(String(20), index=True)     # success, failure, cancelled, in_progress
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    url = Column(String(500), nullable=True)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
