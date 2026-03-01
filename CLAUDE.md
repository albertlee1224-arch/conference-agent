# 컨퍼런스 기획 에이전트 — 프로젝트 컨텍스트

> AI SUMMIT AND EXPO 2026 기획을 위한 AI 에이전트 웹 애플리케이션.
> 4명의 기획팀이 리서치/아젠다/연사 정보를 공유하고, 피드백을 반영하면서 점진적으로 기획안을 완성해가는 협업 도구.

---

## 행사 프로필: AI SUMMIT AND EXPO 2026

| 항목 | 내용 |
|------|------|
| 행사명 | AI SUMMIT AND EXPO 2026 |
| 일시 | 2026년 8월, 양일간 |
| 컨퍼런스 | 코엑스 그랜드볼룸, 2,000명 |
| EXPO | 코엑스 B홀, 부스 200개 |
| 티켓 | 컨퍼런스 ~100만원 / EXPO 1~2만원 |
| 참석자 | 대기업·중견기업 중심 |
| 트랙 | 4개, 매년 트렌드에 따라 재구성 |
| 세션 형식 | 키노트 + 패널 중심 |

---

## 도메인 지식

### 연사 티어링 기준
- **Tier 1 (오전 키노트)**: 전문성 + 네임밸류 최우선. 업계를 대표하는 인물
- **Tier 3 (오후 트랙)**: 실무 성과/사례 중심. AI를 실제 적용해서 성과를 낸 사람

### 연사 소싱 전략
- **초청 중심** — 기획팀이 직접 발굴/섭외
- **해외 컨퍼런스** — NeurIPS, ICML, Google I/O, CES, Web Summit 등의 연사 목록 분석
- **LinkedIn** — 프로필 탐색으로 신규 후보 발굴
- **기존 네트워크** — 이전 행사 연사 풀 활용
- **스노우볼링** — 연사가 다른 연사를 소개하는 관계망
- **연사 신청** — 외부에서 자발적으로 지원
- **스폰서/파트너** — 유료 세션 연사 지정

### 핵심 병목
1. **해외 연사 리서치** — 국내는 네트워크로 찾지만, 해외는 후보 풀이 좁고 적합성 판단이 어려움
2. **트렌드/주제 리서치** — 매년 재구성되는 트랙에 맞는 최신 트렌드 파악

### 의사결정 구조
- **핵심**: 대표 + 기획팀 내부 결정
- **자문**: Advisory Board (외부 전문가) — 테마/연사 추천
- **제약**: 스폰서 요구사항 — 세션 배정/연사 지정에 영향

### 기획 프로세스의 암묵지
> 기획자의 머릿속에 있는 판단 기준(연사 적합성, 트랙 구성 논리, 청중 선호도 등)이
> 명시적으로 문서화되지 않은 채 경험으로만 전달됨.
> 이 암묵지를 체계적으로 추출하고 에이전트에 반영하는 것이 프로젝트의 핵심 도전.

---

## 사용자

| 역할 | 인원 | 주요 활동 |
|------|------|-----------|
| 대표 | 1명 | 최종 의사결정, 방향 설정 |
| 기획팀장 (알벗) | 1명 | 기획 총괄, 연사 리서치 |
| 기획자 | 2명 | 리서치 보조, 섭외, 운영 |

- 기존 도구: Google Workspace (Docs, Sheets, Slides)
- 이전 행사 데이터: 구글 드라이브에 저장, 활용 가능

---

## 기술 스택

- **언어**: Python 3.11+
- **에이전트 프레임워크**: Anthropic Python SDK (`anthropic>=0.40.0`) — 직접 API 호출 + 자체 agentic loop
- **LLM**: Claude API (Anthropic) — 모델: claude-sonnet-4-20250514
- **백엔드**: FastAPI + uvicorn
- **프론트엔드**: Streamlit 대시보드 (5탭)
- **DB**: SQLite (aiosqlite) — WAL 모드
- **검색/리서치**: Anthropic 내장 web_search_20250305 도구
- **배포**: Render (백엔드) + Streamlit Community Cloud (프론트)
- **패키지 관리**: pip + pyproject.toml

