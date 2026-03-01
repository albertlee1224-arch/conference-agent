"""Pydantic 모델 — API 스키마 및 데이터 검증."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# === Research Sessions ===


class ResearchSessionCreate(BaseModel):
    session_type: str = Field(pattern=r"^(trend|speaker|feedback|daily_scan)$")
    input_query: str


class ResearchSession(BaseModel):
    id: int
    session_type: str
    input_query: str
    status: str
    result_summary: str | None = None
    agent_session_id: str | None = None
    created_at: str
    completed_at: str | None = None


# === Trends ===


class TrendCreate(BaseModel):
    keyword: str
    category: str | None = None
    description: str | None = None
    evidence: str | None = None  # JSON 문자열
    source_conferences: str | None = None  # JSON 문자열
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    session_id: int | None = None


class Trend(TrendCreate):
    id: int
    created_at: str
    updated_at: str


# === Tracks ===


class TrackCreate(BaseModel):
    name: str
    description: str | None = None
    target_audience: str | None = None
    session_format: str = "keynote+panel"
    sort_order: int = 0


class TrackUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_audience: str | None = None
    session_format: str | None = None
    sort_order: int | None = None
    trend_ids: list[int] | None = None


class Track(TrackCreate):
    id: int
    created_at: str
    updated_at: str


# === Speakers ===


class SpeakerCreate(BaseModel):
    name: str
    name_ko: str | None = None
    title: str | None = None
    organization: str | None = None
    country: str | None = None
    bio: str | None = None
    expertise: str | None = None  # JSON 문자열
    tier: str | None = Field(None, pattern=r"^(tier1_keynote|tier3_track|unassigned)$")
    overall_score: float | None = Field(None, ge=0.0, le=1.0)
    expertise_score: float | None = Field(None, ge=0.0, le=1.0)
    name_value_score: float | None = Field(None, ge=0.0, le=1.0)
    speaking_score: float | None = Field(None, ge=0.0, le=1.0)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    linkedin_url: str | None = None
    website_url: str | None = None
    email: str | None = None
    photo_url: str | None = None
    speaking_history: str | None = None  # JSON 문자열
    publications: str | None = None  # JSON 문자열
    recommendation_reason: str | None = None
    source_channel: str | None = None
    status: str = "candidate"
    track_id: int | None = None
    session_id: int | None = None
    team_notes: str | None = None


class SpeakerUpdate(BaseModel):
    status: str | None = Field(
        None,
        pattern=r"^(candidate|shortlisted|contacting|confirmed|declined|rejected)$",
    )
    tier: str | None = Field(None, pattern=r"^(tier1_keynote|tier3_track|unassigned)$")
    track_id: int | None = None
    team_notes: str | None = None
    overall_score: float | None = Field(None, ge=0.0, le=1.0)
    estimated_fee: float | None = None
    risk_level: str | None = Field(None, pattern=r"^(low|medium|high)$")
    assigned_to: str | None = None
    travel_required: int | None = None
    last_contacted_at: str | None = None


class Speaker(SpeakerCreate):
    id: int
    created_at: str
    updated_at: str


# === Feedback ===


class FeedbackCreate(BaseModel):
    content: str
    feedback_type: str = Field(
        pattern=r"^(direction|speaker|trend|track|general)$"
    )
    target_id: int | None = None
    target_type: str | None = None


class Feedback(FeedbackCreate):
    id: int
    action_taken: str | None = None
    session_id: int | None = None
    created_by: str = "team"
    created_at: str


# === Discussions (팀에이전트 토론 기록) ===


class DiscussionCreate(BaseModel):
    session_id: int
    agent_name: str
    message_type: str = Field(
        pattern=r"^(proposal|critique|revision|consensus)$"
    )
    content: str
    round_number: int = 1


class Discussion(DiscussionCreate):
    id: int
    created_at: str


# === Daily Suggestions (일일 자동 제안) ===


class DailySuggestionCreate(BaseModel):
    suggestion_type: str = Field(pattern=r"^(trend|speaker)$")
    title: str
    summary: str | None = None
    detail_json: str | None = None
    source_urls: str | None = None
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)


class DailySuggestionUpdate(BaseModel):
    status: str = Field(pattern=r"^(approved|dismissed)$")
    reviewed_by: str | None = None


class DailySuggestion(DailySuggestionCreate):
    id: int
    suggestion_date: str
    status: str
    linked_trend_id: int | None = None
    linked_speaker_id: int | None = None
    session_id: int | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    created_at: str


# === Agenda Sessions (세션/아젠다) ===


class AgendaSessionCreate(BaseModel):
    title: str
    day: int = Field(default=1, ge=1, le=2)
    track_id: int | None = None
    start_time: str  # "09:00"
    end_time: str    # "09:45"
    session_type: str = Field(
        default="presentation",
        pattern=r"^(keynote|panel|presentation|workshop|break|networking)$",
    )
    speaker_id: int | None = None
    second_speaker_id: int | None = None
    moderator_id: int | None = None
    description: str | None = None
    notes: str | None = None
    status: str = "draft"
    sort_order: int = 0


class AgendaSessionUpdate(BaseModel):
    title: str | None = None
    day: int | None = Field(None, ge=1, le=2)
    track_id: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    session_type: str | None = None
    speaker_id: int | None = None
    second_speaker_id: int | None = None
    moderator_id: int | None = None
    description: str | None = None
    notes: str | None = None
    status: str | None = Field(
        None, pattern=r"^(draft|tentative|confirmed|cancelled)$"
    )


# === Milestones (타임라인) ===


class MilestoneCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: str
    phase: str = Field(
        default="planning",
        pattern=r"^(research|planning|outreach|confirmation|production|event)$",
    )
    status: str = "pending"
    owner: str | None = None
    sort_order: int = 0


class MilestoneUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: str | None = None
    phase: str | None = None
    status: str | None = Field(
        None, pattern=r"^(pending|in_progress|completed|overdue|skipped)$"
    )
    owner: str | None = None
    completed_at: str | None = None


# === Budget Items (예산) ===


class BudgetItemCreate(BaseModel):
    category: str = Field(
        pattern=r"^(speaker_fee|travel|venue|catering|production|marketing|staff|other)$"
    )
    description: str
    estimated_amount: float = 0
    actual_amount: float | None = None
    currency: str = "KRW"
    speaker_id: int | None = None
    notes: str | None = None
    status: str = "estimated"


class BudgetItemUpdate(BaseModel):
    category: str | None = None
    description: str | None = None
    estimated_amount: float | None = None
    actual_amount: float | None = None
    notes: str | None = None
    status: str | None = Field(
        None, pattern=r"^(estimated|approved|paid|cancelled)$"
    )


# === Speaker Contacts (연락 이력) ===


class SpeakerContactCreate(BaseModel):
    speaker_id: int
    contact_type: str = Field(
        pattern=r"^(email|linkedin|phone|meeting|other)$"
    )
    direction: str = "outbound"
    subject: str | None = None
    content: str | None = None
    contacted_by: str | None = None
    contact_date: str | None = None
    follow_up_date: str | None = None
    status: str = "sent"


class SpeakerContactUpdate(BaseModel):
    status: str | None = Field(
        None,
        pattern=r"^(draft|sent|replied|no_response|follow_up_needed)$",
    )
    content: str | None = None
    follow_up_date: str | None = None
    contacted_by: str | None = None
