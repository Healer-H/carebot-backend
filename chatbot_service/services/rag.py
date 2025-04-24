from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.knowledge_base import DocumentChunk, Document

from repositories.knowledge_base import DocumentChunkRepository
from services.embeddings import embedding_service
from core.config import settings


class RAGService:
    """Service for Retrieval-Augmented Generation (RAG)"""

    @staticmethod
    def chunk_document(document_text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split document into chunks for embedding and retrieval

        Args:
            document_text: The document text to split
            chunk_size: The approximate size of each chunk in characters
            overlap: The overlap between consecutive chunks in characters

        Returns:
            List of document chunks
        """
        # Simple chunking by character count with overlap
        chunks = []
        start = 0

        while start < len(document_text):
            # Get chunk of approximately chunk_size
            end = min(start + chunk_size, len(document_text))

            # If not at the end of the document, try to find a good splitting point
            if end < len(document_text):
                # Look for the last period, question mark, or exclamation within the last 100 chars of the chunk
                for i in range(end, max(end - 100, start), -1):
                    if document_text[i-1] in ['.', '!', '?', '\n']:
                        end = i
                        break

            # Add the chunk
            chunks.append(document_text[start:end])

            # Move to next chunk with overlap
            start = end - overlap

        return chunks

    @staticmethod
    def index_document(db: Session, document_id: int, document_text: str) -> None:
        """
        Index a document by chunking it and creating embeddings

        Args:
            db: Database session
            document_id: ID of the document to index
            document_text: Text content of the document
        """
        # First delete any existing chunks for this document
        # DocumentChunkRepository.delete_chunks_by_document_id(db, document_id)

        # Chunk the document
        # chunks = RAGService.chunk_document(document_text)
        chunks = [document_text]

        # Create embeddings for all chunks
        embeddings = embedding_service.create_embeddings(chunks)

        # Store chunks with embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            DocumentChunkRepository.create_chunk(
                db=db,
                document_id=document_id,
                content=chunk,
                chunk_number=i,
                embedding=embedding
            )

    @staticmethod
    def retrieve_relevant_context(db: Session, query: str, include_sources=False):
        """
        Retrieve relevant context from the knowledge base based on the user query.

        Args:
            db: Database session
            query: User query string
            include_sources: Whether to include source documents

        Returns:
            dict: Contains context and optionally document sources
        """
        # Create embedding for the query
        query_embedding = embedding_service.create_embedding(query)

        # Search for similar chunks
        chunks = DocumentChunkRepository.search_similar_chunks(
            db=db,
            query_embedding=query_embedding,
            limit=settings.MAX_RELEVANT_CHUNKS
        )

        # Compile context from chunks
        context = "\n\n".join([chunk.content for chunk in chunks])

        result = {"context": context}

        # If sources are requested, include the parent documents
        if include_sources:
            # Get unique parent documents for the chunks
            doc_ids = set(chunk.document_id for chunk in chunks)
            documents = db.query(Document).filter(
                Document.id.in_(doc_ids)).all()
            result["documents"] = documents

        return result


rag_service = RAGService()
