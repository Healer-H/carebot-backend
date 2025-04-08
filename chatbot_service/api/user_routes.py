#api/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from utils.db_manager import get_db
from models.user import User
from repositories.user_repo import UserRepository
from repositories.badge_repo import BadgeRepository, UserBadgeRepository
from models.badge import UserBadge,UserBadgeResponse
from api.middleware import get_current_user

router = APIRouter()

@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of users (requires authentication)
    """
    user_repo = UserRepository(db)
    users = user_repo.get_all(skip, limit)
    
    # Return user data without sensitive information
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user by ID (requires authentication)
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }

@router.get("/{user_id}/badges")
async def get_user_badges(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get badges earned by user (requires authentication)
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    badge_repo = BadgeRepository(db)
    user_badge_repo = UserBadgeRepository(db)
    
    user_badges = user_badge_repo.get_by_user(user_id)
    
    return [
        {
            "id": user_badge.badge.id,
            "name": user_badge.badge.name,
            "description": user_badge.badge.description,
            "image_url": user_badge.badge.image_url,
            "earned_at": user_badge.earned_at.isoformat()
        }
        for user_badge in user_badges
    ]
    
    
@router.post("/{user_id}/badges/{badge_id}", response_model=UserBadgeResponse)
def award_badge(
    user_id: int,
    badge_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Award a badge to a user (admin only)
    """
    # TODO: Implement admin check here
    
    # Verify badge exists
    badge_repo = BadgeRepository(db)
    badge = badge_repo.get_by_id(badge_id)
    
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge not found"
        )
    
    # Verify user exists
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Award badge
    user_badge_repo = UserBadgeRepository(db)
    user_badge = user_badge_repo.award_badge(user_id, badge_id)
    
    return user_badge