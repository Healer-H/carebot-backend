import os
import sys
import pytest
import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import text
# Thêm thư mục gốc vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.db_manager import Base, get_db, engine
from models.blog import Category, Tag, Article
from models.user import User
from config import settings

SECRET_KEY = settings.TOKEN_SECRET_KEY
ALGORITHM = "HS256"

@pytest.fixture(scope="function")
def mock_data(db):
    data = {}

    user = db.query(User).filter_by(username="user").first()
    if not user:
        user = User(username="user", email="user@test.com", password_hash="hash")
        db.add(user)
        db.commit()
        db.refresh(user)
    data["user"] = user

    category = db.query(Category).filter_by(name="Cat 1").first()
    if not category:
        category = Category(name="Cat 1", description="Desc")
        db.add(category)
        db.commit()
        db.refresh(category)
    data["category"] = category

    tag = db.query(Tag).filter_by(name="tag1").first()
    if not tag:
        tag = Tag(name="tag1")
        db.add(tag)
        db.commit()
        db.refresh(tag)
    data["tag"] = tag

    article = db.query(Article).filter_by(title="Article 1").first()
    if not article:
        article = Article(
            title="Article 1",
            content="Content",
            author_id=user.id,
            category_id=category.id,
            published_at=datetime.now(),
            updated_at=datetime.now()
        )
        article.tags.append(tag)
        db.add(article)
        db.commit()
        db.refresh(article)
    data["article"] = article

    return data

def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ---------- TESTS ----------

def test_get_categories(client, mock_data):
    res = client.get("/blog/categories")
    assert res.status_code == 200
    assert any(cat["name"] == "Cat 1" for cat in res.json())

def test_create_category_unauth(client):
    res = client.post("/blog/categories", json={"name": "Cat 2", "description": "Desc"})
    assert res.status_code == 403

def test_create_category_auth(client, mock_data):
    token = create_token(mock_data["user"].id)
    res = client.post("/blog/categories", json={
        "name": f"Cat {datetime.now().timestamp()}",
        "description": "New"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

def test_get_tags(client, mock_data):
    res = client.get("/blog/tags")
    assert res.status_code == 200
    assert any(tag["name"] == "tag1" for tag in res.json())

def test_create_tag_unauth(client):
    res = client.post("/blog/tags", json={"name": "tag2"})
    assert res.status_code == 403

def test_create_tag_auth(client, mock_data):
    token = create_token(mock_data["user"].id)
    res = client.post("/blog/tags", json={
        "name": f"tag_{datetime.now().timestamp()}"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201

def test_get_articles(client, mock_data):
    res = client.get("/blog/articles")
    assert res.status_code == 200
    assert any(article["title"] == "Article 1" for article in res.json())

def test_get_article_by_id(client, mock_data):
    res = client.get(f"/blog/articles/{mock_data['article'].id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Article 1"

def test_create_article_auth(client, db, test_user, auth_header):
    # Tạo category trước
    category = Category(name="Tech", description="Tech stuff")
    db.add(category)
    db.commit()
    db.refresh(category)

    # Gửi request tạo bài viết
    response = client.post(
        "/blog/articles",
        headers=auth_header,
        json={
            "title": "AI is cool",
            "content": "Let's talk about it",
            "category_id": category.id,
            "tag_ids": []
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "AI is cool"
    assert data["category"]["id"] == category.id




