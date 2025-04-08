import os, sys, pytest, jwt
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

# Thêm project root vào sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_manager import Base, get_db, engine, SessionLocal
from models.user import User
from models.blog import Article, Tag, Category
from models.badge import Badge, UserBadge
from models.health_streak import HealthActivity, UserStreak, StreakCompletion
from api.blog_routes import router as blog_router
from api.user_routes import router as user_router
from api.badge_routes import router as badge_router
from api.streak_routes import router as streak_router
from api.middleware import get_current_user
from config import settings

SECRET_KEY = settings.TOKEN_SECRET_KEY
ALGORITHM = "HS256"

# ------------------- App Test ---------------------
def create_test_app():
    app = FastAPI()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # override thông minh để test cả auth/unauth
    def override_get_current_user(request: Request):
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

        try:
            token = auth.split(" ")[1]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = int(payload["sub"])
            return {
                "id": user_id,
                "username": "testuser",
                "email": "test@example.com"
            }
        except Exception:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    app.include_router(user_router, prefix="/users", tags=["Users"])
    app.include_router(streak_router, prefix="/streaks", tags=["Health Streaks"])
    app.include_router(badge_router, prefix="/badges", tags=["Badges"])
    app.include_router(blog_router, prefix="/blog", tags=["Blog"])
    return app

# ------------------- Fixtures ---------------------

@pytest.fixture(scope="session")
def app():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app = create_test_app()
    yield app
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        tables = [
            "streak_completions", "user_streaks", "health_activities",
            "user_badges", "badges", "articles_tags",
            "articles", "categories", "tags", "users"
        ]
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def test_user(db):
    db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    db.execute(text("DELETE FROM user_badges"))
    db.execute(text("DELETE FROM badges"))
    db.execute(text("DELETE FROM articles"))
    db.execute(text("DELETE FROM users"))
    db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    db.commit()

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_header(test_user):
    payload = {
        "sub": str(test_user.id),  # Bắt buộc phải có 'sub'
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}

    
