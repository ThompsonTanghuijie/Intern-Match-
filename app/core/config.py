from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Intern Match"
    database_url: str = "sqlite:///./intern_match.db"
    github_user_agent: str = "InternMatchBot/0.1 (+https://github.com/)"
    request_timeout_seconds: int = 15
    request_retries: int = 3
    request_rate_limit_seconds: float = 1.0
    scheduler_enabled: bool = False
    crawl_interval_hours: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
