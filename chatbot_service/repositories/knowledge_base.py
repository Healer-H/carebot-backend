from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.sql.expression import func

from models.knowledge_base import Document, DocumentChunk


class DocumentRepository:
    """Repository for document CRUD operations"""

    @staticmethod
    def create_document(db: Session, title: str, content: str, doc_metadata: Optional[str] = None,
                        source: Optional[str] = None) -> Document:
        """Create a new document in the knowledge base"""
        document = Document(
            title=title,
            content=content,
            doc_metadata=doc_metadata,
            source=source
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def get_document_by_id(db: Session, document_id: int) -> Optional[Document]:
        """Get a document by its ID"""
        return db.query(Document).filter(Document.id == document_id).first()

    @staticmethod
    def get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
        """Get all documents with pagination"""
        return db.query(Document).offset(skip).limit(limit).all()

    @staticmethod
    def update_document(db: Session, document_id: int,
                        update_data: Dict[str, Any]) -> Optional[Document]:
        """Update a document"""
        db.query(Document).filter(Document.id ==
                                  document_id).update(update_data)
        db.commit()
        return DocumentRepository.get_document_by_id(db, document_id)

    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        """Delete a document and its chunks"""
        document = DocumentRepository.get_document_by_id(db, document_id)
        if document:
            db.delete(document)
            db.commit()
            return True
        return False


class DocumentChunkRepository:
    """Repository for document chunk operations"""

    @staticmethod
    def create_chunk(db: Session, document_id: int, content: str,
                     chunk_number: int, embedding: List[float]) -> DocumentChunk:
        """Create a document chunk with embedding"""
        chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            chunk_number=chunk_number,
            embedding=embedding
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk

    @staticmethod
    def get_chunk_by_id(db: Session, chunk_id: int) -> Optional[DocumentChunk]:
        """Get a document chunk by its ID"""
        return db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()

    @staticmethod
    def get_chunks_by_document_id(db: Session, document_id: int) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

    @staticmethod
    def delete_chunks_by_document_id(db: Session, document_id: int) -> bool:
        """Delete all chunks for a document"""
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id).delete()
        db.commit()
        return True

    @staticmethod
    def search_similar_chunks(db: Session, query_embedding: List[float], limit: int = 5) -> List[DocumentChunk]:
        """
        Search for similar document chunks using vector similarity
        Uses cosine similarity with pgvector
        """
        # SQL query using pgvector's cosine similarity operator
        stmt = text("""
            SELECT id, document_id, content, chunk_number
            FROM document_chunks
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT :limit
        """)

        # Execute query with parameters
        result = db.execute(stmt, {
            "query_embedding": query_embedding,
            "limit": limit
        })

        # Convert result to DocumentChunk objects
        chunks = []
        for row in result:
            chunk = DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                chunk_number=row.chunk_number
            )
            chunks.append(chunk)
        print(f"{chunks=}")
        print(f"Found {len(chunks)} similar chunks")
        return chunks
