from typing import Tuple
import logging
import re
from fastapi import Depends

from models.chat_message import ChatMessage
from config import settings

logger = logging.getLogger("safety_guardrails")


class SafetyGuardrails:
    def __init__(self, max_risk_level: int = 3):
        self.max_risk_level = max_risk_level
        self.disclaimer_template = settings.DISCLAIMER_TEMPLATE

        # Từ khóa có rủi ro cao
        self.high_risk_keywords = [
            "tự tử",
            "giết",
            "đau khổ",
            "thuốc bất hợp pháp",
            "ma túy",
            "vũ khí",
            "bom",
            "tấn công",
            "nguy hiểm",
            "cách chế tạo",
        ]

        # Từ khóa y tế cần disclaimer
        self.medical_keywords = [
            "điều trị",
            "thuốc",
            "liều lượng",
            "tác dụng phụ",
            "bệnh",
            "triệu chứng",
            "chẩn đoán",
            "nguyên nhân",
            "phòng ngừa",
        ]

    async def check_input_safety(self, message: ChatMessage) -> Tuple[bool, int, str]:
        """
        Kiểm tra an toàn nội dung đầu vào
        Returns: (is_safe, risk_level, reason)
        """
        content = message.content.lower()

        # Kiểm tra từ khóa có rủi ro cao
        for keyword in self.high_risk_keywords:
            if keyword in content:
                risk_level = 4
                if risk_level > self.max_risk_level:
                    return (
                        False,
                        risk_level,
                        f"Nội dung chứa từ khóa có rủi ro cao: {keyword}",
                    )
                else:
                    return True, risk_level, ""

        # Kiểm tra nội dung quá dài
        if len(content) > 2000:
            return False, 2, "Nội dung vượt quá độ dài cho phép"

        # Kiểm tra yêu cầu không phù hợp
        if re.search(
            r"(làm thế nào|cách) (để|tạo ra|chế tạo|sản xuất) (vũ khí|bom|chất độc|thuốc)",
            content,
        ):
            return False, 5, "Yêu cầu không phù hợp về cách tạo ra vật nguy hiểm"

        return True, 1, ""

    async def check_output_safety(self, content: str) -> Tuple[bool, int, str]:
        """
        Kiểm tra an toàn nội dung đầu ra
        Returns: (is_safe, risk_level, reason)
        """
        content_lower = content.lower()

        # Kiểm tra nội dung chứa hướng dẫn nguy hiểm
        if re.search(
            r"(cách|hướng dẫn|bước) (tạo ra|chế tạo|sản xuất) (vũ khí|bom|chất độc|thuốc)",
            content_lower,
        ):
            return False, 5, "Phản hồi chứa hướng dẫn tạo vật nguy hiểm"

        # Kiểm tra nội dung chứa lời khuyên y tế không đảm bảo
        if "tôi đảm bảo" in content_lower and any(
            kw in content_lower for kw in self.medical_keywords
        ):
            return False, 4, "Phản hồi đưa ra đảm bảo y tế không phù hợp"

        # Kiểm tra nội dung khuyên dừng điều trị
        if re.search(
            r"(nên|hãy) (dừng|ngừng|bỏ) (điều trị|thuốc|liệu pháp)", content_lower
        ):
            return False, 4, "Phản hồi khuyên dừng điều trị y tế"

        return True, 1, ""

    async def add_medical_disclaimer(self, content: str, risk_level: int = 0) -> str:
        """
        Thêm disclaimer y tế vào nội dung
        """
        # Kiểm tra xem nội dung có liên quan đến y tế không
        is_medical_content = any(
            keyword in content.lower() for keyword in self.medical_keywords
        )

        # Nếu là nội dung y tế hoặc có rủi ro, thêm disclaimer
        if is_medical_content or risk_level > 1:
            if not content.endswith("\n"):
                content += "\n\n"
            else:
                content += "\n"

            content += self.disclaimer_template

        return content

    async def classify_risk_level(self, content: str) -> int:
        """
        Phân loại mức độ rủi ro của nội dung từ 1-5
        """
        content_lower = content.lower()

        # Mức 5: Nguy hiểm cao
        if any(
            re.search(rf"\b{re.escape(kw)}\b", content_lower)
            for kw in ["tự tử", "giết người", "bom"]
        ):
            return 5

        # Mức 4: Nguy cơ cao
        if any(kw in content_lower for kw in ["ma túy", "vũ khí", "chế tạo"]):
            return 4

        # Mức 3: Nguy cơ trung bình
        if any(
            re.search(rf"\b{re.escape(kw)}\b", content_lower)
            for kw in ["liều lượng", "tác dụng phụ", "ngừng thuốc"]
        ):
            return 3

        # Mức 2: Nguy cơ thấp
        if any(kw in content_lower for kw in ["điều trị", "bệnh", "triệu chứng"]):
            return 2

        # Mức 1: Không có nguy cơ
        return 1


# Dependency
def get_safety_guardrails() -> SafetyGuardrails:
    return SafetyGuardrails(max_risk_level=settings.MAX_RISK_LEVEL)
