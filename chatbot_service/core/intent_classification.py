from typing import Dict, List, Any, Tuple, Optional
from fastapi import Depends
import logging
from datetime import datetime
import asyncio

from services.llm_client import LLMClient, get_llm_client
from models.intent import (
    Intent,
    IntentType,
    IntentClassificationRequest,
    IntentClassificationResponse,
)
from config import settings

logger = logging.getLogger("intent_classification")


class IntentClassifier:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.confidence_threshold = 0.7

    async def classify(
        self, request: IntentClassificationRequest
    ) -> IntentClassificationResponse:
        """
        Phân loại ý định của người dùng dựa trên nội dung tin nhắn
        """
        message = request.message
        logger.info(f"Classifying intent for message: {message[:50]}...")

        # Xây dựng system prompt cho LLM để phân loại intent
        system_prompt = """
        Bạn là một hệ thống phân loại ý định (intent). Nhiệm vụ của bạn là phân tích tin nhắn của người dùng 
        và xác định ý định chính của họ. Phản hồi chỉ bao gồm một từ khóa intent không có thêm chú thích.

        Các intent có thể:
        - medical_query: Khi người dùng hỏi về vấn đề y tế, thuốc, bệnh tật, triệu chứng
        - location_search: Khi người dùng muốn tìm cơ sở y tế, bệnh viện, nhà thuốc gần đây
        - streak_challenge: Khi người dùng nói về thử thách hàng ngày, streak, mục tiêu sức khỏe
        - emergency: Khi người dùng mô tả tình trạng khẩn cấp, cần trợ giúp ngay lập tức
        - general_chat: Trò chuyện chung không thuộc các nhóm trên

        Chỉ trả về một từ intent, không kèm giải thích.
        """

        # Gọi LLM để phân loại
        intent_result = await self.llm_client.complete_with_system(
            system_prompt=system_prompt,
            user_prompt=message,
            temperature=0.1,  # Temperature thấp để có kết quả nhất quán
            max_tokens=10,  # Chỉ cần một từ
        )

        # Xử lý và chuẩn hóa kết quả
        intent_type = self._normalize_intent(intent_result.strip().lower())

        # Xác định các entity trong message
        entities = await self._extract_entities(message, intent_type)

        # Gọi thêm một LLM request để lấy confidence score
        confidence = await self._get_confidence_score(message, intent_type)

        # Xác định intent thứ cấp nếu có
        secondary_intents = []
        if confidence < 0.9:  # Nếu confidence thấp, có thể có intent thứ cấp
            secondary_intent, secondary_confidence = await self._get_secondary_intent(
                message, intent_type
            )
            if secondary_intent and secondary_confidence > 0.3:
                secondary_intents.append(
                    {"intent": secondary_intent, "confidence": secondary_confidence}
                )

        # Tạo intent response
        intent = Intent(
            primary_intent=intent_type,
            confidence=confidence,
            secondary_intents=secondary_intents,
            entities=entities,
        )

        # Xác định service cần chuyển hướng
        redirect_service = self._get_redirect_service(intent_type)

        return IntentClassificationResponse(
            intent=intent,
            redirect_service=redirect_service,
            confidence_threshold_met=confidence >= self.confidence_threshold,
        )

    def _normalize_intent(self, raw_intent: str) -> IntentType:
        """
        Chuẩn hóa kết quả intent từ LLM về một trong các IntentType
        """
        intent_mapping = {
            "medical_query": IntentType.MEDICAL_QUERY,
            "medical": IntentType.MEDICAL_QUERY,
            "medicine": IntentType.MEDICAL_QUERY,
            "health": IntentType.MEDICAL_QUERY,
            "location_search": IntentType.LOCATION_SEARCH,
            "location": IntentType.LOCATION_SEARCH,
            "find": IntentType.LOCATION_SEARCH,
            "nearby": IntentType.LOCATION_SEARCH,
            "streak_challenge": IntentType.STREAK_CHALLENGE,
            "streak": IntentType.STREAK_CHALLENGE,
            "challenge": IntentType.STREAK_CHALLENGE,
            "goal": IntentType.STREAK_CHALLENGE,
            "emergency": IntentType.EMERGENCY,
            "urgent": IntentType.EMERGENCY,
            "help": IntentType.EMERGENCY,
            "general_chat": IntentType.GENERAL_CHAT,
            "chat": IntentType.GENERAL_CHAT,
            "general": IntentType.GENERAL_CHAT,
            "greeting": IntentType.GENERAL_CHAT,
        }

        # Try exact match first
        if raw_intent in intent_mapping:
            return intent_mapping[raw_intent]

        # If no exact match, check partial matches
        for key, intent in intent_mapping.items():
            if key in raw_intent:
                return intent

        # Default to general_chat if no match
        return IntentType.GENERAL_CHAT

    async def _extract_entities(
        self, message: str, intent_type: IntentType
    ) -> Dict[str, List[str]]:
        """
        Trích xuất các entity từ tin nhắn dựa trên intent
        """
        entities: Dict[str, List[str]] = {}

        if intent_type == IntentType.MEDICAL_QUERY:
            # Extract medical entities like conditions, symptoms, medications
            system_prompt = """
            Trích xuất các thuật ngữ y tế từ văn bản sau đây. Phân loại thành:
            - medical_condition: các bệnh, triệu chứng, tình trạng y tế
            - medication: tên thuốc, thực phẩm chức năng, điều trị
            - symptom: các biểu hiện, triệu chứng cụ thể

            Trả về định dạng JSON:
            {
                "medical_condition": ["bệnh 1", "bệnh 2"],
                "medication": ["thuốc 1", "thuốc 2"],
                "symptom": ["triệu chứng 1", "triệu chứng 2"]
            }
            """

            try:
                result = await self.llm_client.complete_with_system(
                    system_prompt=system_prompt, user_prompt=message, temperature=0.1
                )

                # Parse JSON result (simplified, would need proper error handling)
                import json

                entities = json.loads(result)
            except Exception as e:
                logger.error(f"Error extracting medical entities: {str(e)}")

        elif intent_type == IntentType.LOCATION_SEARCH:
            # Extract location entities
            system_prompt = """
            Trích xuất thông tin về địa điểm từ văn bản sau đây. Phân loại thành:
            - location: tên địa điểm, vị trí
            - facility_type: loại cơ sở (bệnh viện, phòng khám, nhà thuốc)
            - distance: khoảng cách được đề cập

            Trả về định dạng JSON:
            {
                "location": ["địa điểm 1", "địa điểm 2"],
                "facility_type": ["loại cơ sở 1", "loại cơ sở 2"],
                "distance": ["khoảng cách 1", "khoảng cách 2"]
            }
            """

            try:
                result = await self.llm_client.complete_with_system(
                    system_prompt=system_prompt, user_prompt=message, temperature=0.1
                )

                # Parse JSON result
                import json

                entities = json.loads(result)
            except Exception as e:
                logger.error(f"Error extracting location entities: {str(e)}")

        # Thêm xử lý cho các intent khác tương tự

        return entities

    async def _get_confidence_score(
        self, message: str, intent_type: IntentType
    ) -> float:
        """
        Tính toán độ tin cậy của việc phân loại intent
        """
        system_prompt = f"""
        Đánh giá mức độ chắc chắn (0.0 đến 1.0) rằng tin nhắn sau đây thuộc về intent "{intent_type.value}".

        Định nghĩa intent:
        - medical_query: Hỏi về vấn đề y tế, thuốc, bệnh tật, triệu chứng
        - location_search: Tìm cơ sở y tế, bệnh viện, nhà thuốc gần đây
        - streak_challenge: Liên quan đến thử thách hàng ngày, streak, mục tiêu sức khỏe
        - emergency: Mô tả tình trạng khẩn cấp, cần trợ giúp ngay lập tức
        - general_chat: Trò chuyện chung không thuộc các nhóm trên

        Chỉ trả về một con số từ 0.0 đến 1.0, không kèm giải thích.
        """

        try:
            result = await self.llm_client.complete_with_system(
                system_prompt=system_prompt,
                user_prompt=message,
                temperature=0.1,
                max_tokens=10,
            )

            # Extract confidence score
            return float(result.strip())
        except Exception as e:
            logger.error(f"Error getting confidence score: {str(e)}")
            # Default confidence of 0.7 if there's an error
            return 0.7

    async def _get_secondary_intent(
        self, message: str, primary_intent: IntentType
    ) -> Tuple[Optional[IntentType], float]:
        """
        Xác định intent thứ cấp cho tin nhắn
        """
        # Loại bỏ primary intent khỏi danh sách các intent có thể
        possible_intents = [intent for intent in IntentType if intent != primary_intent]
        possible_intents_str = ", ".join([i.value for i in possible_intents])

        system_prompt = f"""
        Tin nhắn đã được xác định có intent chính là "{primary_intent.value}".
        Hãy xác định xem tin nhắn còn có thể thuộc intent thứ cấp nào trong số: {possible_intents_str}.

        Trả về định dạng: intent,confidence
        Ví dụ: medical_query,0.4

        Chỉ trả về một intent và độ tin cậy, không kèm giải thích.
        """

        try:
            result = await self.llm_client.complete_with_system(
                system_prompt=system_prompt,
                user_prompt=message,
                temperature=0.1,
                max_tokens=20,
            )

            # Parse result
            parts = result.strip().split(",")
            if len(parts) == 2:
                secondary_intent_str, confidence_str = parts
                secondary_intent = self._normalize_intent(secondary_intent_str.strip())
                confidence = float(confidence_str.strip())
                return secondary_intent, confidence

            return None, 0.0
        except Exception as e:
            logger.error(f"Error getting secondary intent: {str(e)}")
            return None, 0.0

    def _get_redirect_service(self, intent_type: IntentType) -> Optional[str]:
        """
        Xác định service cần chuyển hướng dựa trên intent
        """
        intent_to_service = {
            IntentType.MEDICAL_QUERY: "chatbot",
            IntentType.LOCATION_SEARCH: "location",
            IntentType.STREAK_CHALLENGE: "streak",
            IntentType.EMERGENCY: "emergency",
            IntentType.GENERAL_CHAT: "chatbot",
            IntentType.UNSAFE_CONTENT: None,
        }

        return intent_to_service.get(intent_type)


# Dependency
def get_intent_classifier(
    llm_client: LLMClient = Depends(get_llm_client),
) -> IntentClassifier:
    return IntentClassifier(llm_client)
