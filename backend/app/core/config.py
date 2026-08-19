from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    PROJECT_NAME: str = "AskLedger"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    OPENROUTER_API_KEY: str

    MAX_SQL_ROWS: int = 100

    # JWT settings
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60

    # Comma-separated list of allowed frontend origins for CORS,
    # e.g. "http://localhost:3000,https://askledger.vercel.app"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Simple per-IP rate limit for the /chat endpoint (protects the OpenRouter bill
    # on a public demo). Format expected by slowapi, e.g. "20/hour".
    CHAT_RATE_LIMIT: str = "20/hour"

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
