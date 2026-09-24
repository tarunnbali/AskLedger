from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    PROJECT_NAME: str = "AskLedger"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    # Gemini's OpenAI-compatible endpoint — same `openai` SDK, just pointed at
    # Google. Free tier, no billing risk for a public portfolio demo.
    GEMINI_API_KEY: str
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    # Comma-separated, in fallback order. Free-tier quotas are counted per model,
    # so SQL generation prefers the stronger models, while intent classification
    # and explanations prefer the lite model.
    GEMINI_SQL_MODELS: str = "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite"
    GEMINI_FAST_MODELS: str = "gemini-3.5-flash-lite,gemini-3.5-flash,gemini-3.6-flash"

    MAX_SQL_ROWS: int = 100

    # JWT settings
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60

    # Comma-separated list of allowed frontend origins for CORS,
    # e.g. "http://localhost:3000,https://askledger.vercel.app"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Simple per-IP rate limit for the /chat endpoint (protects the free LLM quota
    # on a public demo). Format expected by slowapi, e.g. "20/hour".
    CHAT_RATE_LIMIT: str = "20/hour"

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def sql_models(self) -> list[str]:
        return [m.strip() for m in self.GEMINI_SQL_MODELS.split(",") if m.strip()]

    @property
    def fast_models(self) -> list[str]:
        return [m.strip() for m in self.GEMINI_FAST_MODELS.split(",") if m.strip()]


settings = Settings()
