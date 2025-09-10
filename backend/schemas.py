from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class IngestBase(BaseModel):
    pipeline: str
    repo: str
    branch: str
    status: str = Field(pattern="^(success|failure|cancelled|in_progress)$")
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    url: Optional[str] = None
    logs: Optional[str] = None

class IngestRequest(IngestBase):
    pass

class BuildOut(BaseModel):
    id: int
    provider: str
    pipeline: str
    repo: str
    branch: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    url: Optional[str]

    class Config:
        from_attributes = True

class SummaryOut(BaseModel):
    window: str
    success_rate: float
    failure_rate: float
    avg_build_time: Optional[float]
    last_status_by_pipeline: Dict[str, str]
