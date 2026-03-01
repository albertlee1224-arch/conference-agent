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
