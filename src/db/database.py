"""SQLite 데이터베이스 초기화 및 연결 관리."""

from pathlib import Path

import aiosqlite

from src.config import settings

SCHEMA_SQL = """
-- 리서치 세션 관리
CREATE TABLE IF NOT EXISTS research_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL CHECK(session_type IN ('trend', 'speaker', 'feedback', 'daily_scan', 'planner')),
    input_query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK(status IN ('running', 'completed', 'failed')),
    result_summary TEXT,
    agent_session_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

-- 트렌드 키워드
CREATE TABLE IF NOT EXISTS trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT,
    description TEXT,
    evidence TEXT,
    source_conferences TEXT,
    relevance_score REAL,
    is_auto_discovered INTEGER DEFAULT 0,
    session_id INTEGER REFERENCES research_sessions(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 트랙 구성
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    target_audience TEXT,
    session_format TEXT DEFAULT 'keynote+panel',
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 트렌드-트랙 매핑
CREATE TABLE IF NOT EXISTS track_trends (
    track_id INTEGER REFERENCES tracks(id),
    trend_id INTEGER REFERENCES trends(id),
    PRIMARY KEY (track_id, trend_id)
);

-- 연사 후보
CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_ko TEXT,
    title TEXT,
    organization TEXT,
    country TEXT,
    bio TEXT,
    expertise TEXT,
    tier TEXT CHECK(tier IN ('tier1_keynote', 'tier3_track', 'unassigned')),
    overall_score REAL,
    expertise_score REAL,
    name_value_score REAL,
    speaking_score REAL,
    relevance_score REAL,
    linkedin_url TEXT,
    website_url TEXT,
    email TEXT,
    photo_url TEXT,
    speaking_history TEXT,
    publications TEXT,
    recommendation_reason TEXT,
    source_channel TEXT,
    is_auto_discovered INTEGER DEFAULT 0,
    status TEXT DEFAULT 'candidate'
        CHECK(status IN (
            'candidate', 'shortlisted', 'contacting',
            'confirmed', 'declined', 'rejected'
        )),
    track_id INTEGER REFERENCES tracks(id),
    session_id INTEGER REFERENCES research_sessions(id),
    team_notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 피드백 이력
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feedback_type TEXT NOT NULL
        CHECK(feedback_type IN ('direction', 'speaker', 'trend', 'track', 'general')),
    content TEXT NOT NULL,
    target_id INTEGER,
    target_type TEXT,
    action_taken TEXT,
    session_id INTEGER REFERENCES research_sessions(id),
    created_by TEXT DEFAULT 'team',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 팀에이전트 토론 기록
CREATE TABLE IF NOT EXISTS discussions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES research_sessions(id),
    agent_name TEXT NOT NULL,
    message_type TEXT NOT NULL
        CHECK(message_type IN ('proposal', 'critique', 'revision', 'consensus')),
    content TEXT NOT NULL,
    round_number INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 일일 자동 제안
CREATE TABLE IF NOT EXISTS daily_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_date TEXT NOT NULL,
    suggestion_type TEXT NOT NULL CHECK(suggestion_type IN ('trend', 'speaker')),
    title TEXT NOT NULL,
    summary TEXT,
    detail_json TEXT,
    source_urls TEXT,
    relevance_score REAL,
    status TEXT NOT NULL DEFAULT 'pending_review'
        CHECK(status IN ('pending_review', 'approved', 'dismissed')),
    linked_trend_id INTEGER REFERENCES trends(id),
    linked_speaker_id INTEGER REFERENCES speakers(id),
    session_id INTEGER REFERENCES research_sessions(id),
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Planner 과제
CREATE TABLE IF NOT EXISTS planner_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'medium',
    query TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    session_id INTEGER REFERENCES research_sessions(id),
    result_summary TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

-- 참조 컨퍼런스 데이터
CREATE TABLE IF NOT EXISTS reference_conferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    year INTEGER,
    url TEXT,
    program_url TEXT,
    speakers_data TEXT,
    topics_data TEXT,
    last_scraped_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_speakers_status ON speakers(status);
CREATE INDEX IF NOT EXISTS idx_speakers_tier ON speakers(tier);
CREATE INDEX IF NOT EXISTS idx_speakers_track ON speakers(track_id);
CREATE INDEX IF NOT EXISTS idx_speakers_score ON speakers(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_trends_category ON trends(category);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_target ON feedback(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_discussions_session ON discussions(session_id);
CREATE INDEX IF NOT EXISTS idx_suggestions_date ON daily_suggestions(suggestion_date);
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON daily_suggestions(status);
"""


async def init_db() -> None:
    """DB 파일 생성 및 스키마 초기화."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(SCHEMA_SQL)
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """DB 연결을 반환. FastAPI Depends에서 사용."""
    db = await aiosqlite.connect(str(settings.database_path))
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()
