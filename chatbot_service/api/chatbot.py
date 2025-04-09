from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
import json
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from enum import Enum

from core.database import get_db
from services.chat import ChatService
from repositories.chat import MessageRepository

router = APIRouter()


# Request and response models
class ConversationCreate(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")


class ConversationResponse(BaseModel):
    id: int
    user_id: str
    created_at: str


class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int

class ToolInvocationState(str, Enum):
    CALL = "call"
    PARTIAL_CALL = "partial-call"
    RESULT = "result"


class ToolInvocation(BaseModel):
    state: ToolInvocationState = Field(ToolInvocationState.CALL, description="State of tool invocation")
    toolCallId: str = Field(..., description="ID of the tool call")
    toolName: str = Field(..., description="Name of the tool being called")
    args: Dict[str, Any] = Field(default={}, description="Arguments for the tool call")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result of the tool call")


class MessageCreate(BaseModel):
    role: str = Field(..., description="Role of the message sender (user | assistant | tool)")
    content: str = Field(..., description="The content of the message")
    toolInvocations: Optional[List[ToolInvocation]] = Field(None, description="Tool calls in this message")


class MessagesCreate(BaseModel):
    messages: List[MessageCreate] = Field(
        ..., description="List of messages to add to the conversation"
    )


class ToolCallArguments(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    tool_call_id: str = Field(..., description="ID of the tool call this result is for")
    function_name: str = Field(..., description="Name of the function that was called")
    result: Dict[str, Any] = Field(..., description="Result of the function call")


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    created_at: str


class ChatResponse(BaseModel):
    message: MessageResponse
    conversation_id: int



def convert_to_openai_messages(
    messages: List[MessageCreate],
) -> List[ChatCompletionMessageParam]:
    openai_messages = []

    for message in messages:
        parts = []
        tool_calls = []

        parts.append({"type": "text", "text": message.content})

        # if message.experimental_attachments:
        #     for attachment in message.experimental_attachments:
        #         if attachment.contentType.startswith("image"):
        #             parts.append(
        #                 {"type": "image_url", "image_url": {"url": attachment.url}}
        #             )
        #
        #         elif attachment.contentType.startswith("text"):
        #             parts.append({"type": "text", "text": attachment.url})

        if message.toolInvocations:
            for toolInvocation in message.toolInvocations:
                tool_calls.append(
                    {
                        "id": toolInvocation.toolCallId,
                        "type": "function",
                        "function": {
                            "name": toolInvocation.toolName,
                            "arguments": json.dumps(toolInvocation.args),
                        },
                    }
                )

        tool_calls_dict = (
            {"tool_calls": tool_calls} if tool_calls else {"tool_calls": None}
        )

        openai_messages.append(
            {
                "role": message.role,
                "content": parts,
                **tool_calls_dict,
            }
        )

        if message.toolInvocations:
            for toolInvocation in message.toolInvocations:
                tool_message = {
                    "role": "tool",
                    "tool_call_id": toolInvocation.toolCallId,
                    "content": json.dumps(toolInvocation.result),
                }

                openai_messages.append(tool_message)

    return openai_messages



@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    conversation: ConversationCreate, db: Session = Depends(get_db)
):
    """Create a new conversation"""
    return ChatService.create_conversation(db, conversation.user_id)


@router.get("/conversations/{conversation_id}", response_model=dict)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get a conversation with its messages"""
    conversation = ChatService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.get("/users/{user_id}/conversations", response_model=ConversationListResponse)
def get_user_conversations(
    user_id: str, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    """Get all conversations for a user"""
    conversations = ChatService.get_user_conversations(db, user_id, skip, limit)
    return {"conversations": conversations, "total": len(conversations)}


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation"""
    success = ChatService.delete_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return None


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def create_message(
    conversation_id: int, messages: MessagesCreate, db: Session = Depends(get_db)
):
    """Send multiple message and get a response"""
    # Check if conversation exists
    conversation = ChatService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    latest_message = None
    for message in messages.messages[::-1]:
        if message.role == "user":
            latest_message = message
            break

    if not latest_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found",
        )

    response = ChatService.generate_response(
        db, conversation_id, latest_message.content
    )

    return {"message": response, "conversation_id": conversation_id}


@router.post("/conversations/{conversation_id}/messages/stream")
async def create_message_stream(
    conversation_id: int, messages: MessagesCreate, db: Session = Depends(get_db)
):
    """Stream message responses for Vercel AI SDK"""
    # Check if conversation exists
    conversation = ChatService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    latest_message = None
    for message in messages.messages[::-1]:
        if message.role == "user":
            latest_message = message
            break

    if not latest_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found",
        )

    # Add user message to conversation first
    ChatService.add_user_message(db, conversation_id, latest_message.content)

    # Stream the response
    return await ChatService.generate_response_stream(
        db, conversation_id, latest_message.content
    )


@router.post("/messages/{message_id}/tool-results", response_model=MessageResponse)
def add_tool_result(
    message_id: int, tool_result: ToolResult, db: Session = Depends(get_db)
):
    """Add a tool result to a message"""
    # Get the message
    message = MessageRepository.get_message_by_id(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )

    # Check if the message has tool calls
    if not message.tool_calls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message does not have any tool calls",
        )

    # Find the tool call with the matching ID
    tool_call_exists = False
    for tool_call in message.tool_calls:
        if tool_call.get("id") == tool_result.tool_call_id:
            tool_call_exists = True
            break

    if not tool_call_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool call with ID {tool_result.tool_call_id} not found in message",
        )

    # Format tool result
    tool_results = message.tool_results or {}
    tool_results[tool_result.tool_call_id] = {
        "function_name": tool_result.function_name,
        "result": tool_result.result,
    }

    # Add tool result to message
    updated_message = ChatService.add_tool_result(db, message_id, tool_results)

    return updated_message
