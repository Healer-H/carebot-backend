from typing import List, Optional
import logging
from fastapi import Depends
from datetime import datetime

from services.vector_db_manager import VectorDatabaseManager, get_vector_db_manager
from services.llm_client import LLMClient, get_llm_client
from core.safety_guardrails import SafetyGuardrails, get_safety_guardrails
from core.source_citation import SourceCitationService, get_source_citation_service
from core.message_processor import MessageProcessor, get_message_processor
from core.response_formatter import ResponseFormatter, get_response_formatter
from core.emergency_detector import EmergencyDetector, get_emergency_detector
from core.suggestion_generator import SuggestionGenerator, get_suggestion_generator
from utils.context_builder import ContextBuilder
from models.chat_message import ChatMessage, MessageResponse
from core.intent_classification import IntentClassifier, get_intent_classifier
from models.intent import Intent, IntentClassificationRequest, IntentType
from config import settings

logger = logging.getLogger("message_service")


class MessageService:
    def __init__(
        self,
        vector_db: VectorDatabaseManager,
        llm_client: LLMClient,
        safety_guardrails: SafetyGuardrails,
        source_citation: SourceCitationService,
        message_processor: MessageProcessor,
        response_formatter: ResponseFormatter,
        emergency_detector: EmergencyDetector,
        suggestion_generator: SuggestionGenerator,
        intent_classifier: IntentClassifier,
    ):
        self.vector_db = vector_db
        self.llm_client = llm_client
        self.safety_guardrails = safety_guardrails
        self.source_citation = source_citation
        self.message_processor = message_processor
        self.response_formatter = response_formatter
        self.emergency_detector = emergency_detector
        self.suggestion_generator = suggestion_generator
        self.intent_classifier = intent_classifier
        self.context_builder = ContextBuilder()

    async def process_message(
        self, message: ChatMessage, conversation_history: List[ChatMessage] = None
    ) -> MessageResponse:
        """
        Xử lý tin nhắn và tạo phản hồi sử dụng RAG
        """
        logger.info(f"Processing message: {message.message_id}")

        # Kiểm tra an toàn đầu vào
        is_safe, risk_level, reason = await self.safety_guardrails.check_input_safety(
            message
        )
        if not is_safe:
            logger.warning(f"Unsafe input detected: {reason}")
            return self._create_safety_response(message, reason)

        # Phân loại intent
        intent_request = IntentClassificationRequest(
            message=message.content,
            user_id=message.user_id,
            context=(
                {"conversation_id": str(message.conversation_id)}
                if message.conversation_id
                else {}
            ),
        )

        intent_response = await self.intent_classifier.classify(intent_request)
        intent_result = intent_response.intent

        # Xử lý dựa trên intent
        if intent_result.primary_intent == IntentType.EMERGENCY:
            emergency_type = "general"  # Default
            if "emergency_type" in intent_result.entities:
                emergency_types = intent_result.entities["emergency_type"]
                if emergency_types:
                    emergency_type = emergency_types[0]

            logger.info(f"Emergency intent detected: {emergency_type}")
            return await self._handle_emergency(message, emergency_type)

        # Nếu intent không phải là medical_query hoặc general_chat và có redirect_service
        # thì chuyển đến service tương ứng
        if (
            intent_result.primary_intent
            not in [IntentType.MEDICAL_QUERY, IntentType.GENERAL_CHAT]
            and intent_response.redirect_service
        ):
            # Trong trường hợp thực tế, đây là nơi sẽ redirect request đến service khác
            # Ví dụ: streak service, location service
            logger.info(f"Redirecting to {intent_response.redirect_service} service")

            # Vì đây là một ví dụ đơn giản, chúng ta sẽ tạo một response giả lập
            return await self._create_redirect_response(
                message, intent_result, intent_response.redirect_service
            )

        # Xử lý tin nhắn cho medical_query hoặc general_chat
        processed_query = await self.message_processor.process(message.content)

        # Truy xuất thông tin liên quan
        relevant_docs = await self.vector_db.search(
            processed_query, n_results=settings.TOP_K_RESULTS
        )

        # Xây dựng context
        prompt = self.context_builder.build_prompt(
            processed_query, relevant_docs, conversation_history
        )

        # Gửi prompt đến LLM
        raw_response = await self.llm_client.complete(prompt)

        # Kiểm tra an toàn đầu ra
        is_safe_output, risk_level_output, reason_output = (
            await self.safety_guardrails.check_output_safety(raw_response)
        )
        if not is_safe_output:
            logger.warning(f"Unsafe output detected: {reason_output}")
            return self._create_safety_response(message, reason_output)

        # Thêm disclaimer nếu cần
        response_with_disclaimer = await self.safety_guardrails.add_medical_disclaimer(
            raw_response, risk_level=max(risk_level, risk_level_output)
        )

        # Trích xuất nguồn tham khảo
        sources = await self.source_citation.extract_sources(
            response_with_disclaimer, relevant_docs
        )

        # Tạo gợi ý câu hỏi tiếp theo
        suggestions = await self.suggestion_generator.generate_suggestions(
            message.content, response_with_disclaimer, relevant_docs
        )

        # Định dạng phản hồi cuối cùng
        formatted_response = await self.response_formatter.format_response(
            response_with_disclaimer, sources
        )

        # Tạo và trả về response
        return MessageResponse(
            message_id=message.message_id,
            response=formatted_response,
            conversation_id=message.conversation_id,
            sources=sources,
            intent=intent_result.dict(),
            suggestions=suggestions,
            timestamp=message.created_at or datetime.utcnow(),
        )

    async def _create_redirect_response(
        self, message: ChatMessage, intent: Intent, service: str
    ) -> MessageResponse:
        """
        Tạo phản hồi khi cần chuyển hướng đến service khác
        """
        service_responses = {
            "location": (
                "Tôi thấy bạn đang tìm kiếm cơ sở y tế. "
                "Đang kết nối bạn với dịch vụ tìm kiếm vị trí để hỗ trợ tốt nhất..."
            ),
            "streak": (
                "Tôi thấy bạn quan tâm đến thử thách sức khỏe hàng ngày. "
                "Đang kết nối bạn với dịch vụ Streak Challenge..."
            ),
            "emergency": (
                "ĐÂY CÓ VẺ LÀ TÌNH HUỐNG KHẨN CẤP. "
                "Đang kết nối bạn với dịch vụ hỗ trợ khẩn cấp..."
            ),
        }

        response = service_responses.get(
            service, f"Đang chuyển tiếp yêu cầu của bạn đến dịch vụ {service}..."
        )

        # Tạo gợi ý phù hợp với intent
        suggestions = await self._get_intent_suggestions(intent.primary_intent)

        return MessageResponse(
            message_id=message.message_id,
            response=response,
            conversation_id=message.conversation_id,
            sources=[],
            intent=intent.dict(),
            suggestions=suggestions,
            timestamp=message.created_at or datetime.utcnow(),
        )

    async def _get_intent_suggestions(self, intent_type: IntentType) -> List[str]:
        """
        Tạo gợi ý dựa trên loại intent
        """
        intent_suggestions = {
            IntentType.LOCATION_SEARCH: [
                "Tìm bệnh viện gần nhất",
                "Có nhà thuốc nào gần đây không?",
                "Tôi cần tìm phòng khám nhi",
            ],
            IntentType.STREAK_CHALLENGE: [
                "Thử thách hôm nay là gì?",
                "Tôi đã hoàn thành streak được bao nhiêu ngày?",
                "Gợi ý bài tập cho tôi",
            ],
            IntentType.EMERGENCY: [
                "Cách sơ cứu khi bị bỏng",
                "Triệu chứng đau tim",
                "Xử lý khi bị ngất",
            ],
            IntentType.GENERAL_CHAT: [
                "Làm thế nào để duy trì lối sống lành mạnh?",
                "Cho tôi biết về CareBot",
                "Tôi nên uống bao nhiêu nước mỗi ngày?",
            ],
        }

        return intent_suggestions.get(
            intent_type,
            [
                "Tôi có thể hỏi về triệu chứng của cảm cúm không?",
                "Làm thế nào để duy trì lối sống lành mạnh?",
                "Tìm bệnh viện gần nhất",
            ],
        )

    def _create_safety_response(
        self, message: ChatMessage, reason: str
    ) -> MessageResponse:
        """
        Tạo phản hồi an toàn khi phát hiện nội dung không phù hợp
        """
        response = (
            "Xin lỗi, tôi không thể cung cấp thông tin cho truy vấn này. "
            "Vui lòng đặt câu hỏi khác hoặc liên hệ với chuyên gia y tế."
        )

        return MessageResponse(
            message_id=message.message_id,
            response=response,
            conversation_id=message.conversation_id,
            sources=[],
            intent={"primary_intent": "unsafe_content", "confidence": 0.95},
            suggestions=[
                "Tôi có thể hỏi về triệu chứng của cảm cúm không?",
                "Làm thế nào để duy trì lối sống lành mạnh?",
            ],
            timestamp=message.created_at or datetime.utcnow(),
        )

    async def _handle_emergency(
        self, message: ChatMessage, emergency_type: str
    ) -> MessageResponse:
        """
        Xử lý tình huống khẩn cấp
        """
        # Tạo phản hồi khẩn cấp với hướng dẫn cụ thể
        emergency_response = (
            f"ĐÂY CÓ VẺ LÀ TÌNH HUỐNG KHẨN CẤP. Nếu bạn hoặc người khác đang gặp nguy hiểm, "
            f"hãy gọi ngay số cấp cứu 115 hoặc đến cơ sở y tế gần nhất. "
        )

        if emergency_type == "cardiac":
            emergency_response += (
                "Dấu hiệu đau tim cần được xử lý ngay lập tức bởi chuyên gia y tế."
            )
        elif emergency_type == "stroke":
            emergency_response += "Dấu hiệu đột quỵ cần được xử lý trong vòng vài giờ để giảm thiểu tổn thương não."

        return MessageResponse(
            message_id=message.message_id,
            response=emergency_response,
            conversation_id=message.conversation_id,
            sources=[],
            intent={"primary_intent": "emergency", "confidence": 0.98},
            suggestions=[
                "Làm thế nào để nhận biết dấu hiệu đau tim?",
                "Cách sơ cứu khi có người bị ngất?",
            ],
            timestamp=message.created_at or datetime.utcnow(),
        )


# Dependency
def get_message_service(
    vector_db: VectorDatabaseManager = Depends(get_vector_db_manager),
    llm_client: LLMClient = Depends(get_llm_client),
    safety_guardrails: SafetyGuardrails = Depends(get_safety_guardrails),
    source_citation: SourceCitationService = Depends(get_source_citation_service),
    message_processor: MessageProcessor = Depends(get_message_processor),
    response_formatter: ResponseFormatter = Depends(get_response_formatter),
    emergency_detector: EmergencyDetector = Depends(get_emergency_detector),
    suggestion_generator: SuggestionGenerator = Depends(get_suggestion_generator),
    intent_classifier: IntentClassifier = Depends(get_intent_classifier),
) -> MessageService:
    return MessageService(
        vector_db,
        llm_client,
        safety_guardrails,
        source_citation,
        message_processor,
        response_formatter,
        emergency_detector,
        suggestion_generator,
        intent_classifier,
    )
