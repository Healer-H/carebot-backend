from services.rag import RAGService
from core.database import get_db

db = next(get_db())

def get_information(query: str):
    """
    get information from your knowledge base to answer questions.

    Args:
        query (str): the user question
    
    Return:
        Dictionary contain the relevants context to the query.
    """

    context = RAGService.retrieve_relevant_context(db, query)

    return { "context": context }
