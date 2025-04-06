from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "CareBot Chatbot Service"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # MongoDB
    MONGODB_URI: str = Field(..., env="MONGODB_URI")
    MONGODB_DB: str = Field(default="carebot", env="MONGODB_DB")
    #DB
    DB_USERNAME: str = Field(..., env="DB_USERNAME")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: str = Field(..., env="DB_PORT")
    DB_NAME: str = Field(..., env="DB_NAME")
    # Vector Database (Chroma)
    CHROMA_HOST: str = Field(default="localhost", env="CHROMA_HOST")
    CHROMA_PORT: int = Field(default=8000, env="CHROMA_PORT")
    CHROMA_COLLECTION: str = Field(default="medical_knowledge", env="CHROMA_COLLECTION")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002", env="OPENAI_EMBEDDING_MODEL"
    )

    # Safety Guardrails
    MAX_RISK_LEVEL: int = Field(default=3, env="MAX_RISK_LEVEL")
    DISCLAIMER_TEMPLATE: str = Field(
        default="Lưu ý: Thông tin được cung cấp chỉ mang tính chất tham khảo và không thay thế cho tư vấn y tế chuyên nghiệp.",
        env="DISCLAIMER_TEMPLATE",
    )

    # Authentication
    TOKEN_SECRET_KEY: str = Field(..., env="TOKEN_SECRET_KEY")
    TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="TOKEN_EXPIRE_MINUTES")

    # RAG Settings
    TOP_K_RESULTS: int = Field(default=5, env="TOP_K_RESULTS")

    # Intent Classification
    INTENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7, env="INTENT_CONFIDENCE_THRESHOLD"
    )
    INTENT_MODEL: str = Field(default="gpt-4o", env="INTENT_MODEL")

    # Service routing
    LOCATION_SERVICE_URL: str = Field(
        default="http://location-service:8001/api", env="LOCATION_SERVICE_URL"
    )
    STREAK_SERVICE_URL: str = Field(
        default="http://streak-service:8002/api", env="STREAK_SERVICE_URL"
    )
    EMERGENCY_SERVICE_URL: str = Field(
        default="http://emergency-service:8003/api", env="EMERGENCY_SERVICE_URL"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
