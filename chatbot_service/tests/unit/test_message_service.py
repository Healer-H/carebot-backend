import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from core.message_service import MessageService
from models.chat_message import ChatMessage, MessageResponse
from models.intent import Intent, IntentType, IntentClassificationResponse


@pytest.fixture
def mock_dependencies():
    return {
        "vector_db": AsyncMock(),
        "llm_client": AsyncMock(),
        "safety_guardrails": AsyncMock(),
        "source_citation": AsyncMock(),
        "message_processor": AsyncMock(),
        "response_formatter": AsyncMock(),
        "emergency_detector": AsyncMock(),
        "suggestion_generator": AsyncMock(),
        "intent_classifier": AsyncMock(),
    }


@pytest.fixture
def message_service(mock_dependencies):
    return MessageService(**mock_dependencies)


@pytest.mark.asyncio
async def test_process_message_medical_query(message_service, mock_dependencies):
    # Arrange
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Tôi bị đau đầu, nên uống thuốc gì?",
        created_at=datetime.utcnow(),
    )

    # Mock safety check
    mock_dependencies["safety_guardrails"].check_input_safety.return_value = (
        True,
        1,
        "",
    )
    mock_dependencies["safety_guardrails"].check_output_safety.return_value = (
        True,
        1,
        "",
    )
    mock_dependencies["safety_guardrails"].add_medical_disclaimer.return_value = (
        "Response with disclaimer"
    )

    # Mock intent classification
    intent = Intent(
        primary_intent=IntentType.MEDICAL_QUERY,
        confidence=0.95,
        entities={"medical_condition": ["đau đầu"], "medication": []},
    )
    intent_response = IntentClassificationResponse(
        intent=intent, redirect_service="chatbot", confidence_threshold_met=True
    )
    mock_dependencies["intent_classifier"].classify.return_value = intent_response

    # Mock other services
    mock_dependencies["message_processor"].process.return_value = "processed query"
    mock_dependencies["vector_db"].search.return_value = [
        {"content": "doc1", "metadata": {}}
    ]
    mock_dependencies["llm_client"].complete.return_value = "LLM response"
    mock_dependencies["source_citation"].extract_sources.return_value = []
    mock_dependencies["suggestion_generator"].generate_suggestions.return_value = [
        "suggestion1"
    ]
    mock_dependencies["response_formatter"].format_response.return_value = (
        "Formatted response"
    )

    # Act
    response = await message_service.process_message(message)

    # Assert
    assert isinstance(response, MessageResponse)
    assert response.response == "Formatted response"
    assert response.message_id == message.message_id
    assert response.conversation_id == message.conversation_id
    assert "primary_intent" in response.intent
    assert response.intent["primary_intent"] == IntentType.MEDICAL_QUERY

    # Verify service calls
    mock_dependencies["safety_guardrails"].check_input_safety.assert_called_once()
    mock_dependencies["intent_classifier"].classify.assert_called_once()
    mock_dependencies["message_processor"].process.assert_called_once()
    mock_dependencies["vector_db"].search.assert_called_once()
    mock_dependencies["llm_client"].complete.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_emergency(message_service, mock_dependencies):
    # Arrange
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Cứu tôi đang bị đau tim!",
        created_at=datetime.utcnow(),
    )

    # Mock safety check
    mock_dependencies["safety_guardrails"].check_input_safety.return_value = (
        True,
        1,
        "",
    )

    # Mock intent classification for emergency
    intent = Intent(
        primary_intent=IntentType.EMERGENCY,
        confidence=0.98,
        entities={"emergency_type": ["cardiac"]},
    )
    intent_response = IntentClassificationResponse(
        intent=intent, redirect_service="emergency", confidence_threshold_met=True
    )
    mock_dependencies["intent_classifier"].classify.return_value = intent_response

    # Act
    response = await message_service.process_message(message)

    # Assert
    assert isinstance(response, MessageResponse)
    assert "ĐÂY CÓ VẺ LÀ TÌNH HUỐNG KHẨN CẤP" in response.response
    assert "primary_intent" in response.intent
    assert response.intent["primary_intent"] == IntentType.EMERGENCY

    # Verify that processing stopped after emergency detection
    mock_dependencies["vector_db"].search.assert_not_called()
    mock_dependencies["llm_client"].complete.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_redirect_to_location(message_service, mock_dependencies):
    # Arrange
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Tìm bệnh viện gần đây",
        created_at=datetime.utcnow(),
    )

    # Mock safety check
    mock_dependencies["safety_guardrails"].check_input_safety.return_value = (
        True,
        1,
        "",
    )

    # Mock intent classification for location search
    intent = Intent(
        primary_intent=IntentType.LOCATION_SEARCH,
        confidence=0.92,
        entities={"facility_type": ["bệnh viện"]},
    )
    intent_response = IntentClassificationResponse(
        intent=intent, redirect_service="location", confidence_threshold_met=True
    )
    mock_dependencies["intent_classifier"].classify.return_value = intent_response

    # Act
    response = await message_service.process_message(message)

    # Assert
    assert isinstance(response, MessageResponse)
    assert "tìm kiếm cơ sở y tế" in response.response.lower()
    assert "primary_intent" in response.intent
    assert response.intent["primary_intent"] == IntentType.LOCATION_SEARCH

    # Verify that the message is redirected without using RAG
    mock_dependencies["vector_db"].search.assert_not_called()
    mock_dependencies["llm_client"].complete.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_unsafe_content(message_service, mock_dependencies):
    # Arrange
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Unsafe content example",
        created_at=datetime.utcnow(),
    )

    # Mock safety check to fail
    mock_dependencies["safety_guardrails"].check_input_safety.return_value = (
        False,
        5,
        "Unsafe content detected",
    )

    # Act
    response = await message_service.process_message(message)

    # Assert
    assert isinstance(response, MessageResponse)
    assert "Xin lỗi, tôi không thể cung cấp thông tin" in response.response
    assert "primary_intent" in response.intent
    assert response.intent["primary_intent"] == "unsafe_content"

    # Verify that processing stopped after safety check
    mock_dependencies["intent_classifier"].classify.assert_not_called()
    mock_dependencies["message_processor"].process.assert_not_called()
