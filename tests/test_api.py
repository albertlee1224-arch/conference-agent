"""API 엔드포인트 테스트."""

import os
import pytest
from httpx import AsyncClient, ASGITransport

# 테스트용 설정
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DATABASE_PATH"] = "data/test_conference.db"

from src.main import app
from src.db.database import init_db


@pytest.fixture
async def client():
    """테스트용 HTTP 클라이언트. DB를 수동 초기화."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    # 테스트 DB 정리
    import os as _os
    try:
        _os.remove("data/test_conference.db")
    except FileNotFoundError:
        pass


async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


async def test_speakers_crud(client: AsyncClient):
    # Create
    r = await client.post("/api/speakers", json={
        "name": "Test Speaker",
        "organization": "Test Corp",
    })
    assert r.status_code == 201
    speaker_id = r.json()["id"]

    # Read
    r = await client.get(f"/api/speakers/{speaker_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Speaker"

    # Update
    r = await client.patch(f"/api/speakers/{speaker_id}", json={
        "status": "shortlisted",
    })
    assert r.status_code == 200
    assert r.json()["status"] == "shortlisted"

    # List
    r = await client.get("/api/speakers")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # Delete
    r = await client.delete(f"/api/speakers/{speaker_id}")
    assert r.status_code == 200

    # 404
    r = await client.get(f"/api/speakers/{speaker_id}")
    assert r.status_code == 404


async def test_trends_list(client: AsyncClient):
    r = await client.get("/api/trends")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_tracks_crud(client: AsyncClient):
    # Create
    r = await client.post("/api/tracks", json={
        "name": "AI Infrastructure",
        "description": "AI 인프라 트랙",
    })
    assert r.status_code == 201
    track_id = r.json()["id"]

    # List
    r = await client.get("/api/tracks")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # Update
    r = await client.patch(f"/api/tracks/{track_id}", json={
        "name": "AI Infra & MLOps",
    })
    assert r.status_code == 200
    assert r.json()["name"] == "AI Infra & MLOps"


async def test_feedback_flow(client: AsyncClient):
    # Create feedback
    r = await client.post("/api/feedback", json={
        "content": "Need more healthcare speakers",
        "feedback_type": "speaker",
    })
    assert r.status_code == 201
    assert "id" in r.json()

    # List feedback
    r = await client.get("/api/feedback/history")
    assert r.status_code == 200
    assert len(r.json()) >= 1


async def test_suggestions_flow(client: AsyncClient):
    # 제안 목록 (빈 상태)
    r = await client.get("/api/suggestions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # 통계
    r = await client.get("/api/suggestions/stats")
    assert r.status_code == 200
    assert r.json()["total"] == 0

    # 수동 스캔 트리거 (에이전트는 테스트에서 실행 안 됨)
    r = await client.post("/api/suggestions/scan")
    assert r.status_code == 200
    assert "session_id" in r.json()


async def test_planner_tasks_empty(client: AsyncClient):
    r = await client.get("/api/planner/tasks")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 0


async def test_planner_evaluate_trigger(client: AsyncClient):
    r = await client.post("/api/planner/evaluate")
    assert r.status_code == 200
    assert "session_id" in r.json()
    assert r.json()["status"] == "running"


async def test_research_sessions(client: AsyncClient):
    # Start trend research (agent won't run in test)
    r = await client.post("/api/research/trends", json={
        "query": "AI Agent trends",
    })
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # Get session
    r = await client.get(f"/api/research/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["session_type"] == "trend"

    # List sessions
    r = await client.get("/api/research/sessions")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # Get discussions (empty)
    r = await client.get(f"/api/research/sessions/{session_id}/discussions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
