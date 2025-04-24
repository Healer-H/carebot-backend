from core.database import get_db
from services.rag import RAGService
from utils.format_sources import format_document_source

db = next(get_db())


def get_information(query: str):
    """
    get information from your knowledge base to answer questions.

    Args:
        query (str): the user question

    Return:
        Dictionary containing the relevant context to the query and formatted sources.
    """
    # Get relevant documents and their chunks
    result = RAGService.retrieve_relevant_context(
        db, query, include_sources=True)

    # If we have document sources, format them according to AI SDK requirements
    formatted_sources = []
    if "documents" in result and result["documents"]:
        for doc in result["documents"]:
            formatted_sources.append(format_document_source(doc))

    return {
        "context": result["context"] if "context" in result else "",
        "sources": formatted_sources
    }
