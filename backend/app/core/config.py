from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vector API"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/vector"
    backend_cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )
    rusprofile_headless: bool = False
    rusprofile_browser_channel: str | None = None
    rusprofile_executable_path: str | None = None
    rusprofile_slow_mo_ms: int = 250
    rusprofile_debug_screenshots: bool = True
    rusprofile_human_mode: bool = True
    rusprofile_min_delay_ms: int = 500
    rusprofile_max_delay_ms: int = 2000
    rusprofile_scroll_step_min: int = 250
    rusprofile_scroll_step_max: int = 700
    rusprofile_captcha_manual_timeout_seconds: int = 180
    rusprofile_captcha_poll_interval_ms: int = 2000
    polza_enabled: bool = False
    polza_api_key: str | None = None
    polza_base_url: str = "https://polza.ai/api/v1"
    polza_model: str = "google/gemini-3.1-flash-lite"
    llm_scoring_enabled: bool = False
    llm_scoring_threshold: int = 75
    llm_scoring_review_min_score: int = 50
    llm_scoring_max_input_chars: int = 6000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
