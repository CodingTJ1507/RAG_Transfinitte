from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class SourceType(str, Enum):
    DOCUMENT = "document"
    WEBPAGE = "webpage"
    IMAGE = "image"
    TRANSCRIPT = "transcript"
    STRUCTURED_RECORD = "structured_record"

class Citation(BaseModel):
    source_id: str
    source_type: SourceType
    title: str
    location: str  # e.g., "Page 3", "Timestamp 10:14", "Line 42"
    snippet: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InvestigationRequest(BaseModel):
    query: str
    incident_id: Optional[str] = None
    source_types: Optional[List[SourceType]] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None

class TimelineEvent(BaseModel):
    timestamp: str
    event: str
    source_type: SourceType
    source_id: str
    severity: Optional[str] = "info"

class InvestigationReport(BaseModel):
    query: str
    timeline: List[TimelineEvent] = Field(default_factory=list)
    likely_root_cause: Optional[str] = None
    confidence_score: float = 0.0
    is_abstention: bool = False
    abstention_reason: Optional[str] = None
    supporting_evidence: List[Citation] = Field(default_factory=list)
    conflicting_evidence: List[Citation] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
