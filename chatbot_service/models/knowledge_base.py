from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column
from pgvector.sqlalchemy import Vector

# from sqlalchemy.dialects.postgresql import TSVECTOR

from core.database import Base
from core.config import settings


class Document(Base):
    """
    Document model for storing knowledge base articles, medical information, etc.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column(Text, nullable=True)  # JSON string for additional metadata
    source = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with chunks
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """
    Document chunk model for storing chunks of documents for RAG retrieval
    """

    __tablename__ = "document_chunks"

    id = mapped_column(Integer, primary_key=True, index=True)
    document_id = mapped_column(
        Integer, ForeignKey("documents.id"), nullable=False, index=True
    )
    content = mapped_column(Text, nullable=False)
    chunk_number = mapped_column(
        Integer, nullable=False
    )  

    # Vector embedding for similarity search
    embedding = mapped_column(Vector(settings.VECTOR_DIMENSION))

    # Relationship with parent document
    document = relationship("Document", back_populates="chunks")

    # __table_args__ = {
    #     'postgresql_with': 'vector_extension'
    # }
