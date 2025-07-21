"""
Application configuration management.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Security
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]

    # Vector Database Configuration
    vector_db_provider: str = "pinecone"  # "pinecone", "faiss", "qdrant"

    # Pinecone Configuration
    pinecone_api_key: Optional[str] = None
    pinecone_env: Optional[str] = None
    default_index_name: str = "code-docs"  # Use a standard name to reuse indexes

    # Qdrant Configuration
    qdrant_url: Optional[str] = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "code-docs"

    # Faiss Configuration
    faiss_index_path: str = "./faiss_indexes"
    faiss_index_name: str = "code-docs"

    # LLM Configuration
    llm_provider: str = "gemini"  # "gemini", "openai", "azure_openai"

    # Gemini Configuration
    gemini_api_key: Optional[str] = None

    # OpenAI Configuration
    openai_api_key: Optional[str] = None

    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_embedding_deployment: Optional[str] = None

    # LLM Settings
    llm_temperature: float = 0.0

    # Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 10
    max_repo_size_mb: int = 500
    processing_timeout: int = 600  # 10 minutes

    # Storage Configuration
    temp_directory: str = "./temp"
    repo_directory: str = "./dummy_repo"
    docs_output_directory: str = "./docs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
