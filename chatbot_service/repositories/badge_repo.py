# repositories/badge_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional
from models.badge import Badge, UserBadge

class BadgeRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Badge]:
        """Get all badges"""
        return self.db.query(Badge).all()
    
    def get_by_id(self, badge_id: int) -> Optional[Badge]:
        """Get badge by ID"""
        return self.db.query(Badge).filter(Badge.id == badge_id).first()
    
    def create(self, name: str, description: str = None, image_url: str = None) -> Badge:
        """Create a new badge"""
        badge = Badge(
            name=name,
            description=description,
            image_url=image_url
        )
        
        self.db.add(badge)
        self.db.commit()
        self.db.refresh(badge)
        
        return badge

class UserBadgeRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user(self, user_id: int) -> List[UserBadge]:
        """Get all badges for a user"""
        return (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id)
            .all()
        )
    
    def get_by_user_and_badge(self, user_id: int, badge_id: int) -> Optional[UserBadge]:
        """Check if user has a specific badge"""
        return (
            self.db.query(UserBadge)
            .filter(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge_id
            )
            .first()
        )
    
    def award_badge(self, user_id: int, badge_id: int) -> UserBadge:
        """Award a badge to a user"""
        # Check if user already has this badge
        existing = self.get_by_user_and_badge(user_id, badge_id)
        if existing:
            return existing
        
        # Award new badge
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id
        )
        
        self.db.add(user_badge)
        self.db.commit()
        self.db.refresh(user_badge)
        
        return user_badge