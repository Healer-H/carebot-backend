# services/badge_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from repositories.badge_repo import BadgeRepository, UserBadgeRepository
from repositories.health_streak_repo import UserStreakRepository, StreakCompletionRepository
from models.badge import Badge

class BadgeService:
    """
    Service to check and award badges based on user activities
    """
    def __init__(self, db: Session):
        self.db = db
        self.badge_repo = BadgeRepository(db)
        self.user_badge_repo = UserBadgeRepository(db)
        self.streak_repo = UserStreakRepository(db)
        self.completion_repo = StreakCompletionRepository(db)
    
    def check_achievements(self, user_id: int) -> List[Badge]:
        """
        Check user achievements and award badges accordingly
        Returns list of newly awarded badges
        """
        awarded_badges = []
        
        # Get all available badges
        all_badges = self.badge_repo.get