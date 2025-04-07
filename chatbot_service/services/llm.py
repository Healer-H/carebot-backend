from typing import List, Dict, Any, Optional, Union
import json
from openai import OpenAI
import google.generativeai as genai
from utils import function_to_schema
from tools import get_weather, get_current_location

from core.config import settings


MAX_TOOL_CALLS = 5  # Maximum number of tool calls allowed in a single response

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
        
        # Register available tools
        self.tools = [get_weather, get_current_location]
        self.tools_map = {
            tool.__name__: tool for tool in self.tools
        }
        
        self.tools_schema = [function_to_schema(tool) for tool in self.tools]
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        """Execute a tool call and return the result"""
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])
        
        if tool_name in self.tools_map:
            tool = self.tools_map[tool_name]
            return tool(**tool_args)
        else:
            raise ValueError(f"Tool {tool_name} not found in tools map.")

    
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
        
    def generate_response(self, messages: List[Dict[str, str]], context: Optional[str] = None, execute_tools: bool = True) -> Dict[str, Any]:
        """
        Generate a response from the LLM based on messages and optional context
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            context: Optional context from retrieved documents
            execute_tools: Whether to execute tool calls automatically
            
        Returns:
            Dictionary with response content, optional tool calls, and tool results if executed
        """
        if self.provider == "openai":
            # Format messages for OpenAI
            formatted_messages = self._format_openai_messages(messages, context)
            
            # Initialize conversation history for this turn
            conversation_messages = formatted_messages.copy()
            
            # Start the initial LLM call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_messages,
                tools=self.tools_schema,
                tool_choice="auto"
            )
            
            # Extract response message
            response_message = response.choices[0].message
            response_content = response_message.content or ""
            
            # Initialize result dictionary
            result = {
                "content": response_content,
                "conversation_turns": [],
                "final_content": response_content  # Default if no tool calls
            }
            
            # Check if the response contains tool calls
            if execute_tools and hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                # We have tool calls in the response
                turn_number = 1
                
                while True:
                    # Process current response with tool calls
                    tool_calls = []
                    tool_results = []
                    
                    # Add the assistant message to conversation
                    conversation_messages.append({
                        "role": "assistant",
                        "content": response_content,
                        "tool_calls": response_message.tool_calls
                    })
                    
                    # Process all tool calls in this response
                    for tool_call in response_message.tool_calls:
                        tool_call_data = {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        tool_calls.append(tool_call_data)
                        
                        # Execute the tool
                        try:
                            result_value = self._execute_tool_call(tool_call_data)
                            tool_result = {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "result": result_value
                            }
                        except Exception as e:
                            tool_result = {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "error": str(e)
                            }
                            
                        tool_results.append(tool_result)
                        
                        # Add tool result to conversation
                        conversation_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "name": tool_result["function_name"],
                            "content": str(tool_result.get("result", tool_result.get("error", "")))
                        })
                    
                    # Store this turn's information
                    turn_info = {
                        "turn": turn_number,
                        "content": response_content,
                        "tool_calls": tool_calls,
                        "tool_results": tool_results
                    }
                    result["conversation_turns"].append(turn_info)
                    
                    # Make a follow-up call with the updated conversation
                    follow_up_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=conversation_messages,
                        tools=self.tools_schema,
                        tool_choice="auto"
                    )
                    
                    # Update response for next iteration
                    response_message = follow_up_response.choices[0].message
                    response_content = response_message.content or ""
                    
                    # Update the final content with the latest response
                    result["final_content"] = response_content
                    
                    # Check if we have more tool calls
                    if not (hasattr(response_message, 'tool_calls') and response_message.tool_calls):
                        # No more tool calls, we're done
                        break
                        
                    # Increment turn counter and continue the loop for another turn of tool calling
                    turn_number += 1
                    
                    # Safety check to prevent infinite loops
                    if turn_number > MAX_TOOL_CALLS:  
                        break
            
            return result
            
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
            
            # Initialize conversation history for this turn
            conversation_messages = formatted_messages.copy()
            
            # Start the initial LLM call
            response = model.generate_content(
                conversation_messages,
                tools=self.tools_schema
            )
            
            # Extract text content
            response_content = response.text
            
            # Initialize result dictionary
            result = {
                "content": response_content,
                "conversation_turns": [],
                "final_content": response_content  # Default if no tool calls
            }
            
            # Process tool calls if they exist
            turn_number = 1
            has_tool_calls = False
            
            if execute_tools and hasattr(response, 'candidates') and response.candidates:
                # Check for tool calls in the response
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    content = candidate.content
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'function_call'):
                                has_tool_calls = True
                                break
            
            while has_tool_calls and turn_number <= MAX_TOOL_CALLS:
                # Process current response with tool calls
                tool_calls = []
                tool_results = []
                
                # Add the model message to conversation
                follow_up_message = {"role": "model", "parts": [response_content]}
                conversation_messages.append(follow_up_message)
                
                # Get tool calls from the response
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        if hasattr(content, 'parts') and content.parts:
                            for part in content.parts:
                                if hasattr(part, 'function_call'):
                                    # Format Gemini function call
                                    tool_call_data = {
                                        "id": f"call_{turn_number}_{len(tool_calls)}",
                                        "type": "function",
                                        "function": {
                                            "name": part.function_call.name,
                                            "arguments": json.dumps(part.function_call.args)
                                        }
                                    }
                                    tool_calls.append(tool_call_data)
                                    
                                    # Execute the tool
                                    try:
                                        result_value = self._execute_tool_call(tool_call_data)
                                        tool_result = {
                                            "tool_call_id": tool_call_data["id"],
                                            "function_name": part.function_call.name,
                                            "result": result_value
                                        }
                                    except Exception as e:
                                        tool_result = {
                                            "tool_call_id": tool_call_data["id"],
                                            "function_name": part.function_call.name,
                                            "error": str(e)
                                        }
                                        
                                    tool_results.append(tool_result)
                                    
                                    # Add tool result to conversation (Gemini format)
                                    result_message = {
                                        "role": "user", 
                                        "parts": [f"Tool {tool_result['function_name']} returned: {str(tool_result.get('result', tool_result.get('error', '')))}"]
                                    }
                                    conversation_messages.append(result_message)
                
                # Store this turn's information
                if tool_calls:
                    turn_info = {
                        "turn": turn_number,
                        "content": response_content,
                        "tool_calls": tool_calls,
                        "tool_results": tool_results
                    }
                    result["conversation_turns"].append(turn_info)
                    
                    # Make a follow-up call with the updated conversation
                    follow_up_response = model.generate_content(
                        conversation_messages,
                        tools=self.tools_schema
                    )
                    
                    # Update response for next iteration
                    response = follow_up_response
                    response_content = response.text
                    
                    # Update the final content with the latest response
                    result["final_content"] = response_content
                    
                    # Check if we have more tool calls
                    has_tool_calls = False
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            content = candidate.content
                            if hasattr(content, 'parts') and content.parts:
                                for part in content.parts:
                                    if hasattr(part, 'function_call'):
                                        has_tool_calls = True
                                        break
                    
                    # Increment turn counter
                    turn_number += 1
                else:
                    # No tool calls found, exit the loop
                    break
            
            return result
            
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")


# Singleton pattern
llm_service = LLMService()