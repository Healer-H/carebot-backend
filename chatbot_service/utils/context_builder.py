from typing import List, Dict, Any
import logging

from models.chat_message import ChatMessage
from config import settings

logger = logging.getLogger("context_builder")

class ContextBuilder:
    def __init__(self):
        self.system_prompt = """Bạn là trợ lý y tế CareBot. Cung cấp thông tin y tế chính xác, đáng tin cậy và dễ hiểu. 
        Luôn trả lời dựa trên nguồn đáng tin cậy. Nếu không có thông tin, hãy nói rõ là bạn không biết.
        Không đưa ra chẩn đoán y tế. Nhắc người dùng tham khảo ý kiến bác sĩ khi cần.
        Luôn trích dẫn nguồn thông tin của bạn. Thông tin phải ngắn gọn, súc tích nhưng đầy đủ."""
        
    def build_prompt(
        self, 
        query: str, 
        retrieved_docs: List[Dict[str, Any]], 
        conversation_history: List[ChatMessage] = None
    ) -> str:
        """
        Xây dựng prompt hoàn chỉnh cho LLM
        """
        prompt = f"{self.system_prompt}\n\n"
        
        # Thêm thông tin từ retrieved_docs
        if retrieved_docs:
            prompt += "Thông tin tham khảo:\n"
            for i, doc in enumerate(retrieved_docs, 1):
                content = doc.get('content', '')
                metadata = doc.get('metadata', {})
                source_info = f"(Nguồn: {metadata.get('title', 'Không rõ nguồn')})"
                
                prompt += f"[{i}] {content[:1000]} {source_info}\n\n"
        
        # Thêm lịch sử trò chuyện
        if conversation_history and len(conversation_history) > 0:
            prompt += "Lịch sử trò chuyện gần đây:\n"
            for msg in conversation_history[-3:]:  # Chỉ lấy 3 tin nhắn gần nhất
                sender = "Bot" if msg.is_bot else "Người dùng"
                prompt += f"{sender}: {msg.content}\n"
            prompt += "\n"
        
        # Thêm query người dùng
        prompt += f"Người dùng hiện tại: {query}\n\n"
        
        # Hướng dẫn cho phản hồi
        prompt += "Phản hồi của bạn phải chính xác, rõ ràng và đáng tin cậy. "
        prompt += "Nếu thông tin không đầy đủ, hãy thừa nhận giới hạn và tránh suy đoán. "
        prompt += "Phản hồi nên được định dạng rõ ràng, dễ đọc với đoạn văn ngắn gọn và mạch lạc."
        
        logger.debug(f"Built prompt with {len(retrieved_docs)} retrieved docs and {len(conversation_history) if conversation_history else 0} conversation history messages")
        
        return prompt