import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

class LogManager:
    @staticmethod
    def setup_logging(log_level=logging.INFO, log_file=None):
        """
        Thiết lập logging cho ứng dụng
        """
        # Tạo thư mục logs nếu chưa tồn tại
        if log_file and not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        
        # Định dạng log
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # Định dạng bộ xử lý
        formatter = logging.Formatter(log_format, date_format)
        
        # Bộ xử lý console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Bộ xử lý file nếu có
        handlers = [console_handler]
        if log_file:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
            
        # Cấu hình logging
        logging.basicConfig(
            level=log_level,
            handlers=handlers
        )
        
        # Thiết lập các logger cho thư viện bên thứ ba
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("motor").setLevel(logging.WARNING)