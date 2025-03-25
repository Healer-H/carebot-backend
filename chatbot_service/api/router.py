from fastapi import APIRouter
from .chat_controller import router as chat_router
from .feedback_controller import router as feedback_router
from .intent_controller import router as intent_router

router = APIRouter()

# Register sub-routers
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(feedback_router, prefix="/chat/feedback", tags=["feedback"])
router.include_router(intent_router, prefix="/intent", tags=["intent"])
