# api/blog_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from utils.db_manager import get_db
from models.blog import (
    CategoryResponse, CategoryCreate,
    TagResponse, TagCreate,
    ArticleResponse, ArticleCreate, ArticleUpdate
)
from repositories.blog_repo import CategoryRepository, TagRepository, ArticleRepository
from api.middleware import get_current_user

router = APIRouter(tags=["Blog"])

# Categories endpoints
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """
    Get all blog categories
    """
    category_repo = CategoryRepository(db)
    return category_repo.get_all()

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new blog category (admin only)
    """
    # TODO: Implement admin check here
    
    category_repo = CategoryRepository(db)
    
    category = category_repo.create(
        name=category_data.name,
        description=category_data.description
    )
    
    return category

# Tags endpoints
@router.get("/tags", response_model=List[TagResponse])
def get_tags(db: Session = Depends(get_db)):
    """
    Get all blog tags
    """
    tag_repo = TagRepository(db)
    return tag_repo.get_all()

@router.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new blog tag (admin only)
    """
    # TODO: Implement admin check here
    
    tag_repo = TagRepository(db)
    
    tag = tag_repo.create(name=tag_data.name)
    
    return tag

# Articles endpoints
@router.get("/articles", response_model=List[ArticleResponse])
def get_articles(
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get blog articles with optional filtering
    """
    article_repo = ArticleRepository(db)
    
    if category_id:
        return article_repo.get_by_category(
            category_id=category_id,
            limit=limit,
            offset=offset
        )
    elif tag_id:
        return article_repo.get_by_tag(
            tag_id=tag_id,
            limit=limit,
            offset=offset
        )
    else:
        return article_repo.get_all(limit=limit, offset=offset)

@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """
    Get blog article by ID
    """
    article_repo = ArticleRepository(db)
    article = article_repo.get_by_id(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    return article

@router.post("/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new blog article
    """
    # Verify category exists
    category_repo = CategoryRepository(db)
    category = category_repo.get_by_id(article_data.category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Create article
    article_repo = ArticleRepository(db)
    
    # If no author_id is provided, use the current user
    if article_data.author_id is None:
        author_id = article_data.author_id
    
    article = article_repo.create(
        title=article_data.title,
        content=article_data.content,
        category_id=article_data.category_id,
        author_id=author_id,
        source=article_data.source,
        tags=article_data.tags
    )
    
    return article

@router.put("/articles/{article_id}", response_model=ArticleResponse)
def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a blog article
    """
    article_repo = ArticleRepository(db)
    article = article_repo.get_by_id(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Check if user is the author or admin
    if article.author_id != int(current_user["sub"]):
        # TODO: Implement admin check here
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this article"
        )
    
    # Convert pydantic model to dict, filtering out None values
    update_data = {k: v for k, v in article_data.dict().items() if v is not None}
    
    updated_article = article_repo.update(article_id, **update_data)
    
    return updated_article

@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a blog article
    """
    # TODO: Implement article deletion in repository
    pass