from typing import List, Dict, Any
import chromadb
import asyncio
import logging
from fastapi import Depends

from config import settings

logger = logging.getLogger("vector_db_manager")

class VectorDatabaseManager:
    def __init__(self, host: str, port: int, collection_name: str = "medical_knowledge"):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection_name = collection_name
        self.logger = logging.getLogger("vector_db")
        self._init_collection()
        
    def _init_collection(self):
        """
        Khởi tạo collection
        """
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Connected to collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error connecting to vector database: {str(e)}")
            self.collection = None
        
    async def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tài liệu liên quan dựa trên query
        """
        if not self.collection:
            self._init_collection()
            if not self.collection:
                logger.error("Cannot search: collection not available")
                return []
        
        try:
            # Thực hiện tìm kiếm
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=n_results
            )
            
            documents = []
            if "documents" in results and results["documents"]:
                for i, doc in enumerate(results['documents'][0]):
                    documents.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i] if 'metadatas' in results and results['metadatas'] else {},
                        'score': float(results['distances'][0][i]) if 'distances' in results and results['distances'] else 0
                    })
            
            logger.info(f"Retrieved {len(documents)} documents for query")
            return documents
        except Exception as e:
            logger.error(f"Error searching vector database: {str(e)}")
            return []
    
    async def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        """
        Thêm tài liệu vào vector database
        """
        if not self.collection:
            self._init_collection()
            if not self.collection:
                logger.error("Cannot add documents: collection not available")
                return False
        
        try:
            await asyncio.to_thread(
                self.collection.add,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(texts)} documents to vector database")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to vector database: {str(e)}")
            return False

# Dependency
def get_vector_db_manager() -> VectorDatabaseManager:
    return VectorDatabaseManager(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        collection_name=settings.CHROMA_COLLECTION
    )