from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
import logging

class VectorDBRepository:
    def __init__(self, host: str, port: int):
        self.client = chromadb.Client(host=host, port=port)
        self.logger = logging.getLogger("vector_db_repo")
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key="",  # Filled at runtime
            model_name="text-embedding-ada-002"
        )
        
    def create_collection(self, name: str) -> None:
        """
        Tạo collection mới hoặc lấy collection đã tồn tại
        """
        try:
            self.client.get_collection(name)
        except:
            self.client.create_collection(
                name=name,
                embedding_function=self.embedding_function
            )
            
    def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        """
        Thêm tài liệu vào collection
        """
        collection = self.client.get_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )