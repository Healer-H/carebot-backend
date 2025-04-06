# repositories/health_streak_repo.py
from sqlalchemy.orm import Session
from models.health_streak import HealthActivity, UserStreak, StreakCompletion
from datetime import date

class HealthActivityRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self):
        return self.db.query(HealthActivity).all()
    
    def get_by_id(self, activity_id: int):
        return self.db.query(HealthActivity).filter(HealthActivity.id == activity_id).first()
    
    def create(self, name: str, description: str, difficulty: str):
        activity = HealthActivity(name=name, description=description, difficulty=difficulty)
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)
        return activity

class UserStreakRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user(self, user_id: int):
        return self.db.query(UserStreak).filter(UserStreak.user_id == user_id).all()
    
    def get_by_user_and_activity(self, user_id: int, activity_id: int):
        return self.db.query(UserStreak).filter(
            UserStreak.user_id == user_id,
            UserStreak.activity_id == activity_id
        ).first()
    
    def create_or_update(self, user_id: int, activity_id: int, current_streak: int, 
                         longest_streak: int, last_completed: date):
        streak = self.get_by_user_and_activity(user_id, activity_id)
        
        if not streak:
            streak = UserStreak(
                user_id=user_id,
                activity_id=activity_id,
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_completed=last_completed
            )
            self.db.add(streak)
        else:
            streak.current_streak = current_streak
            streak.longest_streak = longest_streak
            streak.last_completed = last_completed
        
        self.db.commit()
        self.db.refresh(streak)
        return streak

class StreakCompletionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_date_range(self, user_id: int, start_date: date, end_date: date):
        return self.db.query(StreakCompletion).filter(
            StreakCompletion.user_id == user_id,
            StreakCompletion.completed_date >= start_date,
            StreakCompletion.completed_date <= end_date
        ).all()
    
    def get_by_user_and_activity_date(self, user_id: int, activity_id: int, completed_date: date):
        return self.db.query(StreakCompletion).filter(
            StreakCompletion.user_id == user_id,
            StreakCompletion.activity_id == activity_id,
            StreakCompletion.completed_date == completed_date
        ).first()
    
    def create(self, user_id: int, activity_id: int, completed_date: date):
        completion = StreakCompletion(
            user_id=user_id,
            activity_id=activity_id,
            completed_date=completed_date
        )
        self.db.add(completion)
        self.db.commit()
        self.db.refresh(completion)
        return completion