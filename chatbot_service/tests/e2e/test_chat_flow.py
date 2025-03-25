import pytest
import requests
import os

BASE_URL = os.environ.get("CHATBOT_SERVICE_URL", "http://localhost:8000")


def get_auth_token():
    # In a real scenario, you would get a token from your auth service
    # For testing, you could use a test token or authenticate with test credentials
    auth_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@example.com", "password": "test_password"},
    )
    return auth_response.json()["token"]


@pytest.fixture
def auth_headers():
    token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


def test_medical_query_flow(auth_headers):
    # Step 1: Send a message to the chat endpoint
    message_data = {"content": "Tôi bị đau đầu và sốt nhẹ, nên làm gì?"}

    response = requests.post(
        f"{BASE_URL}/api/chat/message", headers=auth_headers, json=message_data
    )

    assert response.status_code == 201
    result = response.json()

    # Verify the response structure
    assert "message_id" in result
    assert "response" in result
    assert "conversation_id" in result
    assert "intent" in result
    assert "suggestions" in result

    conversation_id = result["conversation_id"]

    # Verify intent classification
    assert result["intent"]["primary_intent"] == "medical_query"
    assert result["intent"]["confidence"] >= 0.7

    # Step 2: Get the conversation history
    history_response = requests.get(
        f"{BASE_URL}/api/chat/conversation/{conversation_id}", headers=auth_headers
    )

    assert history_response.status_code == 200
    history = history_response.json()

    assert history["conversation_id"] == conversation_id
    assert len(history["messages"]) >= 2  # User message and bot response

    # Step 3: Respond to a suggestion
    follow_up_data = {
        "content": "Làm thế nào để giảm đau đầu tự nhiên?",
        "conversation_id": conversation_id,
    }

    follow_up_response = requests.post(
        f"{BASE_URL}/api/chat/message", headers=auth_headers, json=follow_up_data
    )

    assert follow_up_response.status_code == 201
    follow_up_result = follow_up_response.json()

    assert follow_up_result["conversation_id"] == conversation_id
    assert follow_up_result["intent"]["primary_intent"] == "medical_query"

    # Step 4: Get conversations list
    conversations_response = requests.get(
        f"{BASE_URL}/api/chat/conversations", headers=auth_headers
    )

    assert conversations_response.status_code == 200
    conversations = conversations_response.json()

    # Verify our conversation is in the list
    conversation_ids = [conv["conversation_id"] for conv in conversations]
    assert conversation_id in conversation_ids


def test_location_search_flow(auth_headers):
    # Test location search intent that should redirect to location service
    message_data = {"content": "Tìm bệnh viện gần nhất quanh đây"}

    response = requests.post(
        f"{BASE_URL}/api/chat/message", headers=auth_headers, json=message_data
    )

    assert response.status_code == 201
    result = response.json()

    # Verify intent classification
    assert result["intent"]["primary_intent"] == "location_search"
    assert "facility_type" in result["intent"].get("entities", {})

    # Verify response indicating redirect to location service
    assert "tìm kiếm cơ sở y tế" in result["response"].lower()

    # In a real scenario with multiple services, you might follow up with a call to the location service
    # But for this test, we're just verifying the chatbot identified and handled the intent correctly
