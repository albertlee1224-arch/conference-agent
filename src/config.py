"""환경변수 및 설정 관리."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정. .env 파일에서 자동 로딩."""

    # API 키
    anthropic_api_key: str

    # DB
    database_path: str = "data/conference.db"

    # 서버
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:8501",
        "https://conference-agent.streamlit.app",
        "https://conference-agent-78qcjalyjenzozi7sw6ups.streamlit.app",
    ]

    # 에이전트
    max_agent_turns: int = 30
    default_speaker_count: int = 10

    # 스캔 스케줄러
    daily_scan_enabled: bool = True
    daily_scan_hour: int = 9   # KST 기준 메인 스캔 시각 (0-23)
    daily_scan_minute: int = 0
    scan_interval_hours: int = 6  # 주기적 스캔 간격 (시간)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def database_dir(self) -> Path:
        """DB 파일의 부모 디렉토리."""
        return Path(self.database_path).parent


settings = Settings()
