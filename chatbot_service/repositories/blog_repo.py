# repositories/blog_repo.py
from sqlalchemy.orm import Session
from models.blog import Article, Category, Tag
from typing import List

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self):
        return self.db.query(Category).all()
    
    def get_by_id(self, category_id: int):
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_name(self, name: str):
        return self.db.query(Category).filter(Category.name == name).first()
    
    def create(self, name: str, description: str = None):
        category = Category(name=name, description=description)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

class TagRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self):
        return self.db.query(Tag).all()
    
    def get_by_id(self, tag_id: int):
        return self.db.query(Tag).filter(Tag.id == tag_id).first()
    
    def get_by_name(self, name: str):
        return self.db.query(Tag).filter(Tag.name == name).first()
    
    def create(self, name: str):
        tag = Tag(name=name)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag
    
    def get_or_create(self, name: str):
        tag = self.get_by_name(name)
        if not tag:
            tag = self.create(name)
        return tag

class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 10):
        return self.db.query(Article).offset(skip).limit(limit).all()
    
    def get_by_id(self, article_id: int):
        return self.db.query(Article).filter(Article.id == article_id).first()
    
    def get_by_category(self, category_id: int, skip: int = 0, limit: int = 10):
        return self.db.query(Article).filter(
            Article.category_id == category_id
        ).offset(skip).limit(limit).all()
    
    def get_by_tag(self, tag_name: str, skip: int = 0, limit: int = 10):
        return self.db.query(Article).join(Article.tags).filter(
            Tag.name == tag_name
        ).offset(skip).limit(limit).all()
    
    def create(self, title: str, content: str, author_id: int, category_id: int, 
               source: str = None, tags: List[Tag] = None):
        article = Article(
            title=title,
            content=content,
            author_id=author_id,
            category_id=category_id,
            source=source
        )
        
        if tags:
            article.tags = tags
            
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article