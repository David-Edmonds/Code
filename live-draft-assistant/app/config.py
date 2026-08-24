from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / ".data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    yahoo_client_id: str = ""
    yahoo_client_secret: str = ""
    yahoo_redirect_uri: str = "http://127.0.0.1:8765/auth/callback"
    yahoo_league_id: str = "810161"
    yahoo_team_id: int = 10

    league_teams: int = Field(default=10, ge=4, le=20)
    draft_slot: int = Field(default=7, ge=1, le=20)
    draft_rounds: int = Field(default=16, ge=1, le=40)
    scoring_format: str = "ppr"
    season_year: int = Field(default=2026, ge=2020, le=2100)
    poll_seconds: int = Field(default=5, ge=2, le=60)

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"

    @property
    def token_path(self) -> Path:
        return DATA_DIR / "yahoo_token.json"

    @property
    def manual_state_path(self) -> Path:
        return DATA_DIR / "manual_draft.json"

    @property
    def custom_rankings_path(self) -> Path:
        return DATA_DIR / "rankings.csv"

    @property
    def sleeper_cache_path(self) -> Path:
        return DATA_DIR / "sleeper_players.json"

    @property
    def adp_cache_path(self) -> Path:
        return DATA_DIR / "adp.json"


settings = Settings()
