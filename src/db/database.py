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

-- 아젠다 세션 (Session/Agenda Builder)
CREATE TABLE IF NOT EXISTS agenda_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    day INTEGER NOT NULL DEFAULT 1 CHECK(day IN (1, 2)),
    track_id INTEGER REFERENCES tracks(id),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    session_type TEXT NOT NULL DEFAULT 'presentation'
        CHECK(session_type IN ('keynote', 'panel', 'presentation', 'workshop', 'break', 'networking')),
    speaker_id INTEGER REFERENCES speakers(id),
    second_speaker_id INTEGER REFERENCES speakers(id),
    moderator_id INTEGER REFERENCES speakers(id),
    description TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK(status IN ('draft', 'tentative', 'confirmed', 'cancelled')),
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 마일스톤 (Timeline/Milestones)
CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'planning'
        CHECK(phase IN ('research', 'planning', 'outreach', 'confirmation', 'production', 'event')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending', 'in_progress', 'completed', 'overdue', 'skipped')),
    owner TEXT,
    sort_order INTEGER DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 예산 항목 (Budget Tracking)
CREATE TABLE IF NOT EXISTS budget_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL
        CHECK(category IN ('speaker_fee', 'travel', 'venue', 'catering', 'production', 'marketing', 'staff', 'other')),
    description TEXT NOT NULL,
    estimated_amount REAL NOT NULL DEFAULT 0,
    actual_amount REAL,
    currency TEXT NOT NULL DEFAULT 'KRW',
    speaker_id INTEGER REFERENCES speakers(id),
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'estimated'
        CHECK(status IN ('estimated', 'approved', 'paid', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 연사 연락 이력 (Communication Tracking)
CREATE TABLE IF NOT EXISTS speaker_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    speaker_id INTEGER NOT NULL REFERENCES speakers(id),
    contact_type TEXT NOT NULL
        CHECK(contact_type IN ('email', 'linkedin', 'phone', 'meeting', 'other')),
    direction TEXT NOT NULL DEFAULT 'outbound'
        CHECK(direction IN ('inbound', 'outbound')),
    subject TEXT,
    content TEXT,
    contacted_by TEXT,
    contact_date TEXT NOT NULL DEFAULT (datetime('now')),
    follow_up_date TEXT,
    status TEXT NOT NULL DEFAULT 'sent'
        CHECK(status IN ('draft', 'sent', 'replied', 'no_response', 'follow_up_needed')),
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
CREATE INDEX IF NOT EXISTS idx_agenda_day ON agenda_sessions(day);
CREATE INDEX IF NOT EXISTS idx_agenda_track ON agenda_sessions(track_id);
CREATE INDEX IF NOT EXISTS idx_milestones_phase ON milestones(phase);
CREATE INDEX IF NOT EXISTS idx_milestones_due ON milestones(due_date);
CREATE INDEX IF NOT EXISTS idx_budget_category ON budget_items(category);
CREATE INDEX IF NOT EXISTS idx_budget_speaker ON budget_items(speaker_id);
CREATE INDEX IF NOT EXISTS idx_contacts_speaker ON speaker_contacts(speaker_id);
CREATE INDEX IF NOT EXISTS idx_contacts_date ON speaker_contacts(contact_date);
"""

# speakers 테이블 마이그레이션용 ALTER 문
MIGRATION_SQL = [
    "ALTER TABLE speakers ADD COLUMN estimated_fee REAL",
    "ALTER TABLE speakers ADD COLUMN risk_level TEXT DEFAULT 'low' CHECK(risk_level IN ('low', 'medium', 'high'))",
    "ALTER TABLE speakers ADD COLUMN assigned_to TEXT",
    "ALTER TABLE speakers ADD COLUMN travel_required INTEGER DEFAULT 1",
    "ALTER TABLE speakers ADD COLUMN last_contacted_at TEXT",
]


async def init_db() -> None:
    """DB 파일 생성 및 스키마 초기화 + 마이그레이션."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(SCHEMA_SQL)
        # 기존 DB에 새 컬럼 추가 (이미 존재하면 무시)
        for alter_sql in MIGRATION_SQL:
            try:
                await db.execute(alter_sql)
            except Exception:
                pass  # 컬럼이 이미 존재하면 무시
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
