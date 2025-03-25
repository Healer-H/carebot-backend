# chatbot_service/tests/unit/test_chat_controller.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from api.chat_controller import router
from models.chat_message import ChatMessage, MessageResponse

app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_message_service():
    return AsyncMock()


@pytest.fixture
def mock_chat_repo():
    return AsyncMock()


@pytest.fixture
def mock_current_user():
    return {"user_id": "test_user", "email": "test@example.com"}


@pytest.mark.asyncio
async def test_send_message(
    client, mock_message_service, mock_chat_repo, mock_current_user
):
    # Override dependencies
    app.dependency_overrides = {
        "get_message_service": lambda: mock_message_service,
        "get_chat_repository": lambda: mock_chat_repo,
        "get_current_user": lambda: mock_current_user,
    }

    # Mock repository responses
    mock_chat_repo.save_message.return_value = "message_id"
    mock_chat_repo.get_conversation_messages.return_value = []

    # Mock message service response
    message_response = MessageResponse(
        message_id=uuid4(),
        response="Test response",
        conversation_id=uuid4(),
        sources=[],
        intent={"primary_intent": "medical_query", "confidence": 0.95},
        suggestions=[],
        timestamp=datetime.now(),
    )
    mock_message_service.process_message.return_value = message_response

    # Test data
    test_message = {
        "content": "Test message",
    }

    # Act
    response = client.post("/message", json=test_message)

    # Assert
    assert response.status_code == 201
    assert "response" in response.json()
    assert response.json()["response"] == "Test response"
    assert "intent" in response.json()
    assert response.json()["intent"]["primary_intent"] == "medical_query"

    # Clean up
    app.dependency_overrides = {}
