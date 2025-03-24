from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class MessageFeedback(BaseModel):
    feedback_id: Optional[UUID] = Field(default_factory=uuid4)
    message_id: UUID
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None
    is_helpful: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    success: bool
    message: str
