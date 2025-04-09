def get_information(db, rag_service, query: str):
    """
    get information from your knowledge base to answer questions.

    Args:
        query (str): the user question
    
    Return:
        Dictionary contain the relevants context to the query.
    """

    context = rag_service.retrieve_relevant_context(db, query)

    return { "context": context }
