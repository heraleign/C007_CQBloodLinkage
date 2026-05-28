"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lineage Platform"
    app_version: str = "1.0.0"
    debug: bool = False

    # MySQL
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "123456"
    db_database: str = "lineage"

    # Neo4j
    neo4j_uri: str = "bolt://127.0.0.1:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j2026"

    # Redis
    redis_uri: str = "redis://192.168.137.189:6379/0"

    # AI
    ai_api_endpoint: str = "https://api.example.com/v1/chat/completions"
    ai_api_key: str = ""
    ai_model: str = "claude-sonnet-4-6"
    ai_timeout: int = 30000

    # Auth
    aes_key: str = "default-aes-key-32bytes!!"
    system_code: str = "dxmh"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
            "?charset=utf8mb4"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
