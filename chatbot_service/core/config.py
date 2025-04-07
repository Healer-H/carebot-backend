import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseModel):
    # Application settings
    APP_NAME: str = "Carebot Chatbot API"
    API_PREFIX: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://hiuminee:postgres@localhost:5432/carebot")
    
    # LLM settings
    # Default to OpenAI, can be set to "gemini" in env
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Vector search settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    VECTOR_DIMENSION: int = 1536  # For OpenAI embeddings
    
    # RAG settings
    MAX_RELEVANT_CHUNKS: int = 5

settings = Settings()