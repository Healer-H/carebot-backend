import pytest
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from models.intent import IntentType, IntentClassificationRequest
from core.intent_classification import IntentClassifier
from core.message_service import MessageService
from models.chat_message import ChatMessage
from services.llm_client import LLMClient


@pytest.fixture
def mock_vector_db():
    db = AsyncMock()
    db.search.return_value = [
        {
            "content": "Paracetamol là thuốc giảm đau, hạ sốt thông dụng",
            "metadata": {
                "source": "Y học thường thức",
                "url": "https://example.com/paracetamol",
                "published_date": "2023-01-01",
            },
        }
    ]
    return db


@pytest.fixture
def mock_openai_response():
    with patch("openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_completion = AsyncMock()

        # Mock responses for different prompts
        mock_completion.choices = [
            AsyncMock(
                message=AsyncMock(content="medical_query")
            ),  # Intent classification
            AsyncMock(
                message=AsyncMock(
                    content='{"medical_condition":["đau đầu"],"medication":["paracetamol"]}'
                )
            ),  # Entity extraction
            AsyncMock(message=AsyncMock(content="0.95")),  # Confidence
            AsyncMock(
                message=AsyncMock(
                    content="Paracetamol là một thuốc giảm đau và hạ sốt an toàn khi sử dụng theo đúng liều lượng..."
                )
            ),  # Main response
        ]

        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client
        yield mock_openai


@pytest.mark.asyncio
async def test_intent_classification_to_message_processing(
    mock_vector_db, mock_openai_response
):
    # Setup real LLM client with mocked OpenAI
    llm_client = LLMClient(api_key="fake_key", model="gpt-4")

    # Setup IntentClassifier with real LLM
    intent_classifier = IntentClassifier(llm_client=llm_client)

    # Create a message
    message = ChatMessage(
        message_id=uuid4(),
        user_id="test_user",
        conversation_id=uuid4(),
        content="Tôi bị đau đầu, nên uống paracetamol không?",
        created_at=None,
    )

    # First test the intent classification
    intent_request = IntentClassificationRequest(
        message=message.content, user_id=message.user_id
    )

    intent_response = await intent_classifier.classify(intent_request)

    # Assert that intent is correctly classified
    assert intent_response.intent.primary_intent == IntentType.MEDICAL_QUERY
    assert intent_response.intent.confidence >= 0.9
    assert "paracetamol" in intent_response.intent.entities.get("medication", [])

    # Now create a MessageService with necessary mocks
    safety_guardrails = AsyncMock()
    safety_guardrails.check_input_safety.return_value = (True, 1, "")
    safety_guardrails.check_output_safety.return_value = (True, 1, "")
    safety_guardrails.add_medical_disclaimer.return_value = (
        "Paracetamol là thuốc giảm đau... DISCLAIMER"
    )

    source_citation = AsyncMock()
    source_citation.extract_sources.return_value = [
        {"title": "Y học thường thức", "url": "https://example.com/paracetamol"}
    ]

    message_processor = AsyncMock()
    message_processor.process.return_value = message.content

    response_formatter = AsyncMock()
    response_formatter.format_response.return_value = (
        "Paracetamol là thuốc giảm đau... FORMATTED"
    )

    emergency_detector = AsyncMock()
    emergency_detector.detect_emergency.return_value = (False, None)

    suggestion_generator = AsyncMock()
    suggestion_generator.generate_suggestions.return_value = [
        "Làm thế nào để giảm đau đầu tự nhiên?"
    ]

    # Create MessageService with all dependencies
    message_service = MessageService(
        vector_db=mock_vector_db,
        llm_client=llm_client,
        safety_guardrails=safety_guardrails,
        source_citation=source_citation,
        message_processor=message_processor,
        response_formatter=response_formatter,
        emergency_detector=emergency_detector,
        suggestion_generator=suggestion_generator,
        intent_classifier=intent_classifier,
    )

    # Process the message
    response = await message_service.process_message(message)

    # Assert the final response
    assert response.message_id == message.message_id
    assert response.conversation_id == message.conversation_id
    assert "FORMATTED" in response.response
    assert response.intent["primary_intent"] == IntentType.MEDICAL_QUERY
    assert len(response.suggestions) > 0
