from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.router import router as api_router
# from api.middleware import auth_middleware
from repositories.chat_history_repo import ChatHistoryRepository
from repositories.vector_db_repo import VectorDBRepository
from services.vector_db_manager import VectorDatabaseManager
from services.llm_client import LLMClient
from config import Settings
from utils.log_manager import LogManager
import logging

app = FastAPI(title="CareBot Chatbot Service")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router
app.include_router(api_router, prefix="/api")

# Khởi tạo logging
LogManager.setup_logging(log_file="logs/chatbot_service.log")
logger = logging.getLogger("main")
# logging.config.dictConfig({
#     log_file="logs/chatbot_service.log"
# })

@app.on_event("startup")
async def startup_event():
    # Khởi tạo kết nối database    
    # Khởi tạo các dịch vụ
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Đóng kết nối database
    # Dọn dẹp tài nguyên
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)