### 팀에이전트 아키텍처
- **Orchestrator**: 순차 에이전트 호출로 토론 진행 + 합의 도출
- **기능 에이전트**: Trend Researcher, Speaker Researcher (run_agent() 호출)
- **페르소나 에이전트** (토론 패널 — 순차 평가):
  1. AI 기술 전문가 — 기술적 타당성/최신성
  2. 대기업 참가자 — 비즈니스 가치/ROI
  3. 오퍼레이션 담당자 — 섭외 현실성/비용
  4. 일반 참가자 — 흥미도/접근성
- **Planner Director**: 데이터 품질 평가 + 자동 개선 과제 생성 (메타 에이전트)

---

## 폴더 구조

```
conference-agent/
├── CLAUDE.md              # 이 파일 — 프로젝트 컨텍스트
├── .env.example           # 환경변수 템플릿
├── pyproject.toml         # 의존성 관리
├── src/
│   ├── main.py            # FastAPI 앱 진입점
│   ├── config.py          # 환경변수/설정 관리
│   ├── agents/            # 에이전트 정의
│   │   ├── agent_loop.py      # Anthropic SDK agentic loop (핵심)
│   │   ├── tool_defs.py       # 도구 정의 + 핸들러 레지스트리
│   │   ├── orchestrator.py    # 팀 토론 조율, 순차 에이전트 호출
│   │   ├── trend_researcher.py
│   │   ├── speaker_researcher.py
│   │   └── personas.py        # 4개 페르소나 에이전트
│   ├── tools/             # DB/스코어링 핸들러
│   │   ├── db_tools.py        # DB CRUD 핸들러 (str 반환)
│   │   └── scoring_tools.py   # 연사 스코어링 (str 반환)
│   ├── prompts/           # 프롬프트 템플릿 (7종, planner_director.py 포함)
│   ├── db/                # DB 레이어
│   │   ├── database.py        # SQLite 초기화, 스키마
│   │   ├── models.py          # Pydantic 모델
│   │   └── queries.py         # SQL 쿼리 (파라미터 바인딩)
│   ├── api/               # FastAPI 라우터
│   │   ├── research.py        # 리서치 실행 (BackgroundTask)
│   │   ├── speakers.py        # 연사 CRUD
│   │   ├── trends.py          # 트렌드 조회
│   │   ├── tracks.py          # 트랙 CRUD
│   │   ├── feedback.py        # 피드백 입력/처리
│   │   └── planner.py         # Planner Director API
│   └── web/
│       └── app.py             # Streamlit 대시보드
├── data/
│   └── seed/                  # 시드 데이터
├── docs/
│   └── PRD.md
└── tests/
    ├── test_db.py             # DB 레이어 테스트 (9개)
    └── test_api.py            # API 엔드포인트 테스트 (6개)
```

---

## 코딩 컨벤션

- Python 스타일: PEP 8 준수
- Type hints 사용 권장
- docstring: Google 스타일
- 비밀 정보: `.env`에 저장, 코드에 하드코딩 금지
- 보안 원칙: 루트 CLAUDE.md §6-1 바이브코딩 보안 원칙 적용
- Human-in-the-loop: 에이전트가 자동 제출/실행하지 않음, 항상 사람이 확인

---

## 개발 명령어

```bash
# 의존성 설치
pip install -e ".[dev]"

# FastAPI 백엔드 서버 실행
uvicorn src.main:app --reload

# Streamlit 대시보드 실행 (별도 터미널)
streamlit run src/web/app.py

# 테스트 실행
pytest tests/ -v

# 보안 스캔
semgrep scan --config auto .
```

---

## 참고

- 루트 CLAUDE.md의 보안 원칙(§6-1) 항상 적용
- PRD: `docs/PRD.md` 참조
- 개발 계획: `~/.claude/plans/compressed-seeking-lemon.md`
- 현재 단계: Anthropic SDK 마이그레이션 완료 + Planner Director 에이전트 추가

---

*생성일: 2026.03.01 | 마지막 업데이트: 2026.03.02*
