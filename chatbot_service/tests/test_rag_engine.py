import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import uuid4

from core.rag_engine import RagEngine
from models.chat_message import ChatMessage, MessageResponse
from models.source import Source

@pytest.fixture
def mock_vector_db():
    mock = MagicMock()
    mock.search.return_value = asyncio.Future()
    mock.search.return_value.set_result([
        {
            'content': 'Thông tin về bệnh tiểu đường',
            'metadata': {'title': 'Hướng dẫn điều trị tiểu đường', 'url': 'https://example.com/diabetes'},
            'score': 0.85
        }
    ])
    return mock

@pytest.fixture
def mock_llm_client():
    mock = MagicMock()
    mock.complete.return_value = asyncio.Future()
    mock.complete.return_value.set_result("Bệnh tiểu đường là bệnh rối loạn chuyển hóa mãn tính.")
    return mock

@pytest.fixture
def mock_safety_guardrails():
    mock = MagicMock()
    mock.check_input_safety.return_value = asyncio.Future()
    mock.check_input_safety.return_value.set_result((True, 1, ""))
    mock.check_output_safety.return_value = asyncio.Future()
    mock.check_output_safety.return_value.set_result((True, 1, ""))
    mock.add_medical_disclaimer.return_value = asyncio.Future()
    mock.add_medical_disclaimer.return_value.set_result("Bệnh tiểu đường là bệnh rối loạn chuyển hóa mãn tính.\n\nLưu ý: Thông tin được cung cấp chỉ mang tính chất tham khảo.")
    return mock

@pytest.fixture
def mock_source_citation():
    mock = MagicMock()
    mock.extract_sources.return_value = asyncio.Future()
    mock.extract_sources.return_value.set_result([
        Source(title="Hướng dẫn điều trị tiểu đường", url="https://example.com/diabetes")
    ])
    return mock

@pytest.fixture
def mock_emergency_detector():
    mock = MagicMock()
    mock.detect_emergency.return_value = asyncio.Future()
    mock.detect_emergency.return_value.set_result((False, ""))
    return mock

@pytest.fixture
def mock_message_processor():
    mock = MagicMock()
    mock.process.return_value = asyncio.Future()
    mock.process.return_value.set_result("bệnh tiểu đường là gì")
    return mock

@pytest.fixture
def mock_response_formatter():
    mock = MagicMock()
    mock.format_response.return_value = asyncio.Future()
    mock.format_response.return_value.set_result("Bệnh tiểu đường là bệnh rối loạn chuyển hóa mãn tính.\n\nNguồn: Hướng dẫn điều trị tiểu đường")
    return mock

@pytest.fixture
def mock_suggestion_generator():
    mock = MagicMock()
    mock.generate_suggestions.return_value = asyncio.Future()
    mock.generate_suggestions.return_value.set_result(["Triệu chứng của bệnh tiểu đường?", "Cách phòng ngừa bệnh tiểu đường?"])
    return mock

@pytest.mark.asyncio
async def test_process_message(
    mock_vector_db, 
    mock_llm_client, 
    mock_safety_guardrails,
    mock_source_citation,
    mock_emergency_detector,
    mock_message_processor,
    mock_response_formatter,
    mock_suggestion_generator
):
    # Arrange
    rag_engine = RagEngine(
        mock_vector_db,
        mock_llm_client,
        mock_safety_guardrails,
        mock_source_citation,
        mock_message_processor,
        mock_response_formatter,
        mock_emergency_detector,
        mock_suggestion_generator
    )
    
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Bệnh tiểu đường là gì?",
        created_at=datetime.utcnow()
    )
    
    # Act
    response = await rag_engine.process_message(message)
    
    # Assert
    assert isinstance(response, MessageResponse)
    assert response.message_id == message.message_id
    assert response.conversation_id == message.conversation_id
    assert "Bệnh tiểu đường" in response.response
    assert len(response.sources) == 1
    assert len(response.suggestions) == 2
    
    # Verify calls
    mock_safety_guardrails.check_input_safety.assert_called_once()
    mock_emergency_detector.detect_emergency.assert_called_once()
    mock_message_processor.process.assert_called_once()
    mock_vector_db.search.assert_called_once()
    mock_llm_client.complete.assert_called_once()
    mock_safety_guardrails.check_output_safety.assert_called_once()
    mock_source_citation.extract_sources.assert_called_once()
    mock_suggestion_generator.generate_suggestions.assert_called_once()
    mock_response_formatter.format_response.assert_called_once()