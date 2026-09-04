import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/watchlist"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 14  # 2 weeks
    cors_origins_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]
    poll_interval_market_open_seconds: int = 8
    poll_interval_market_closed_seconds: int = 120
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "none")

    class Config:
        env_file = ".env"


settings = Settings()
