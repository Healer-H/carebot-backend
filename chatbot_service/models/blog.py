# models/blog.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from utils.db_manager import Base
from pydantic import BaseModel
from typing import  Optional, List
from datetime import datetime
# Association table for article-tag many-to-many relationship
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    articles = relationship("Article", back_populates="category")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    
    # Relationships
    articles = relationship("Article", secondary=article_tags, back_populates="tags")

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    source = Column(String(255))
    published_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    author = relationship("User")
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")
    
    
    
# Blog schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    
    class Config:
        orm_mode = True

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    
    class Config:
        orm_mode = True

class ArticleBase(BaseModel):
    title: str
    content: str
    category_id: int
    author_id: Optional[int] = None
    source: Optional[str] = None

class ArticleCreate(ArticleBase):
    tags: Optional[List[int]] = []

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    tags: Optional[List[int]] = None

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    category_id: int
    author_id: Optional[int] = None
    source: Optional[str] = None
    published_at: datetime
    updated_at: datetime
    category: CategoryResponse
    tags: List[TagResponse] = []
    
    class Config:
        orm_mode = True