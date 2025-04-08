# api/badge_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from utils.db_manager import get_db
from models.badge import BadgeResponse, BadgeCreate, UserBadgeResponse
from repositories.badge_repo import BadgeRepository, UserBadgeRepository
from api.middleware import get_current_user
from repositories.user_repo import UserRepository

router = APIRouter(tags=["Badges"])

@router.get("/", response_model=List[BadgeResponse])
def get_badges(db: Session = Depends(get_db)):
    """
    Get all available badges
    """
    badge_repo = BadgeRepository(db)
    return badge_repo.get_all()

@router.get("/{badge_id}", response_model=BadgeResponse)
def get_badge(badge_id: int, db: Session = Depends(get_db)):
    """
    Get badge by ID
    """
    badge_repo = BadgeRepository(db)
    badge = badge_repo.get_by_id(badge_id)
    
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge not found"
        )
    
    return badge

@router.post("/", response_model=BadgeResponse, status_code=status.HTTP_201_CREATED)
def create_badge(
    badge_data: BadgeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new badge (admin only)
    """
    # TODO: Implement admin check here
    
    badge_repo = BadgeRepository(db)
    
    badge = badge_repo.create(
        name=badge_data.name,
        description=badge_data.description,
        image_url=badge_data.image_url
    )
    
    return badge
