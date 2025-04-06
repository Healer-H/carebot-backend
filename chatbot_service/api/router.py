from fastapi import APIRouter
from .chat_controller import router as chat_router
from .feedback_controller import router as feedback_router
from .intent_controller import router as intent_router
from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .streak_routes import router as streak_router
from .badge_routes import router as badge_router
from .blog_routes import router as blog_router
router = APIRouter()

# Register sub-routers
router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(feedback_router, prefix="/chat/feedback", tags=["feedback"])
router.include_router(intent_router, prefix="/intent", tags=["intent"])
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(streak_router, prefix="/streaks", tags=["Health Streaks"])
router.include_router(badge_router, prefix="/badges", tags=["Badges"])
router.include_router(blog_router, prefix="/blog", tags=["Blog"])