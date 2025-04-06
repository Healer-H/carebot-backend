from typing import List, Dict, Any, Optional, Union
import json
from openai import OpenAI
import google.generativeai as genai
from utils import function_to_schema

from core.config import settings

class LLMService:
    """Service for interacting with language models"""
    
    def __init__(self):
        """Initialize the LLM service based on configuration"""
        self.provider = settings.LLM_PROVIDER
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        elif self.provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = settings.GEMINI_MODEL
            self.client = genai
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
        
        # enter callable functions here
        self.tools = []
        
        self.tools = [function_to_schema(tool) for tool in self.tools]
    
    def _format_openai_messages(self, messages: List[Dict[str, str]], context: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for OpenAI API with optional context"""
        formatted_messages = []
        
        # Add system message with context if provided
        if context:
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful healthcare assistant. Answer questions based on the following context.\n\n"
                    f"Context: {context}\n\n"
                    "If the answer is not in the context, respond based on your general healthcare knowledge."
                )
            }
        else:
            system_message = {
                "role": "system",
                "content": "You are a helpful healthcare assistant. Provide accurate and helpful information about healthcare topics."
            }
        
        formatted_messages.append(system_message)
        
        # Add the rest of the messages
        for message in messages:
            formatted_messages.append(message)
            
        return formatted_messages
    
    def _format_gemini_messages(self, messages: List[Dict[str, str]], context: Optional[str] = None) -> List[Dict[str, str]]:
        """Format messages for Gemini API with optional context"""
        formatted_messages = []
        
        # Add system message with context if provided
        if context:
            system_content = (
                "You are a helpful healthcare assistant. Answer questions based on the following context.\n\n"
                f"Context: {context}\n\n"
                "If the answer is not in the context, respond based on your general healthcare knowledge."
            )
        else:
            system_content = "You are a helpful healthcare assistant. Provide accurate and helpful information about healthcare topics."
        
        # Add system message
        formatted_messages.append({"role": "system", "parts": [system_content]})
        
        # Add the rest of the messages
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                role = "model"  # Gemini uses "model" instead of "system"
                
            formatted_message = {"role": role, "parts": [content]}
            formatted_messages.append(formatted_message)
            
        return formatted_messages
        
    def generate_response(self, messages: List[Dict[str, str]], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM based on messages and optional context
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            context: Optional context from retrieved documents
            
        Returns:
            Dictionary with response content and optional tool calls
        """
        if self.provider == "openai":
            # Format messages for OpenAI
            formatted_messages = self._format_openai_messages(messages, context)
            
            # Generate response with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # Extract response message
            response_message = response.choices[0].message
            response_content = response_message.content or ""
            
            # Check for tool calls
            tool_calls = None
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                tool_calls = []
                for tool_call in response_message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            return {
                "content": response_content,
                "tool_calls": tool_calls
            }
            
        elif self.provider == "gemini":
            # Format messages for Gemini
            formatted_messages = self._format_gemini_messages(messages, context)
            
            # Initialize Gemini model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            model = self.client.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            
            # Generate response
            response = model.generate_content(
                formatted_messages,
                tools=self.tools
            )
            
            # Extract text content
            response_content = response.text
            
            # Check for function calls (Gemini uses a different format)
            tool_calls = None
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'function_call'):
                                if tool_calls is None:
                                    tool_calls = []
                                # Format Gemini function calls to match OpenAI format
                                tool_calls.append({
                                    "id": f"call_{len(tool_calls)}",
                                    "type": "function",
                                    "function": {
                                        "name": part.function_call.name,
                                        "arguments": json.dumps(part.function_call.args)
                                    }
                                })
            
            return {
                "content": response_content,
                "tool_calls": tool_calls
            }
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")


# Singleton pattern
llm_service = LLMService()