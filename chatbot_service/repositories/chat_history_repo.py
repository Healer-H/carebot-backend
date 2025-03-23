from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from fastapi import Depends

from models.chat_message import ChatMessage
from models.conversation import Conversation, ConversationSummary
from config import settings

logger = logging.getLogger("chat_history_repo")

class ChatHistoryRepository:
    def __init__(self, mongo_uri: str, db_name: str):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        self.messages = self.db.messages
        self.conversations = self.db.conversations
        
    async def save_message(self, message: ChatMessage) -> str:
        """
        Lưu tin nhắn vào database
        """
        message_dict = message.dict()
        
        # Tạo message_id nếu chưa có
        if not message_dict.get("message_id"):
            message_dict["message_id"] = str(uuid4())
        
        # Tạo conversation_id nếu chưa có
        if not message_dict.get("conversation_id"):
            message_dict["conversation_id"] = str(uuid4())
            
        # Thêm timestamp nếu chưa có
        if not message_dict.get("created_at"):
            message_dict["created_at"] = datetime.utcnow()
        
        # Lưu tin nhắn
        try:
            await self.messages.insert_one(message_dict)
            
            # Cập nhật hoặc tạo conversation
            await self._update_conversation(message_dict)
            
            return message_dict["message_id"]
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            raise
        
    async def get_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        limit: int = 20, 
        before: Optional[datetime] = None
    ) -> Conversation:
        """
        Lấy cuộc trò chuyện theo ID
        """
        # Tạo query
        query = {
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
        if before:
            query["created_at"] = {"$lt": before}
        
        # Lấy tin nhắn
        cursor = self.messages.find(query).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        
        # Lấy tổng số tin nhắn
        total_messages = await self.messages.count_documents({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        # Lấy thông tin conversation
        conv_info = await self.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        if not messages or not conv_info:
            return None
        
        # Chuyển đổi tin nhắn
        chat_messages = [ChatMessage(**msg) for msg in messages]
        
        # Sắp xếp lại theo thời gian tăng dần
        chat_messages.reverse()
        
        return Conversation(
            conversation_id=UUID(conversation_id),
            messages=chat_messages,
            has_more=total_messages > len(messages),
            total_messages=total_messages
        )
        
    async def get_conversations(
        self, 
        user_id: str, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[ConversationSummary]:
        """
        Lấy danh sách cuộc trò chuyện
        """
        # Lấy danh sách conversation
        cursor = self.conversations.find({
            "user_id": user_id
        }).sort("last_message_time", -1).skip(offset).limit(limit)
        
        conversations = await cursor.to_list(length=limit)
        
        # Chuyển đổi thành ConversationSummary
        return [
            ConversationSummary(
                conversation_id=UUID(conv["conversation_id"]),
                title=conv.get("title", "Cuộc trò chuyện"),
                last_message=conv.get("last_message", ""),
                last_message_time=conv.get("last_message_time", datetime.utcnow()),
                message_count=conv.get("message_count", 0)
            )
            for conv in conversations
        ]
    
    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = 10
    ) -> List[ChatMessage]:
        """
        Lấy tin nhắn của cuộc trò chuyện
        """
        cursor = self.messages.find({
            "conversation_id": conversation_id
        }).sort("created_at", -1).limit(limit)
        
        messages = await cursor.to_list(length=limit)
        
        # Chuyển đổi và sắp xếp
        chat_messages = [ChatMessage(**msg) for msg in messages]
        chat_messages.reverse()
        
        return chat_messages
    
    async def _update_conversation(self, message: Dict[str, Any]) -> None:
        """
        Cập nhật hoặc tạo thông tin conversation
        """
        conversation_id = message["conversation_id"]
        user_id = message["user_id"]
        
        # Kiểm tra conversation đã tồn tại chưa
        existing = await self.conversations.find_one({
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
        if existing:
            # Cập nhật conversation
            await self.conversations.update_one(
                {"conversation_id": conversation_id, "user_id": user_id},
                {
                    "$set": {
                        "last_message": message["content"][:100],
                        "last_message_time": message.get("created_at", datetime.utcnow())
                    },
                    "$inc": {"message_count": 1}
                }
            )
        else:
            # Tạo conversation mới
            await self.conversations.insert_one({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": self._generate_title(message["content"]),
                "last_message": message["content"][:100],
                "last_message_time": message.get("created_at", datetime.utcnow()),
                "message_count": 1,
                "created_at": message.get("created_at", datetime.utcnow())
            })
    
    def _generate_title(self, content: str) -> str:
        """
        Tạo tiêu đề cho cuộc trò chuyện từ nội dung tin nhắn đầu tiên
        """
        # Lấy 5 từ đầu tiên, tối đa 50 ký tự
        words = content.split()[:5]
        title = " ".join(words)
        
        if len(title) > c:
            title = title[:47] + "..."
            
        return title or "Cuộc trò chuyện mới"

# Dependency
def get_chat_repository() -> ChatHistoryRepository:
    return ChatHistoryRepository(
        mongo_uri=settings.MONGODB_URI,
        db_name=settings.MONGODB_DB
    )