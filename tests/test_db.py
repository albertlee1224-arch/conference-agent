"""DB 레이어 테스트."""

import os
import pytest
import aiosqlite

# 테스트용 DB 경로 설정
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DATABASE_PATH"] = ":memory:"

from src.db.database import SCHEMA_SQL
from src.db import queries


@pytest.fixture
async def db():
    """인메모리 DB 연결."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.executescript(SCHEMA_SQL)
    await conn.commit()
    yield conn
    await conn.close()


async def test_create_session(db):
    sid = await queries.create_session(db, "trend", "AI Agent trends")
    assert sid == 1
    session = await queries.get_session(db, sid)
    assert session["session_type"] == "trend"
    assert session["status"] == "running"


async def test_update_session_status(db):
    sid = await queries.create_session(db, "speaker", "find speakers")
    await queries.update_session_status(db, sid, "completed", "Found 5 speakers")
    session = await queries.get_session(db, sid)
    assert session["status"] == "completed"
    assert session["result_summary"] == "Found 5 speakers"
    assert session["completed_at"] is not None


async def test_insert_and_list_trends(db):
    tid = await queries.insert_trend(
        db, keyword="AI Agents", category="GenAI",
        description="자율 AI 에이전트", relevance_score=0.9,
    )
    assert tid == 1

    trends = await queries.list_trends(db)
    assert len(trends) == 1
    assert trends[0]["keyword"] == "AI Agents"

    # 카테고리 필터
    trends_filtered = await queries.list_trends(db, category="GenAI")
    assert len(trends_filtered) == 1

    trends_empty = await queries.list_trends(db, category="Other")
    assert len(trends_empty) == 0


async def test_insert_and_list_speakers(db):
    spid = await queries.insert_speaker(
        db, name="John Doe", organization="Google",
        overall_score=0.85, expertise_score=0.9,
        status="candidate", tier="tier1_keynote",
    )
    assert spid == 1

    speakers = await queries.list_speakers(db)
    assert len(speakers) == 1
    assert speakers[0]["name"] == "John Doe"

    # 필터
    speakers_tier1 = await queries.list_speakers(db, tier="tier1_keynote")
    assert len(speakers_tier1) == 1

    speakers_tier3 = await queries.list_speakers(db, tier="tier3_track")
    assert len(speakers_tier3) == 0


async def test_update_speaker(db):
    spid = await queries.insert_speaker(
        db, name="Jane Smith", organization="Meta", status="candidate",
    )
    await queries.update_speaker(db, spid, status="shortlisted")
    speaker = await queries.get_speaker(db, spid)
    assert speaker["status"] == "shortlisted"


async def test_delete_speaker(db):
    spid = await queries.insert_speaker(
        db, name="Delete Me", organization="Test",
    )
    deleted = await queries.delete_speaker(db, spid)
    assert deleted is True
    speaker = await queries.get_speaker(db, spid)
    assert speaker is None


async def test_insert_and_list_feedback(db):
    fid = await queries.insert_feedback(
        db, content="More healthcare speakers",
        feedback_type="speaker",
    )
    assert fid == 1

    feedback = await queries.list_feedback(db)
    assert len(feedback) == 1
    assert feedback[0]["content"] == "More healthcare speakers"


async def test_tracks_crud(db):
    # Create
    tid = await queries.insert_track(
        db, name="AI Infrastructure", description="AI 인프라 트랙",
    )
    assert tid == 1

    # List
    tracks = await queries.list_tracks(db)
    assert len(tracks) == 1

    # Update
    await queries.update_track(db, tid, name="AI Infra & MLOps")
    track = await queries.get_track(db, tid)
    assert track["name"] == "AI Infra & MLOps"

    # Track-Trend 매핑
    trend_id = await queries.insert_trend(db, keyword="MLOps", description="test")
    await queries.set_track_trends(db, tid, [trend_id])
    track_trends = await queries.get_track_trends(db, tid)
    assert len(track_trends) == 1
    assert track_trends[0]["keyword"] == "MLOps"


async def test_insert_and_list_suggestions(db):
    sid = await queries.create_session(db, "daily_scan", "auto scan")
    sug_id = await queries.insert_suggestion(
        db,
        suggestion_date="2026-03-01",
        suggestion_type="trend",
        title="AI Agents 2.0",
        summary="자율 에이전트 프레임워크가 급부상 중",
        relevance_score=0.85,
        session_id=sid,
    )
    assert sug_id == 1

    suggestions = await queries.list_suggestions(db, date="2026-03-01")
    assert len(suggestions) == 1
    assert suggestions[0]["title"] == "AI Agents 2.0"
    assert suggestions[0]["status"] == "pending_review"

    # 상태 업데이트
    await queries.update_suggestion_status(
        db, sug_id, "approved", reviewed_by="team"
    )
    updated = await queries.get_suggestion(db, sug_id)
    assert updated["status"] == "approved"
    assert updated["reviewed_by"] == "team"
    assert updated["reviewed_at"] is not None

    # 통계
    stats = await queries.get_suggestion_stats(db, date="2026-03-01")
    assert stats["total"] == 1
    assert stats["approved"] == 1
    assert stats["pending"] == 0


async def test_suggestion_filters(db):
    await queries.insert_suggestion(
        db, suggestion_date="2026-03-01", suggestion_type="trend",
        title="Trend A", relevance_score=0.9,
    )
    await queries.insert_suggestion(
        db, suggestion_date="2026-03-01", suggestion_type="speaker",
        title="Speaker B", relevance_score=0.7,
    )
    await queries.insert_suggestion(
        db, suggestion_date="2026-03-02", suggestion_type="trend",
        title="Trend C", relevance_score=0.6,
    )

    # 날짜 필터
    day1 = await queries.list_suggestions(db, date="2026-03-01")
    assert len(day1) == 2

    # 타입 필터
    trends_only = await queries.list_suggestions(
        db, date="2026-03-01", suggestion_type="trend"
    )
    assert len(trends_only) == 1
    assert trends_only[0]["title"] == "Trend A"


async def test_discussions(db):
    sid = await queries.create_session(db, "trend", "test")
    did = await queries.insert_discussion(
        db, session_id=sid, agent_name="ai-tech-expert",
        message_type="critique", content="This trend is too academic",
        round_number=1,
    )
    assert did == 1

    discussions = await queries.list_discussions(db, sid)
    assert len(discussions) == 1
    assert discussions[0]["agent_name"] == "ai-tech-expert"
    assert discussions[0]["message_type"] == "critique"
