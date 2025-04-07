from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.chat import Conversation, Message

class ConversationRepository:
    """Repository for conversation CRUD operations"""
    
    @staticmethod
    def create_conversation(db: Session, user_id: str) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by its ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def get_conversations_by_user_id(db: Session, user_id: str, skip: int = 0, limit: int = 20) -> List[Conversation]:
        """Get all conversations for a user with pagination"""
        return db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(desc(Conversation.updated_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> bool:
        """Delete a conversation and its messages"""
        conversation = ConversationRepository.get_conversation_by_id(db, conversation_id)
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False


class MessageRepository:
    """Repository for message CRUD operations"""
    
    @staticmethod
    def create_message(db: Session, conversation_id: int, role: str, content: str,
                      tool_calls: Optional[Dict] = None, tool_results: Optional[Dict] = None) -> Message:
        """Create a new message in a conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    @staticmethod
    def get_message_by_id(db: Session, message_id: int) -> Optional[Message]:
        """Get a message by its ID"""
        return db.query(Message).filter(Message.id == message_id).first()
    
    @staticmethod
    def get_messages_by_conversation_id(db: Session, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get all messages for a conversation with pagination"""
        return db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at)\
            .offset(skip)\
            .limit(limit)\
            .all()