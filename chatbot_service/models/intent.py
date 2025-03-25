from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class IntentType(str, Enum):
    MEDICAL_QUERY = "medical_query"
    LOCATION_SEARCH = "location_search"
    STREAK_CHALLENGE = "streak_challenge"
    EMERGENCY = "emergency"
    GENERAL_CHAT = "general_chat"
    UNSAFE_CONTENT = "unsafe_content"


class Intent(BaseModel):
    primary_intent: IntentType
    confidence: float
    secondary_intents: List[Dict[str, Union[IntentType, float]]] = Field(default_factory=list)
    entities: Dict[str, List[str]] = Field(default_factory=dict)


class IntentClassificationRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class IntentClassificationResponse(BaseModel):
    intent: Intent
    action: Optional[str] = None
    redirect_service: Optional[str] = None
    confidence_threshold_met: bool = True