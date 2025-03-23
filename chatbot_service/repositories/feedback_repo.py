from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from fastapi import Depends

from models.message_feedback import MessageFeedback
from config import settings

logger = logging.getLogger("feedback_repo")

class FeedbackRepository:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.feedback = self.db.feedback
        
    async def save_feedback(self, feedback: MessageFeedback) -> str:
        """
        Lưu feedback vào database
        """
        feedback_dict = feedback.dict()
        
        # Tạo feedback_id nếu chưa có
        if not feedback_dict.get("feedback_id"):
            feedback_dict["feedback_id"] = str(uuid4())
            
        # Thêm timestamp nếu chưa có
        if not feedback_dict.get("created_at"):
            feedback_dict["created_at"] = datetime.utcnow()
        
        # Lưu feedback
        try:
            await self.feedback.insert_one(feedback_dict)
            return feedback_dict["feedback_id"]
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            raise
    
    async def get_feedback_by_message(self, message_id: UUID) -> Optional[MessageFeedback]:
        """
        Lấy feedback theo message_id
        """
        result = await self.feedback.find_one({"message_id": str(message_id)})
        
        if result:
            return MessageFeedback(**result)
        return None
    
    async def get_user_feedback(self, user_id: str, limit: int = 10) -> List[MessageFeedback]:
        """
        Lấy danh sách feedback của user
        """
        cursor = self.feedback.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        
        return [MessageFeedback(**item) for item in results]

# Dependency
def get_feedback_repository() -> FeedbackRepository:
    return FeedbackRepository(
        mongo_uri=settings.MONGODB_URI,
        db_name=settings.MONGODB_DB
    )