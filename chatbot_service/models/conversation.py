from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from .chat_message import ChatMessage

class ConversationSummary(BaseModel):
    conversation_id: UUID
    title: str
    last_message: str
    last_message_time: datetime
    message_count: int
    
    class Config:
        orm_mode = True

class Conversation(BaseModel):
    conversation_id: UUID
    messages: List[ChatMessage]
    has_more: bool = False
    total_messages: int
    
    class Config:
        orm_mode = True