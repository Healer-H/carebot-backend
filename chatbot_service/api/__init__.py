from fastapi import APIRouter

from api.chatbot import router as chatbot_router
from api.knowledge_base import router as knowledge_base_router

# Create main router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(knowledge_base_router, prefix="/knowledge", tags=["knowledge base"])

# Export router
__all__ = ['api_router']