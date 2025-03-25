import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import sys

prj_root = Path(__file__).parent.parent
sys.path.insert(0, str(prj_root))


from core.intent_classification import IntentClassifier
from models.intent import IntentClassificationRequest, IntentType


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.complete_with_system = AsyncMock()
    return client


@pytest.fixture
def intent_classifier(mock_llm_client):
    return IntentClassifier(llm_client=mock_llm_client)


@pytest.mark.asyncio
async def test_medical_query_classification(intent_classifier, mock_llm_client):
    # Arrange
    request = IntentClassificationRequest(
        message="Tôi bị đau đầu liên tục trong ba ngày qua, nên làm gì?"
    )
    mock_llm_client.complete_with_system.side_effect = [
        "medical_query",  # Intent response
        '{"medical_condition": ["đau đầu"], "medication": [], "symptom": ["đau đầu liên tục"]}',  # Entities
        "0.95",  # Confidence
        "general_chat,0.2",  # Secondary intent
    ]

    # Act
    response = await intent_classifier.classify(request)

    # Assert
    assert response.intent.primary_intent == IntentType.MEDICAL_QUERY
    assert response.intent.confidence >= 0.9
    assert "đau đầu" in response.intent.entities.get("medical_condition", [])
    assert response.redirect_service == "chatbot"


@pytest.mark.asyncio
async def test_location_search_classification(intent_classifier, mock_llm_client):
    # Arrange
    request = IntentClassificationRequest(message="Tìm bệnh viện gần nhất quanh đây")
    mock_llm_client.complete_with_system.side_effect = [
        "location_search",  # Intent response
        '{"location": ["gần đây"], "facility_type": ["bệnh viện"], "distance": []}',  # Entities
        "0.92",  # Confidence
        "medical_query,0.1",  # Secondary intent
    ]

    # Act
    response = await intent_classifier.classify(request)

    # Assert
    assert response.intent.primary_intent == IntentType.LOCATION_SEARCH
    assert "bệnh viện" in response.intent.entities.get("facility_type", [])
    assert response.redirect_service == "location"


@pytest.mark.asyncio
async def test_emergency_classification(intent_classifier, mock_llm_client):
    # Arrange
    request = IntentClassificationRequest(
        message="Cứu, tôi khó thở và đau ngực dữ dội!"
    )
    mock_llm_client.complete_with_system.side_effect = [
        "emergency",  # Intent response
        '{"emergency_type": ["cardiac"], "symptom": ["khó thở", "đau ngực"]}',  # Entities
        "0.98",  # Confidence
        "medical_query,0.4",  # Secondary intent
    ]

    # Act
    response = await intent_classifier.classify(request)

    # Assert
    assert response.intent.primary_intent == IntentType.EMERGENCY
    assert response.intent.confidence >= 0.7 
    assert response.redirect_service == "emergency"
    # assert len(response.intent.secondary_intents) == 1
    # assert response.intent.secondary_intents[0]["intent"] == IntentType.MEDICAL_QUERY


@pytest.mark.asyncio
async def test_normalize_intent(intent_classifier):
    # Test direct matches
    assert (
        intent_classifier._normalize_intent("medical_query") == IntentType.MEDICAL_QUERY
    )
    assert (
        intent_classifier._normalize_intent("location_search")
        == IntentType.LOCATION_SEARCH
    )

    # Test partial/related terms
    assert (
        intent_classifier._normalize_intent("medical info") == IntentType.MEDICAL_QUERY
    )
    assert (
        intent_classifier._normalize_intent("find nearby") == IntentType.LOCATION_SEARCH
    )

    # Test default case
    assert (
        intent_classifier._normalize_intent("unknown_intent") == IntentType.GENERAL_CHAT
    )
