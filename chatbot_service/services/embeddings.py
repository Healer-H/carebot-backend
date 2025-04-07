from typing import List, Union
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import settings

class EmbeddingService:
    """Service for creating text embeddings"""
    
    def __init__(self):
        """Initialize the embedding service based on configuration"""
        if settings.LLM_PROVIDER == "openai":
            self.embedding_model = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        elif settings.LLM_PROVIDER == "gemini":
            # Fallback to OpenAI embeddings since Google Generative AI embeddings 
            # might not be as well suited for RAG as OpenAI's
            self.embedding_model = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text"""
        return self.embedding_model.embed_query(text)
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts"""
        return self.embedding_model.embed_documents(texts)


# Singleton pattern
embedding_service = EmbeddingService()