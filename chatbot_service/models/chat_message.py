from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .source import Source


class ChatMessage(BaseModel):
    message_id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: str
    conversation_id: Optional[UUID] = None
    content: str
    is_bot: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message_id: UUID
    response: str
    conversation_id: UUID
    sources: List[Source] = []
    intent: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
