from fastapi import APIRouter, Depends, Body, HTTPException, status
from typing import Dict, Any

from core.intent_classification import IntentClassifier, get_intent_classifier
from models.intent import IntentClassificationRequest, IntentClassificationResponse
from api.middleware import get_current_user

router = APIRouter()


@router.post("/classify", response_model=IntentClassificationResponse)
async def classify_intent(
    request: IntentClassificationRequest = Body(...),
    intent_classifier: IntentClassifier = Depends(get_intent_classifier),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Phân loại ý định (intent) từ tin nhắn của người dùng
    """
    # Thêm user_id nếu không có
    if not request.user_id:
        request.user_id = current_user["user_id"]

    # Phân loại intent
    response = await intent_classifier.classify(request)

    return response
