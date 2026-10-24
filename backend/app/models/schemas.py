from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    DOCUMENT = "document"
    WEBPAGE = "webpage"
    IMAGE = "image"
    TRANSCRIPT = "transcript"
    STRUCTURED_RECORD = "structured_record"


class Citation(BaseModel):
    source_id: str
    chunk_id: str | None = None
    source_type: SourceType
    title: str
    location: str
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    retrieval_score: float | None = None


class InvestigationRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    incident_id: str | None = None
    owner: str | None = None
    source_types: list[SourceType] | None = None
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    version: str | None = None

    @field_validator("time_range_start", "time_range_end")
    @classmethod
    def require_timezone_for_time_filters(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("Time filters must include a timezone, preferably UTC")
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "InvestigationRequest":
        if self.time_range_start and self.time_range_end and self.time_range_start > self.time_range_end:
            raise ValueError("time_range_start must be earlier than or equal to time_range_end")
        return self


class TimelineEvent(BaseModel):
    timestamp: str
    event: str
    source_type: SourceType
    source_id: str
    chunk_id: str
    classification: str = "observed"


class SupportedClaim(BaseModel):
    claim: str
    classification: str = Field(pattern="^(confirmed|inference|unknown)$")
    citation_chunk_ids: list[str] = Field(default_factory=list)
    explanation: str | None = None
    verification_status: str = Field(
        default="not_checked",
        pattern="^(verified|contradicted|insufficient|not_checked)$",
    )


class InvestigationReport(BaseModel):
    query: str
    answer: str = ""
    timeline: list[TimelineEvent] = Field(default_factory=list)
    claims: list[SupportedClaim] = Field(default_factory=list)
    likely_root_cause: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_explanation: str | None = None
    is_abstention: bool = False
    abstention_reason: str | None = None
    supporting_evidence: list[Citation] = Field(default_factory=list)
    conflicting_evidence: list[Citation] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    retrieval_diagnostics: dict[str, Any] = Field(default_factory=dict)


class IngestionFailure(BaseModel):
    source_id: str
    error: str


class IngestionReport(BaseModel):
    run_id: str
    status: str
    discovered_sources: int
    processed_sources: int
    created_sources: int
    updated_sources: int
    skipped_sources: int
    failed_sources: list[IngestionFailure] = Field(default_factory=list)
    chunks_created: int = 0
    structured_records_processed: int = 0


class EvaluationCaseResult(BaseModel):
    question_id: str
    category: str
    expected_source_ids: list[str]
    retrieved_source_ids: list[str]
    recall_at_k: float
    precision_at_k: float
    ndcg_at_k: float
    reciprocal_rank: float
    hit: bool
    abstention_expected: bool
    abstained: bool | None = None
    citations_valid: bool | None = None
    faithfulness: float | None = None
    answer_evaluated: bool = False
    passed: bool
    failure_reasons: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    status: str
    cases_run: int
    aggregate: dict[str, float]
    results: list[EvaluationCaseResult]
