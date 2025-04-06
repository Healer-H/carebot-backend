# models/badge.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from utils.db_manager import Base
from pydantic import BaseModel
from typing import  Optional
from datetime import datetime

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    image_url = Column(String(255))

class UserBadge(Base):
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=func.now())
    
    # Relationships
    badge = relationship("Badge")
    user = relationship("User")
    

# Badge schemas
class BadgeBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class BadgeCreate(BadgeBase):
    pass

class BadgeResponse(BadgeBase):
    id: int
    
    class Config:
        orm_mode = True

class UserBadgeResponse(BaseModel):
    id: int
    user_id: int
    badge_id: int
    earned_at: datetime
    badge: BadgeResponse
    
    class Config:
        orm_mode = True

