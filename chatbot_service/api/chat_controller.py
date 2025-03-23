from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

from core.rag_engine import RagEngine, get_rag_engine
from repositories.chat_history_repo import ChatHistoryRepository, get_chat_repository
from models.chat_message import ChatMessage, MessageResponse
from models.conversation import Conversation, ConversationSummary
from api.middleware import get_current_user

router = APIRouter()

@router.post("/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: ChatMessage = Body(...),
    rag_engine: RagEngine = Depends(get_rag_engine),
    chat_repo: ChatHistoryRepository = Depends(get_chat_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Gửi tin nhắn và nhận phản hồi từ chatbot
    """
    # Xác nhận người dùng
    message.user_id = current_user["user_id"]
    
    # Tạo conversation_id nếu chưa có
    if not message.conversation_id:
        message.conversation_id = uuid4()
    
    # Lưu tin nhắn người dùng
    message_id = await chat_repo.save_message(message)
    
    # Lấy lịch sử cuộc trò chuyện
    conversation_history = await chat_repo.get_conversation_messages(
        str(message.conversation_id),
        limit=10
    )
    
    # Xử lý tin nhắn bằng RAG Engine
    response = await rag_engine.process_message(message, conversation_history)
    
    # Lưu tin nhắn của bot
    bot_message = ChatMessage(
        user_id=current_user["user_id"],
        conversation_id=message.conversation_id,
        content=response.response,
        is_bot=True,
        metadata={"sources": [s.dict() for s in response.sources]}
    )
    await chat_repo.save_message(bot_message)
    
    return response

@router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: UUID = Path(...),
    limit: int = Query(20, ge=1, le=100),
    before: Optional[datetime] = Query(None),
    chat_repo: ChatHistoryRepository = Depends(get_chat_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy lịch sử cuộc trò chuyện theo ID
    """
    conversation = await chat_repo.get_conversation(
        str(conversation_id),
        user_id=current_user["user_id"],
        limit=limit,
        before=before
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    chat_repo: ChatHistoryRepository = Depends(get_chat_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Lấy danh sách cuộc trò chuyện
    """
    conversations = await chat_repo.get_conversations(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset
    )
    
    return conversations