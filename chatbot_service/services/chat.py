from typing import List, Dict, Any, Optional, AsyncIterator
import json
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from repositories.chat import ConversationRepository, MessageRepository
from services.llm import llm_service
from services.rag import RAGService


class ChatService:
    """Service for chat conversations with RAG integration"""

    @staticmethod
    def create_conversation(db: Session, user_id: str) -> Dict[str, Any]:
        """Create a new conversation for a user"""
        conversation = ConversationRepository.create_conversation(db, user_id)
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "created_at": conversation.created_at.isoformat(),
        }

    @staticmethod
    def get_conversation(db: Session, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation details with messages"""
        conversation = ConversationRepository.get_conversation_by_id(
            db, conversation_id
        )
        if not conversation:
            return None

        messages = MessageRepository.get_messages_by_conversation_id(
            db, conversation_id
        )

        # Convert to dict
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_results": msg.tool_results,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
        }

    @staticmethod
    def get_user_conversations(
        db: Session, user_id: str, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        conversations = ConversationRepository.get_conversations_by_user_id(
            db, user_id, skip, limit
        )

        return [
            {
                "id": conv.id,
                "user_id": conv.user_id,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
            }
            for conv in conversations
        ]

    @staticmethod
    def delete_conversation(db: Session, conversation_id: int) -> bool:
        """Delete a conversation"""
        return ConversationRepository.delete_conversation(db, conversation_id)

    @staticmethod
    def add_user_message(
        db: Session, conversation_id: int, content: str
    ) -> Dict[str, Any]:
        """Add a user message to a conversation"""
        message = MessageRepository.create_message(
            db=db, conversation_id=conversation_id, role="user", content=content
        )

        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }

    @staticmethod
    def add_assistant_message(
        db: Session,
        conversation_id: int,
        content: str,
        tool_calls: Optional[Dict] = None,
        tool_result: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Add an assistant message to a conversation"""
        message = MessageRepository.create_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_result,
        )

        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "tool_calls": message.tool_calls,
            "tool_results": message.tool_results,
            "created_at": message.created_at.isoformat(),
        }

    @staticmethod
    def add_tool_result(
        db: Session, message_id: int, tool_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a message with tool results"""
        message = MessageRepository.get_message_by_id(db, message_id)
        if not message:
            return None

        # Update message with tool results
        message.tool_results = tool_results
        db.commit()
        db.refresh(message)

        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "tool_calls": message.tool_calls,
            "tool_results": message.tool_results,
            "created_at": message.created_at.isoformat(),
        }

    @staticmethod
    def generate_response(
        db: Session, conversation_id: int, query: str
    ) -> Dict[str, Any]:
        """
        Generate a response to a user query with RAG

        Args:
            db: Database session
            conversation_id: ID of the conversation
            query: User query

        Returns:
            Generated response with optional tool calls
        """
        # Add user message to conversation
        ChatService.add_user_message(db, conversation_id, query)

        # Get conversation history
        messages = MessageRepository.get_messages_by_conversation_id(
            db, conversation_id
        )

        # Format messages for LLM
        formatted_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        # Retrieve relevant context using RAG
        # context = RAGService.retrieve_relevant_context(db, query)
        context = ""

        # Generate response from LLM with context
        llm_response = llm_service.generate_response(formatted_messages, context)
        tool_calls, tool_results = [], []
        for conversation_turn in llm_response["conversation_turns"]:
            tool_calls.extend(conversation_turn.get("tool_calls", []))
            tool_results.extend(conversation_turn.get("tool_results", []))
        print("LLM Response:", llm_response)
        # Add assistant response to conversation
        assistant_message = ChatService.add_assistant_message(
            db, conversation_id, llm_response["final_content"], tool_calls, tool_results
        )

        return assistant_message

    @staticmethod
    def generate_response_stream(
        db: Session, conversation_id: int, messages: List[Any]
    ) -> Any:
        """
        Stream a response to a user query with RAG for Vercel AI SDK

        Args:
            db: Database session
            conversation_id: ID of the conversation
            query: User query

        Returns:
            StreamingResponse containing the generated content chunks
        """
        # Add user message to conversation
        # ChatService.add_user_message(db, conversation_id, query)
        
        # Get conversation history
        # messages = MessageRepository.get_messages_by_conversation_id(
        #     db, conversation_id
        # )

        # Format messages for LLM
        # formatted_messages = [
        #     {"role": msg.role, "content": msg.content} for msg in messages
        # ]

        # Retrieve relevant context using RAG
        # context = RAGService.retrieve_relevant_context(db, query)

        llm_response = llm_service.generate_response_stream(messages)


        # Get the full content from the final chunks to save in the database
        # final_content = await llm_service.get_final_streaming_content()

        # Store the complete message in the database
        # assistant_message = ChatService.add_assistant_message(
        #     db,
        #     conversation_id,
        #     final_content,
        #     llm_service.current_stream_tool_calls,
        #     llm_service.current_stream_tool_results,
        # )

        return llm_response