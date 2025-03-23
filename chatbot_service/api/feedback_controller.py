from fastapi import APIRouter, Depends, HTTPException, Body, status
from uuid import UUID

from repositories.feedback_repo import FeedbackRepository, get_feedback_repository
from models.message_feedback import MessageFeedback, FeedbackResponse
from api.middleware import get_current_user

router = APIRouter()

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: MessageFeedback = Body(...),
    feedback_repo: FeedbackRepository = Depends(get_feedback_repository),
    current_user: dict = Depends(get_current_user)
):
    """
    Gửi đánh giá về tin nhắn từ chatbot
    """
    # Xác nhận người dùng
    feedback.user_id = current_user["user_id"]
    
    # Kiểm tra rating
    if feedback.rating < 1 or feedback.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )
    
    # Lưu feedback
    feedback_id = await feedback_repo.save_feedback(feedback)
    
    return FeedbackResponse(
        success=True,
        message="Feedback recorded successfully"
    )