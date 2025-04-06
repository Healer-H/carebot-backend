# api/streak_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from utils.db_manager import get_db
from models.health_streak import (
    HealthActivityResponse, HealthActivityCreate,
    UserStreakResponse, StreakCompletionCreate, StreakCompletionResponse,
    StreakStatsResponse
)
from repositories.health_streak_repo import (
    HealthActivityRepository, UserStreakRepository, StreakCompletionRepository
)
from api.middleware import get_current_user

router = APIRouter(tags=["Health Streaks"])

# Health Activities endpoints
@router.get("/activities", response_model=List[HealthActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    """
    Get all health activities
    """
    activity_repo = HealthActivityRepository(db)
    return activity_repo.get_all()

@router.get("/activities/{activity_id}", response_model=HealthActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    """
    Get health activity by ID
    """
    activity_repo = HealthActivityRepository(db)
    activity = activity_repo.get_by_id(activity_id)
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return activity

@router.post("/activities", response_model=HealthActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity_data: HealthActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new health activity (admin only)
    """
    # TODO: Implement admin check here
    
    activity_repo = HealthActivityRepository(db)
    
    activity = activity_repo.create(
        name=activity_data.name,
        description=activity_data.description,
        difficulty=activity_data.difficulty
    )
    
    return activity

# User Streaks endpoints
@router.get("/streaks", response_model=List[UserStreakResponse])
def get_user_streaks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all streaks for the current user
    """
    streak_repo = UserStreakRepository(db)
    return streak_repo.get_by_user(int(current_user["sub"]))

@router.get("/streaks/{activity_id}", response_model=UserStreakResponse)
def get_user_streak(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific streak for the current user
    """
    streak_repo = UserStreakRepository(db)
    streak = streak_repo.get_by_user_and_activity(
        user_id=int(current_user["sub"]),
        activity_id=activity_id
    )
    
    if not streak:
        # Create a new streak if it doesn't exist
        streak = streak_repo.create_or_update(
            user_id=int(current_user["sub"]),
            activity_id=activity_id
        )
    
    return streak

# Streak Completions endpoints
@router.post("/completions", response_model=StreakCompletionResponse, status_code=status.HTTP_201_CREATED)
def complete_activity(
    completion_data: StreakCompletionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark an activity as completed
    """
    # Verify activity exists
    activity_repo = HealthActivityRepository(db)
    activity = activity_repo.get_by_id(completion_data.activity_id)
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Record completion
    completion_repo = StreakCompletionRepository(db)
    completion = completion_repo.create(
        user_id=int(current_user["sub"]),
        activity_id=completion_data.activity_id,
        completion_date=completion_data.completed_date
    )
    
    return completion

@router.get("/completions", response_model=List[StreakCompletionResponse])
def get_completions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity completions for the current user
    """
    completion_repo = StreakCompletionRepository(db)
    
    if not start_date:
        # Default to last 7 days
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
    elif not end_date:
        end_date = start_date
    
    return completion_repo.get_by_user_and_date(
        user_id=int(current_user["sub"]),
        start_date=start_date,
        end_date=end_date
    )

@router.get("/stats", response_model=StreakStatsResponse)
def get_streak_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get streak statistics for the current user
    """
    completion_repo = StreakCompletionRepository(db)
    
    return completion_repo.get_stats(
        user_id=int(current_user["sub"]),
        days=days
    )