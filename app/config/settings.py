from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Existing app settings
    app_name: str = "Real Estate API"
    app_version: str = "1.0.0"
    app_description: str = "AI-powered Real Estate System"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    db_echo: bool = False

    # OpenAI API (for AutoGen and embeddings)
    openai_api_key: str
    openai_model_name: str = "gpt-4o-mini"
    
    # Phoenix Observability (Optional)
    phoenix_api_key: Optional[str] = None
    phoenix_collector_endpoint: Optional[str] = None
    phoenix_project_name: str = "realestate-autogen"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
