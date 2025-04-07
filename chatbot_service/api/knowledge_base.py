from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from repositories.knowledge_base import DocumentRepository
from services.rag import RAGService

router = APIRouter()

# Request and response models


class DocumentCreate(BaseModel):
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Content of the document")
    metadata: Optional[str] = Field(
        None, description="Optional metadata as JSON string")
    source: Optional[str] = Field(None, description="Source of the document")


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(
        None, description="Updated title of the document")
    content: Optional[str] = Field(
        None, description="Updated content of the document")
    metadata: Optional[str] = Field(
        None, description="Updated metadata as JSON string")
    source: Optional[str] = Field(
        None, description="Updated source of the document")


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    metadata: Optional[str] = None
    source: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    """Create a new document in the knowledge base"""
    # Create document in database
    doc = DocumentRepository.create_document(
        db=db,
        title=document.title,
        content=document.content,
        doc_metadata=document.metadata,
        source=document.source
    )

    # Index the document for RAG
    RAGService.index_document(db, doc.id, doc.content)

    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content,
        "metadata": doc.doc_metadata,
        "source": doc.source,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }


@router.get("/documents", response_model=DocumentListResponse)
def get_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all documents with pagination"""
    documents = DocumentRepository.get_all_documents(db, skip, limit)

    return {
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "content": doc.content,
                "metadata": doc.doc_metadata,
                "source": doc.source,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
            }
            for doc in documents
        ],
        "total": len(documents)
    }


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a document by ID"""
    document = DocumentRepository.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "metadata": document.doc_metadata,
        "source": document.source,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat() if document.updated_at else None
    }


@router.put("/documents/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, document: DocumentUpdate, db: Session = Depends(get_db)):
    """Update a document"""
    # Check if document exists
    existing_document = DocumentRepository.get_document_by_id(db, document_id)
    if not existing_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    # Prepare update data
    update_data = {}
    if document.title is not None:
        update_data["title"] = document.title
    if document.content is not None:
        update_data["content"] = document.content
    if document.metadata is not None:
        update_data["doc_metadata"] = document.metadata
    if document.source is not None:
        update_data["source"] = document.source

    # Update document
    updated_document = DocumentRepository.update_document(
        db, document_id, update_data)

    # Reindex document if content was updated
    if document.content is not None:
        RAGService.index_document(db, document_id, updated_document.content)

    return {
        "id": updated_document.id,
        "title": updated_document.title,
        "content": updated_document.content,
        "metadata": updated_document.doc_metadata,
        "source": updated_document.source,
        "created_at": updated_document.created_at.isoformat(),
        "updated_at": updated_document.updated_at.isoformat() if updated_document.updated_at else None
    }


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    success = DocumentRepository.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )
    return None
