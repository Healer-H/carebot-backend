from typing import List, Dict, Any
import random
import logging
from fastapi import Depends

logger = logging.getLogger("suggestion_generator")

class SuggestionGenerator:
    def __init__(self):
        # Gợi ý chung
        self.general_suggestions = [
            "Làm thế nào để duy trì lối sống lành mạnh?",
            "Tôi nên uống bao nhiêu nước mỗi ngày?",
            "Các loại vitamin cần thiết cho cơ thể là gì?",
            "Làm sao để ngủ ngon hơn?",
            "Những thực phẩm tốt cho sức khỏe tim mạch?",
            "Cách phòng ngừa cảm lạnh và cúm?"
        ]
        
        # Gợi ý theo chủ đề
        self.topic_suggestions = {
            "dinh dưỡng": [
                "Chế độ ăn cân bằng gồm những gì?",
                "Các loại thực phẩm giàu protein?",
                "Thực phẩm hỗ trợ hệ miễn dịch?"
            ],
            "vận động": [
                "Các bài tập thể dục đơn giản tại nhà?",
                "Nên tập thể dục bao nhiêu phút mỗi ngày?",
                "Làm sao để duy trì thói quen tập thể dục?"
            ],
            "stress": [
                "Cách giảm stress hiệu quả?",
                "Các bài tập thư giãn đơn giản?",
                "Thiền có tác dụng gì đối với stress?"
            ],
            "giấc ngủ": [
                "Làm sao để cải thiện chất lượng giấc ngủ?",
                "Bao nhiêu giờ ngủ là đủ?",
                "Những thói quen xấu ảnh hưởng đến giấc ngủ?"
            ]
        }
    
    async def generate_suggestions(
        self, 
        query: str, 
        response: str, 
        retrieved_docs: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Tạo gợi ý câu hỏi tiếp theo dựa trên nội dung
        """
        # Xác định chủ đề
        topic = self._identify_topic(query, response)
        suggestions = []
        
        # Lấy gợi ý theo chủ đề
        if topic in self.topic_suggestions:
            topic_suggs = self.topic_suggestions[topic]
            suggestions.extend(random.sample(topic_suggs, min(2, len(topic_suggs))))
        
        # Tạo gợi ý theo nội dung tìm được
        content_suggs = self._generate_from_content(retrieved_docs)
        if content_suggs:
            suggestions.append(content_suggs[0])
        
        # Nếu chưa đủ 3 gợi ý, thêm gợi ý chung
        while len(suggestions) < 3:
            general_sugg = random.choice(self.general_suggestions)
            if general_sugg not in suggestions:
                suggestions.append(general_sugg)
        
        # Đảm bảo không quá 3 gợi ý
        return suggestions[:3]
    
    def _identify_topic(self, query: str, response: str) -> str:
        """
        Xác định chủ đề của cuộc trò chuyện
        """
        combined_text = (query + " " + response).lower()
        
        for topic in self.topic_suggestions.keys():
            if topic in combined_text:
                return topic
        
        return ""
    
    def _generate_from_content(self, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        """
        Tạo gợi ý dựa trên nội dung đã truy xuất
        """
        suggestions = []
        
        for doc in retrieved_docs:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Lấy tiêu đề làm gợi ý
            if metadata.get('title'):
                suggestions.append(f"Cho tôi biết thêm về {metadata['title']}?")
            
            # Trích xuất thuật ngữ y tế từ nội dung
            terms = self._extract_medical_terms(content)
            if terms:
                suggestions.append(f"{terms[0]} là gì?")
        
        return suggestions
    
    def _extract_medical_terms(self, content: str) -> List[str]:
        """
        Trích xuất thuật ngữ y tế từ nội dung
        """
        # Thuật ngữ y tế thông dụng để tìm kiếm
        medical_terms = [
            "tiểu đường", "huyết áp", "cholesterol", "viêm khớp",
            "đau nửa đầu", "trầm cảm", "lo âu", "mất ngủ", "béo phì"
        ]
        
        found_terms = []
        for term in medical_terms:
            if term in content.lower():
                found_terms.append(term)
        
        return found_terms

# Dependency
def get_suggestion_generator() -> SuggestionGenerator:
    return SuggestionGenerator()