# repositories/health_streak_repo.py
from sqlalchemy.orm import Session
from models.health_streak import HealthActivity, UserStreak, StreakCompletion
from datetime import date,timedelta
from collections import defaultdict
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
    
    def create_or_update(self, user_id: int, activity_id: int):
        streak = self.get_by_user_and_activity(user_id, activity_id)

        today = date.today()
        
        # Tìm completion hôm qua
        yesterday = today - timedelta(days=1)
        completion_repo = StreakCompletionRepository(self.db)
        did_yesterday = completion_repo.get_by_user_and_activity_date(user_id, activity_id, yesterday)

        if not streak:
            # Chưa có streak thì tạo mới
            current_streak = 1
            longest_streak = 1
        else:
            # Đã có streak → tính tiếp
            if streak.last_completed == yesterday:
                current_streak = streak.current_streak + 1
            elif streak.last_completed == today:
                current_streak = streak.current_streak  # đã hoàn thành hôm nay
            else:
                current_streak = 1  # reset chuỗi

            longest_streak = max(streak.longest_streak, current_streak)

        if not streak:
            streak = UserStreak(
                user_id=user_id,
                activity_id=activity_id,
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_completed=today
            )
            self.db.add(streak)
        else:
            streak.current_streak = current_streak
            streak.longest_streak = longest_streak
            streak.last_completed = today

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
    def get_stats(self, user_id: int, days: int):
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        completions = self.db.query(StreakCompletion).filter(
            StreakCompletion.user_id == user_id,
            StreakCompletion.completed_date >= start_date,
            StreakCompletion.completed_date <= end_date
        ).all()

        # Tính toán các trường cần thiết
        total_completions = len(completions)

        by_date = defaultdict(int)
        by_activity = defaultdict(int)
        dates_set = set()

        for c in completions:
            date_str = c.completed_date.isoformat()
            by_date[date_str] += 1
            by_activity[str(c.activity_id)] += 1
            dates_set.add(c.completed_date)

        return {
            "total_completions": total_completions,
            "by_date": dict(by_date),
            "by_activity": dict(by_activity),
            "days_with_completions": len(dates_set),
            "period_days": days
        }

