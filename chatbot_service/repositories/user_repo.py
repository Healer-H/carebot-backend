# repositories/user_repo.py
from sqlalchemy.orm import Session
from models.user import User
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, username: str, email: str, password_hash: str):
        db_user = User(username=username, email=email, password_hash=password_hash)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    def update(self, user: User) -> Optional[User]:
        """Cập nhật thông tin người dùng"""
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error: {e}")
            return None

    def delete(self, user: User) -> bool:
        """Xóa người dùng"""
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error: {e}")
            return False