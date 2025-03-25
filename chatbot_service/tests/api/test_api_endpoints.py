import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4, UUID

from main import app
from models.chat_message import MessageResponse
from models.intent import Intent, IntentType, IntentClassificationResponse

import jwt
from datetime import datetime, timedelta
from config import settings

def create_test_token():
    payload = {
        "user_id": "test_user",
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }
    return jwt.encode(payload, settings.TOKEN_SECRET_KEY, algorithm="HS256")

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_test_token()
    print(f"token='{token}'")  # Optional để debug
    return {"Authorization": f"Bearer {token}"}


def test_intent_classify_endpoint(client, auth_headers):
    # Mock the dependencies
    with patch("api.intent_controller.get_intent_classifier") as mock_get_classifier:
        # Setup mocks
        mock_classifier = AsyncMock()
        mock_intent = Intent(
            primary_intent=IntentType.MEDICAL_QUERY,
            confidence=0.95,
            entities={"medical_condition": ["đau đầu"]},
        )
        mock_response = IntentClassificationResponse(
            intent=mock_intent,
            redirect_service="chatbot",
            confidence_threshold_met=True,
        )
        mock_classifier.classify.return_value = mock_response
        mock_get_classifier.return_value = mock_classifier
        #mock_get_user.return_value = {"user_id": "test_user"}

        # Test data
        request_data = {
            "message": "Tôi bị đau đầu quá",
        }

        # Act
        response = client.post(
            "/api/intent/classify", headers=auth_headers, json=request_data
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["intent"]["primary_intent"] == IntentType.MEDICAL_QUERY
        assert result["intent"]["confidence"] == 0.95
        assert result["redirect_service"] == "chatbot"


#
# def test_chat_message_endpoint(client, auth_headers):
#     # Mock the dependencies
#     with patch("api.chat_controller.get_message_service") as mock_get_service, patch(
#         "api.chat_controller.get_chat_repository"
#     ) as mock_get_repo, patch("api.chat_controller.get_current_user") as mock_get_user:
#
#         # Setup mocks
#         conversation_id = uuid4()
#         message_id = uuid4()
#
#         mock_service = AsyncMock()
#         mock_response = MessageResponse(
#             message_id=message_id,
#             response="Test response",
#             conversation_id=conversation_id,
#             sources=[],
#             intent={"primary_intent": "medical_query", "confidence": 0.95},
#             suggestions=["suggestion1"],
#         )
#         mock_service.process_message.return_value = mock_response
#         mock_get_service.return_value = mock_service
#
#         mock_repo = AsyncMock()
#         mock_repo.save_message.return_value = str(message_id)
#         mock_repo.get_conversation_messages.return_value = []
#         mock_get_repo.return_value = mock_repo
#
#         mock_get_user.return_value = {"user_id": "test_user"}
#
#         # Test data
#         request_data = {
#             "content": "Tôi bị đau đầu quá",
#         }
#
#         # Act
#         response = client.post(
#             "/api/chat/message", headers=auth_headers, json=request_data
#         )
#
#         # Assert
#         assert response.status_code == 201
#         result = response.json()
#         assert result["response"] == "Test response"
#         assert result["intent"]["primary_intent"] == "medical_query"
#         assert UUID(result["conversation_id"]) is not None
