"""Configuration settings for the Intelligent Query Retrieval System."""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="Intelligent Query Retrieval System")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # OpenRouter/DeepSeek
    openai_api_key: str = Field(..., description="OpenRouter API key")
    openai_model: str = Field(default="deepseek/deepseek-r1-0528:free")
    openai_base_url: str = Field(default="https://openrouter.ai/api/v1")

    # Pinecone
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_environment: str = Field(..., description="Pinecone environment")
    pinecone_index_name: str = Field(default="document-retrieval")

    # PostgreSQL
    database_url: str = Field(..., description="PostgreSQL database URL")
    postgres_user: Optional[str] = Field(
        default=None, description="PostgreSQL username (optional if using DATABASE_URL)")
    postgres_password: Optional[str] = Field(
        default=None, description="PostgreSQL password (optional if using DATABASE_URL)")
    postgres_db: Optional[str] = Field(
        default=None, description="PostgreSQL database name (optional if using DATABASE_URL)")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    # Document Processing
    max_file_size_mb: int = Field(default=50)
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)

    # Vector Search
    similarity_threshold: float = Field(default=0.7)
    max_results: int = Field(default=10)
    enable_embeddings: bool = Field(
        default=False, description="Enable vector embeddings (requires compatible embedding model)")

    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30)

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
