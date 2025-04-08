import os
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from datetime import datetime, timezone

# Thêm thư mục gốc vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.db_manager import Base, get_db, engine, SessionLocal
from models.user import User
from models.blog import Article, Tag, Category
from models.badge import Badge, UserBadge
from api.user_routes import router as user_router
from api.middleware import get_current_user

# --- FIXTURES ---

@pytest.fixture
def test_badges(db, test_user):
    db.query(UserBadge).delete()
    db.query(Badge).delete()
    db.commit()

    badge1 = Badge(name="First Post", description="Created your first post", image_url="url1")
    badge2 = Badge(name="Popular", description="Post reached 100 views", image_url="url2")
    db.add_all([badge1, badge2])
    db.commit()

    user_badge1 = UserBadge(user_id=test_user.id, badge_id=badge1.id, earned_at=datetime.now(timezone.utc))
    user_badge2 = UserBadge(user_id=test_user.id, badge_id=badge2.id, earned_at=datetime.now(timezone.utc))
    db.add_all([user_badge1, user_badge2])
    db.commit()

    return [user_badge1, user_badge2]

# --- TESTS ---

def test_get_users(client, auth_header):
    response = client.get("/users/", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(u["username"] == "testuser" for u in data)

def test_get_user_valid(client, test_user, auth_header):
    response = client.get(f"/users/{test_user.id}", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

def test_get_user_invalid(client, auth_header):
    response = client.get("/users/9999", headers=auth_header)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_get_user_badges(client, test_user, test_badges,auth_header):
    response = client.get(f"/users/{test_user.id}/badges", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [b["name"] for b in data]
    assert "First Post" in names
    assert "Popular" in names

def test_get_user_badges_invalid(client, auth_header):
    response = client.get("/users/9999/badges", headers=auth_header)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_multiple_users(client, db, auth_header):
    users = [
        User(username="alice", email="alice@example.com", password_hash="x"),
        User(username="bob", email="bob@example.com", password_hash="y"),
    ]
    db.add_all(users)
    db.commit()

    response = client.get("/users/",headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    usernames = [user["username"] for user in data]
    assert "alice" in usernames
    assert "bob" in usernames

def test_skip_and_limit(client, db,auth_header):
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com", password_hash="x")
        for i in range(5)
    ]
    db.add_all(users)
    db.commit()

    response = client.get("/users/?skip=1&limit=2", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_all_badges(client, test_badges, auth_header):
    response = client.get("/badges", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [b["name"] for b in data]
    assert "First Post" in names
    assert "Popular" in names

def test_get_badge_by_id(client, test_badges, auth_header):
    badge = test_badges[0].badge
    response = client.get(f"/badges/{badge.id}", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["name"] == badge.name

def test_get_badge_not_found(client, auth_header):
    response = client.get("/badges/9999", headers=auth_header)
    assert response.status_code == 404
    assert response.json()["detail"] == "Badge not found"

def test_create_badge(client, db, auth_header):
    payload = {
        "name": "Helpful",
        "description": "Commented on 10 posts",
        "image_url": "https://example.com/helpful.png"
    }
    response = client.post("/badges", json=payload, headers=auth_header)
    print("Badge created:", response.json())
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]

    # ✅ Lấy badge_id từ response
    badge_id = data["id"]

    # 🔁 Truy vấn lại badge thông qua API
    get_response = client.get(f"/badges/{badge_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Helpful"


def test_award_badge_to_user(client, db, test_user, auth_header):
    badge = Badge(name="Helpful", description="Commented on 10 posts", image_url="img")
    db.add(badge)
    db.commit()
    db.refresh(badge)

    response = client.post(
        f"/users/{test_user.id}/badges/{badge.id}",
        headers=auth_header
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["badge_id"] == badge.id

def test_award_badge_to_nonexistent_user(client, db, auth_header):
    badge = Badge(name="Ghost", image_url="img")
    db.add(badge)
    db.commit()
    db.refresh(badge)

    response = client.post(
        "/users/9999/badges/{}".format(badge.id),
        headers=auth_header
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

def test_award_nonexistent_badge(client, test_user, auth_header):
    response = client.post(
        f"/users/{test_user.id}/badges/9999",
        headers=auth_header
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Badge not found"

def test_award_duplicate_badge(client, db, test_user, auth_header):
    # Tạo badge qua API
    payload = {
        "name": "Repeat",
        "description": "Duplicate test",
        "image_url": "https://example.com/repeat.png"
    }
    create_response = client.post("/badges", json=payload, headers=auth_header)
    assert create_response.status_code == 201
    badge = create_response.json()
    badge_id = badge["id"]

    # Gán badge lần 1
    response1 = client.post(f"/users/{test_user.id}/badges/{badge_id}", headers=auth_header)
    assert response1.status_code == 200

    # Gán badge lần 2 (trùng lặp)
    response2 = client.post(f"/users/{test_user.id}/badges/{badge_id}", headers=auth_header)
    assert response2.status_code == 200

    # Lấy tất cả badge của user để kiểm tra
    get_badges_response = client.get(f"/users/{test_user.id}/badges", headers=auth_header)
    assert get_badges_response.status_code == 200
    user_badges = get_badges_response.json()

    # In để kiểm tra cấu trúc trả về
    print("User badges:", user_badges)

    # Nếu không có key "badge", kiểm tra theo badge_id
    badge_count = sum(1 for b in user_badges if b["id"] == badge_id)
    assert badge_count == 1

