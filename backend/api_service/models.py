"""Validated public complaint and session contracts."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Identity(StrictModel):
    system_version: Literal['v1', 'v2']
    order_id: int = Field(gt=0)


class ComplaintRequest(StrictModel):
    email_text: str = Field(min_length=1, max_length=20000)
    session_id: str | None = None

    @field_validator('email_text')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('blank')
        return value


class MessageRequest(StrictModel):
    message: str | None = Field(default=None, max_length=10000)
    selected_candidate: Identity | None = None

    @model_validator(mode='after')
    def require_content(self):
        if self.message is not None and not self.message.strip():
            raise ValueError('blank')
        if self.message is None and self.selected_candidate is None:
            raise ValueError('missing content')
        return self


class Error(BaseModel):
    code: str
    message: str
    retryable: bool


class Citation(BaseModel):
    n: int
    source_id: str
    type: Literal['sql', 'tabular', 'image', 'document', 'log']
    ref: str
    locator: str
    record_key: dict | None = None
    label: str | None = None


class Candidate(Identity):
    created: str
    status: str | None = None
    zone: str | None = None
    postal_code: str | None = None
    evidence_for: str
    citations: list[int]


class Complaint(BaseModel):
    category: str | None = None
    claims: list[str] = Field(default_factory=list)
    citations: list[int] = Field(default_factory=list)


class Order(Identity):
    customer: str | None = None
    postal_code: str | None = None
    zone: str | None = None
    driver_code: str | None = None
    promised_date: str | None = None
    citations: list[int] = Field(default_factory=list)


class Clarification(BaseModel):
    question: str
    hint: str | None = None


class Evidence(BaseModel):
    key: str
    title: str
    status: Literal['found', 'ambiguous', 'not_found', 'partial', 'failed']
    summary: str
    facts: list[tuple[str, str]] = Field(default_factory=list)
    citations: list[int] = Field(default_factory=list)
    gps: list[dict] | None = None
    deliveredAt: str | None = None
    note: str | None = None


class ConflictValue(BaseModel):
    value: str
    source: str
    citation: int


class Conflict(BaseModel):
    field: str
    values: list[ConflictValue]
    note: str


class Recommendation(BaseModel):
    action: Literal['Refund', 'Re-deliver', 'Reject', 'Apology only', 'Compensate']
    amount_sgd: float | None = None
    summary: str
    rationale: str
    approval_required: bool
    approver: str | None = None
    citations: list[int]


class Reason(BaseModel):
    reason: str


class Guardrail(BaseModel):
    code: str
    pii_masked: list[str]


class Message(BaseModel):
    role: Literal['user', 'assistant']
    text: str


class WeeklyPeriod(BaseModel):
    week_start: str
    week_end: str
    timezone: str


class ZoneCategoryRow(BaseModel):
    zone: str
    values: list[int]


class ZoneCategory(BaseModel):
    zones: list[str]
    categories: list[str]
    rows: list[ZoneCategoryRow]


class TrendPoint(BaseModel):
    week_start: str
    total: int
    by_zone: dict[str, int]


class WeeklyResult(BaseModel):
    """Contract per frontend contract §3 and catalog §3.4; nullable metrics stay null."""
    period: WeeklyPeriod
    definitions: list[list[str]]
    totals: dict[str, int | float | None]
    by_zone: list[dict[str, object]]
    by_driver: list[dict[str, object]]
    by_category: list[dict[str, object]]
    by_resolution: list[dict[str, object]]
    zone_category: ZoneCategory
    trend: list[TrendPoint]
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


class ComplaintResult(BaseModel):
    request_id: str
    session_id: str | None
    status: Literal['found', 'ambiguous', 'partial', 'not_found', 'refused', 'failed']
    complaint: Complaint = Field(default_factory=Complaint)
    order: Order | None = None
    candidates: list[Candidate] = Field(default_factory=list)
    clarification: Clarification | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    recommendation: Recommendation | None = None
    abstention: Reason | None = None
    guardrail: Guardrail | None = None
    follow_up_answer: str | None = None
    limitations: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    error: Error | None = None
    recovered: bool = False
    messages: list[Message] | None = None

    @model_validator(mode='after')
    def references_exist(self):
        numbers = [citation.n for citation in self.citations]
        if any(n <= 0 for n in numbers) or len(set(numbers)) != len(numbers):
            raise ValueError('invalid citation numbers')
        refs = list(self.complaint.citations)
        for item in [self.order, self.recommendation, *self.candidates, *self.evidence]:
            if item is not None:
                refs.extend(item.citations)
        refs.extend(value.citation for conflict in self.conflicts for value in conflict.values)
        if not set(refs).issubset(numbers):
            raise ValueError('dangling citation')
        if self.status == 'failed' and self.error is None:
            raise ValueError('failed result requires error')
        if self.status in ('ambiguous', 'refused', 'not_found', 'failed') and self.recommendation is not None:
            raise ValueError('unsupported recommendation')
        return self
