from typing import Tuple
import re
from datetime import datetime

class Validators:
    @staticmethod
    def validate_message_content(content: str) -> Tuple[bool, str]:
        """
        Kiểm tra nội dung tin nhắn
        """
        if not content or content.strip() == "":
            return False, "Nội dung không được để trống"
            
        if len(content) > 2000:
            return False, "Nội dung không được vượt quá 2000 ký tự"
            
        return True, ""
    
    @staticmethod
    def validate_feedback_rating(rating: int) -> Tuple[bool, str]:
        """
        Kiểm tra đánh giá
        """
        if rating < 1 or rating > 5:
            return False, "Đánh giá phải từ 1 đến 5"
            
        return True, ""
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        Kiểm tra URL
        """
        if not url:
            return True, ""  # URL không bắt buộc
            
        url_pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
        if not re.match(url_pattern, url):
            return False, "URL không hợp lệ"
            
        return True, ""
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, datetime, str]:
        """
        Kiểm tra định dạng ngày
        """
        if not date_str:
            return True, None, ""
            
        try:
            date_format = "%Y-%m-%d"
            date_obj = datetime.strptime(date_str, date_format)
            return True, date_obj, ""
        except ValueError:
            return False, None, "Định dạng ngày không hợp lệ (YYYY-MM-DD)"