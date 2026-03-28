from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_mode: str = "sqlite"  # "sqlite" or "supabase"
    sqlite_path: str = "./data/persona_tracking.db"
    database_url: str | None = None  # PostgreSQL connection string for Supabase

    # Supabase (optional, for direct Supabase client usage)
    supabase_url: str | None = None
    supabase_service_key: str | None = None

    # Auth
    api_key: str = "change-me-in-production"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def effective_database_url(self) -> str:
        if self.database_mode == "supabase" and self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.sqlite_path}"


settings = Settings()
