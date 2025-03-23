from typing import Tuple
import re
import logging
from fastapi import Depends

logger = logging.getLogger("emergency_detector")

class EmergencyDetector:
    def __init__(self):
        # Từ khóa khẩn cấp
        self.emergency_keywords = {
            "cardiac": [
                "đau tim", "nhồi máu cơ tim", "đau thắt ngực", 
                "khó thở dữ dội", "đau ngực dữ dội", "tức ngực"
            ],
            "stroke": [
                "đột quỵ", "tê liệt nửa người", "méo miệng", 
                "nói ngọng", "đột ngột", "nhìn mờ"
            ],
            "bleeding": [
                "chảy máu dữ dội", "chảy máu không ngừng",
                "chảy máu nhiều", "mất máu"
            ],
            "shock": [
                "sốc phản vệ", "khó thở cấp", "ngứa toàn thân",
                "nổi mề đay đột ngột", "phù nề"
            ],
            "suicide": [
                "tự tử", "muốn chết", "không muốn sống",
                "kết thúc cuộc đời", "kết liễu"
            ]
        }
        
        # Các cụm từ khẩn cấp
        self.emergency_patterns = [
            r"(khó thở|ngạt thở) (dữ dội|nghiêm trọng|không thở được)",
            r"(đau|tức) ngực (dữ dội|không chịu nổi|quá mức)",
            r"bất tỉnh|ngất xỉu|hôn mê",
            r"(chảy máu|xuất huyết) (nhiều|nghiêm trọng|không ngừng)",
            r"gãy xương hở|chấn thương đầu nặng|ngã từ trên cao"
        ]
    
    async def detect_emergency(self, content: str) -> Tuple[bool, str]:
        """
        Phát hiện tình huống khẩn cấp từ nội dung
        Returns: (is_emergency, emergency_type)
        """
        content_lower = content.lower()
        
        # Kiểm tra các từ khóa khẩn cấp
        for emergency_type, keywords in self.emergency_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    logger.warning(f"Emergency detected: {emergency_type} - Keyword: {keyword}")
                    return True, emergency_type
        
        # Kiểm tra các mẫu câu khẩn cấp
        for pattern in self.emergency_patterns:
            if re.search(pattern, content_lower):
                logger.warning(f"Emergency detected with pattern: {pattern}")
                return True, "general_emergency"
        
        # Kiểm tra các cụm từ khẩn cấp kết hợp
        if (("đau" in content_lower and "dữ dội" in content_lower) or
            ("cấp cứu" in content_lower) or
            ("gấp" in content_lower and "ngay" in content_lower)):
            logger.warning("Emergency detected with combined patterns")
            return True, "general_emergency"
        
        return False, ""

# Dependency
def get_emergency_detector() -> EmergencyDetector:
    return EmergencyDetector()