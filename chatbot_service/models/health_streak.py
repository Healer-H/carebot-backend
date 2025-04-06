# models/health_streak.py
from sqlalchemy import Column, Integer, String, Enum, Text, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from utils.db_manager import Base
from pydantic import BaseModel, validator
from typing import  Optional, Dict
from datetime import datetime, date
class HealthActivity(Base):
    __tablename__ = "health_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    difficulty = Column(Enum('easy', 'medium', 'hard'), nullable=False)
    
    # Relationships
    user_streaks = relationship("UserStreak", back_populates="activity")
    completions = relationship("StreakCompletion", back_populates="activity")

class UserStreak(Base):
    __tablename__ = "user_streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("health_activities.id"), nullable=False)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_completed = Column(DateTime, nullable=True)
    
    # Relationships
    activity = relationship("HealthActivity", back_populates="user_streaks")
    user = relationship("User")

class StreakCompletion(Base):
    __tablename__ = "streak_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("health_activities.id"), nullable=False)
    completed_date = Column(Date, nullable=False)
    
    # Relationships
    activity = relationship("HealthActivity", back_populates="completions")
    user = relationship("User")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'activity_id', 'completed_date', name='unique_completion'),
    )
    

# Health Activity schemas
class HealthActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty: str
    
    @validator('difficulty')
    def valid_difficulty(cls, v):
        allowed = ['easy', 'medium', 'hard']
        if v.lower() not in allowed:
            raise ValueError(f'Difficulty must be one of: {", ".join(allowed)}')
        return v.lower()

class HealthActivityCreate(HealthActivityBase):
    pass

class HealthActivityResponse(HealthActivityBase):
    id: int
    
    class Config:
        orm_mode = True

# Streak schemas
class UserStreakBase(BaseModel):
    activity_id: int

class UserStreakCreate(UserStreakBase):
    pass

class UserStreakResponse(BaseModel):
    id: int
    user_id: int
    activity_id: int
    current_streak: int
    longest_streak: int
    last_completed: Optional[datetime]
    activity: HealthActivityResponse
    
    class Config:
        orm_mode = True

class StreakCompletionCreate(BaseModel):
    activity_id: int
    completed_date: Optional[date] = None

class StreakCompletionResponse(BaseModel):
    id: int
    user_id: int
    activity_id: int
    completed_date: date
    activity: HealthActivityResponse
    
    class Config:
        orm_mode = True

class StreakStatsResponse(BaseModel):
    by_date: Dict[str, int]
    by_activity: Dict[str, int]
    total_completions: int
    days_with_completions: int
    period_days: int
