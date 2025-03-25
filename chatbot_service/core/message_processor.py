import re
import logging
from fastapi import Depends

logger = logging.getLogger("message_processor")


class MessageProcessor:
    def __init__(self):
        self.stopwords = [
            "à",
            "là",
            "của",
            "và",
            "cho",
            "trong",
            "với",
            "có",
            "được",
            "không",
            "những",
            "này",
            "về",
            "từ",
            "một",
            "các",
            "để",
            "đến",
            "theo",
            "như",
        ]

    async def process(self, content: str) -> str:
        """
        Xử lý tin nhắn đầu vào để tối ưu hóa truy vấn
        """
        # Chuẩn hóa nội dung
        normalized = self._normalize_text(content)

        # Chuyển đổi các từ khóa y tế thông dụng
        normalized = self._convert_common_terms(normalized)

        # Tách từ khóa y tế chính
        keywords = self._extract_medical_keywords(normalized)

        # Log
        logger.debug(f"Normalized query: {normalized}")
        logger.debug(f"Extracted keywords: {keywords}")

        return normalized

    def _normalize_text(self, text: str) -> str:
        """
        Chuẩn hóa văn bản: loại bỏ ký tự đặc biệt, dấu câu thừa
        """
        # Chuyển về chữ thường
        text = text.lower()

        # Loại bỏ ký tự đặc biệt
        text = re.sub(r"[^\w\s]", " ", text)

        # Loại bỏ khoảng trắng thừa
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _convert_common_terms(self, text: str) -> str:
        """
        Chuyển đổi từ khóa thông dụng sang thuật ngữ y tế
        """
        term_mapping = {
            "đau đầu": "đau đầu (nhức đầu)",
            "đau bụng": "đau bụng (đau vùng bụng)",
            "ho nhiều": "ho kéo dài",
            "sốt cao": "sốt trên 38.5°C",
            "khó thở": "khó thở (khó hô hấp)",
            "dị ứng": "phản ứng dị ứng",
        }

        for common, medical in term_mapping.items():
            text = re.sub(r"\b" + common + r"\b", medical, text)

        return text

    def _extract_medical_keywords(self, text: str) -> str:
        """
        Trích xuất từ khóa y tế quan trọng
        """
        # Tách từ
        words = text.split()

        # Lọc stopwords
        filtered_words = [w for w in words if w not in self.stopwords]

        # Tạo chuỗi keywords
        keywords = " ".join(filtered_words)

        return keywords


# Dependency
def get_message_processor() -> MessageProcessor:
    return MessageProcessor()
