from typing import List, Dict, Any
import logging
from fastapi import Depends

from models.source import Source
from config import settings

logger = logging.getLogger("source_citation")

class SourceCitationService:
    def __init__(self):
        pass
        
    async def extract_sources(self, content: str, retrieved_docs: List[Dict[str, Any]]) -> List[Source]:
        """
        Trích xuất và định dạng thông tin nguồn
        """
        sources = []
        
        # Lọc các nguồn có điểm tương đồng cao
        relevant_sources = [doc for doc in retrieved_docs if doc.get('score', 0) > 0.7]
        
        # Xử lý metadata từ mỗi tài liệu
        for doc in relevant_sources:
            metadata = doc.get('metadata', {})
            
            # Kiểm tra trùng lặp
            if not self._is_duplicate_source(sources, metadata):
                source = Source(
                    title=metadata.get('title', 'Tài liệu y tế'),
                    url=metadata.get('url'),
                    description=metadata.get('description', self._create_snippet(doc.get('content', ''), 100)),
                    publication_date=metadata.get('publication_date')
                )
                sources.append(source)
        
        # Giới hạn số nguồn
        return sources[:5]
        
    async def format_citation(self, sources: List[Source]) -> str:
        """
        Định dạng trích dẫn từ nguồn
        """
        if not sources:
            return ""
        
        citation = "\n\nNguồn tham khảo:\n"
        
        for i, source in enumerate(sources, 1):
            citation += f"{i}. {source.title}"
            if source.publication_date:
                citation += f" ({source.publication_date.year})"
            if source.url:
                citation += f" - {source.url}"
            citation += "\n"
        
        return citation
    
    def _is_duplicate_source(self, sources: List[Source], metadata: Dict[str, Any]) -> bool:
        """
        Kiểm tra xem nguồn đã tồn tại trong danh sách chưa
        """
        for source in sources:
            if source.title == metadata.get('title') or source.url == metadata.get('url'):
                return True
        return False
    
    def _create_snippet(self, text: str, max_length: int = 100) -> str:
        """
        Tạo đoạn mô tả ngắn từ nội dung
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length].rsplit(' ', 1)[0] + "..."

# Dependency
def get_source_citation_service() -> SourceCitationService:
    return SourceCitationService()