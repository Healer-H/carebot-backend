def format_document_source(document):
    """
    Convert a Document model instance to the AI SDK source format.

    Args:
        document: Document model instance

    Returns:
        str: Formatted source string
    """
    # Create source data dictionary from document properties
    source_data = {
        "sourceType": "knowledge_base",
        "id": f"doc-{document.id}",
        "title": document.title
    }

    # Add URL if source contains a URL
    if document.source and (document.source.startswith("http://") or document.source.startswith("https://")):
        source_data["url"] = document.source

    return source_data
