# Healthcare Chatbot Service

A RAG-based chatbot service for a healthcare mobile application using FastAPI, PostgreSQL with pgvector, and LLMs from OpenAI or Google Gemini.

## Features

- **RAG (Retrieval-Augmented Generation)**: Enhances responses with relevant information from the knowledge base
- **Vector Search**: Uses pgvector for efficient similarity search of document chunks
- **Function Calling**: Integrates healthcare-specific tools for medication information, appointment scheduling, and symptom checking
- **Conversation Management**: Tracks and manages chat history
- **Multi-LLM Support**: Works with both OpenAI and Google Gemini models

## Prerequisites

- Python 3.9+
- PostgreSQL with [pgvector](https://github.com/pgvector/pgvector) extension
- OpenAI API key or Google Gemini API key

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Update the `.env` file with your database and API credentials
5. Create a PostgreSQL database and install the pgvector extension:
   ```sql
   CREATE DATABASE carebot;
   \c carebot
   CREATE EXTENSION vector;
   ```

## Usage

1. Start the service:
   ```bash
   python main.py
   ```
2. Access the API documentation at `http://localhost:8000/api/v1/docs`

## API Endpoints

### Chatbot

- `POST /api/v1/chatbot/conversations`: Create a new conversation
- `GET /api/v1/chatbot/conversations/{conversation_id}`: Get conversation details with messages
- `GET /api/v1/chatbot/users/{user_id}/conversations`: Get all conversations for a user
- `DELETE /api/v1/chatbot/conversations/{conversation_id}`: Delete a conversation
- `POST /api/v1/chatbot/conversations/{conversation_id}/messages`: Send a message and get a response
- `POST /api/v1/chatbot/messages/{message_id}/tool-results`: Add a tool result to a message

### Knowledge Base

- `POST /api/v1/knowledge/documents`: Create a new document
- `GET /api/v1/knowledge/documents`: Get all documents
- `GET /api/v1/knowledge/documents/{document_id}`: Get a specific document
- `PUT /api/v1/knowledge/documents/{document_id}`: Update a document
- `DELETE /api/v1/knowledge/documents/{document_id}`: Delete a document

## Architecture

- **FastAPI**: Web framework for building the API
- **SQLAlchemy**: ORM for database operations
- **pgvector**: PostgreSQL extension for vector similarity search
- **LangChain**: Framework for working with LLMs
- **OpenAI/Gemini**: LLM providers for generating responses

## Healthcare Tools

The chatbot integrates the following healthcare-specific tools:

1. **Medication Information**: Provides details about medications including dosage, side effects, and interactions
2. **Appointment Scheduling**: Allows users to schedule medical appointments
3. **Symptom Checker**: Analyzes symptoms and suggests possible conditions

## License

[MIT License](LICENSE)