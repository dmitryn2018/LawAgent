from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Legal AI System"
    app_env: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/legal_ai"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # LLM Provider
    llm_provider: str = "mock"  # openai, ollama, mock
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1"
    
    # Embedding Provider
    embedding_provider: str = "mock"  # openai, ollama, mock
    openai_embedding_model: str = "text-embedding-3-small"
    ollama_embedding_model: str = "nomic-embed-text"
    
    # Storage
    storage_path: str = "/app/storage"
    templates_path: str = "/app/templates"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

