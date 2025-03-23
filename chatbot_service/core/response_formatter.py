from typing import List
import logging
from fastapi import Depends

from models.source import Source
from core.source_citation import SourceCitationService, get_source_citation_service

logger = logging.getLogger("response_formatter")

class ResponseFormatter:
    def __init__(self, source_citation: SourceCitationService):
        self.source_citation = source_citation
    
    async def format_response(self, content: str, sources: List[Source]) -> str:
        """
        Định dạng phản hồi cuối cùng với trích dẫn
        """
        # Xóa các tham chiếu số nếu có
        clean_content = self._remove_numeric_references(content)
        
        # Thêm trích dẫn
        if sources:
            citation = await self.source_citation.format_citation(sources)
            formatted_response = clean_content + citation
        else:
            formatted_response = clean_content
        
        return formatted_response
    
    def _remove_numeric_references(self, content: str) -> str:
        """
        Xóa các tham chiếu số như [1], [2] trong nội dung
        """
        # Xóa các tham chiếu dạng [1], [2,3], [4-6]
        return re.sub(r'\[\d+(?:[-,]\d+)*\]', '', content)
    
    def _format_bullet_points(self, content: str) -> str:
        """
        Định dạng danh sách dấu gạch đầu dòng
        """
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Chuyển đổi dòng bắt đầu bằng "- " thành dạng bullet point chuẩn
            if line.startswith("- "):
                formatted_lines.append("• " + line[2:])
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

# Dependency
def get_response_formatter(
    source_citation: SourceCitationService = Depends(get_source_citation_service)
) -> ResponseFormatter:
    return ResponseFormatter(source_citation)