from typing import List, Dict, Any, Optional, Union, AsyncIterator
import json
from openai import OpenAI, AsyncOpenAI
import google.generativeai as genai
from utils import function_to_schema
from tools import get_weather, get_current_location, get_information

from core.config import settings


MAX_TOOL_CALLS = 5  # Maximum number of tool calls allowed in a single response


class LLMService:
    """Service for interacting with language models"""

    def __init__(self):
        """Initialize the LLM service based on configuration"""
        self.provider = settings.LLM_PROVIDER

        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
        elif self.provider == "gemini":
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = settings.GEMINI_MODEL
            self.client = genai
        else:
            raise ValueError(
                f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

        # Register available tools
        self.tools = [get_information]
        self.tools_map = {tool.__name__: tool for tool in self.tools}
        self.tools_schema = [function_to_schema(tool) for tool in self.tools]

        # Streaming state variables
        self.current_stream_content = ""
        self.current_stream_tool_calls = []
        self.current_stream_tool_results = []

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Any:
        """Execute a tool call and return the result"""
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(tool_call["function"]["arguments"])

        if tool_name in self.tools_map:
            tool = self.tools_map[tool_name]
            return tool(**tool_args)
        else:
            raise ValueError(f"Tool {tool_name} not found in tools map.")

    def _format_openai_messages(
        self, messages: List[Dict[str, str]], context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Format messages for OpenAI API with optional context"""
        formatted_messages = []

        # Add system message with context if provided
        if context:
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful healthcare assistant. Answer questions based on the following context.\n\n"
                    f"Context: {context}\n\n"
                    "If the answer is not in the context, respond based on your general healthcare knowledge.\n\n"
                    "IMPORTANT TOOL USAGE INSTRUCTIONS:\n"
                    "- You have access to several tools that can provide real-time information. Always use these tools when appropriate.\n"
                    "- When a user asks for real-time or external information that can be answered by a tool, use that tool rather than providing general information.\n"
                    "- Use tools in a logical sequence. If one tool depends on the output of another tool, call them in the correct order.\n"
                    "- For location-based queries without a specified location, get the user's location first before using location-dependent tools.\n"
                    "- Read each tool's description carefully to understand when and how to use it appropriately.\n"
                    "- For queries requiring real-time data (weather, time, location, etc.), always prefer using the appropriate tool over giving general responses."
                ),
            }
        else:
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful healthcare assistant. Provide accurate and helpful information about healthcare topics.\n\n"
                    "IMPORTANT TOOL USAGE INSTRUCTIONS:\n"
                    "- You have access to several tools that can provide real-time information. Always use these tools when appropriate.\n"
                    "- When a user asks for real-time or external information that can be answered by a tool, use that tool rather than providing general information.\n"
                    "- Use tools in a logical sequence. If one tool depends on the output of another tool, call them in the correct order.\n"
                    "- For location-based queries without a specified location, get the user's location first before using location-dependent tools.\n"
                    "- Read each tool's description carefully to understand when and how to use it appropriately.\n"
                    "- For queries requiring real-time data (weather, time, location, etc.), always prefer using the appropriate tool over giving general responses."
                ),
            }

        formatted_messages.append(system_message)

        # Add the rest of the messages
        for message in messages:
            formatted_messages.append(message)

        return formatted_messages

    def _format_gemini_messages(
        self, messages: List[Dict[str, str]], context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Format messages for Gemini API with optional context"""
        formatted_messages = []

        # Add system message with context if provided
        if context:
            system_content = (
                "You are a helpful healthcare assistant. Answer questions based on the following context.\n\n"
                f"Context: {context}\n\n"
                "If the answer is not in the context, respond based on your general healthcare knowledge.\n\n"
                "IMPORTANT TOOL USAGE INSTRUCTIONS:\n"
                "- You have access to several tools that can provide real-time information. Always use these tools when appropriate.\n"
                "- When a user asks for real-time or external information that can be answered by a tool, use that tool rather than providing general information.\n"
                "- Use tools in a logical sequence. If one tool depends on the output of another tool, call them in the correct order.\n"
                "- For location-based queries without a specified location, get the user's location first before using location-dependent tools.\n"
                "- Read each tool's description carefully to understand when and how to use it appropriately.\n"
                "- For queries requiring real-time data (weather, time, location, etc.), always prefer using the appropriate tool over giving general responses."
            )
        else:
            system_content = (
                "You are a helpful healthcare assistant. Provide accurate and helpful information about healthcare topics.\n\n"
                "IMPORTANT TOOL USAGE INSTRUCTIONS:\n"
                "- You have access to several tools that can provide real-time information. Always use these tools when appropriate.\n"
                "- When a user asks for real-time or external information that can be answered by a tool, use that tool rather than providing general information.\n"
                "- Use tools in a logical sequence. If one tool depends on the output of another tool, call them in the correct order.\n"
                "- For location-based queries without a specified location, get the user's location first before using location-dependent tools.\n"
                "- Read each tool's description carefully to understand when and how to use it appropriately.\n"
                "- For queries requiring real-time data (weather, time, location, etc.), always prefer using the appropriate tool over giving general responses."
            )

        # Add system message
        formatted_messages.append(
            {"role": "system", "parts": [system_content]})

        # Add the rest of the messages
        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "system":
                role = "model"  # Gemini uses "model" instead of "system"

            formatted_message = {"role": role, "parts": [content]}
            formatted_messages.append(formatted_message)

        return formatted_messages

    def convert_to_openai_messages(self, messages: List[Any]):
        openai_messages = [
            # {
            #     "role": "system",
            #     "content": (
            #     "You are a helpful healthcare assistant. Provide accurate and helpful information about healthcare topics.\n\n"
            #     "IMPORTANT TOOL USAGE INSTRUCTIONS:\n"
            #     "- You have access to several tools that can provide real-time information. Always use these tools when appropriate.\n"
            #     "- When a user asks for real-time or external information that can be answered by a tool, use that tool rather than providing general information.\n"
            #     "- Use tools in a logical sequence. If one tool depends on the output of another tool, call them in the correct order.\n"
            #     "- For location-based queries without a specified location, get the user's location first before using location-dependent tools.\n"
            #     "- Read each tool's description carefully to understand when and how to use it appropriately.\n"
            #     "- For queries requiring real-time data (weather, time, location, etc.), always prefer using the appropriate tool over giving general responses.")
            # }
        ]

        for message in messages:
            parts = []

            parts.append({
                'type': 'text',
                'text': message.content
            })

            if (message.toolInvocations):
                tool_calls = [
                    {
                        'id': tool_invocation.toolCallId,
                        'type': 'function',
                        'function': {
                            'name': tool_invocation.toolName,
                            'arguments': json.dumps(tool_invocation.args)
                        }
                    }
                    for tool_invocation in message.toolInvocations]

                openai_messages.append({
                    "role": 'assistant',
                    "tool_calls": tool_calls
                })

                tool_results = [
                    {
                        'role': 'tool',
                        'content': json.dumps(tool_invocation.result),
                        'tool_call_id': tool_invocation.toolCallId
                    }
                    for tool_invocation in message.toolInvocations]

                openai_messages.extend(tool_results)

                continue

            openai_messages.append({
                "role": message.role,
                "content": parts
            })

        return openai_messages

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[str] = None,
        execute_tools: bool = True,
    ) -> Dict[str, Any]:
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

            # Initialize conversation history for this turn
            conversation_messages = formatted_messages.copy()

            # Start the initial LLM call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_messages,
                tools=self.tools_schema,
                tool_choice="auto",
            )

            # Extract response message
            response_message = response.choices[0].message
            response_content = response_message.content or ""

            # Initialize result dictionary
            result = {
                "content": response_content,
                "conversation_turns": [],
                "final_content": response_content,  # Default if no tool calls
            }

            # Check if the response contains tool calls
            if (
                execute_tools
                and hasattr(response_message, "tool_calls")
                and response_message.tool_calls
            ):
                # We have tool calls in the response
                turn_number = 1

                while True:
                    # Process current response with tool calls
                    tool_calls = []
                    tool_results = []

                    # Add the assistant message to conversation
                    conversation_messages.append(
                        {
                            "role": "assistant",
                            "content": response_content,
                            "tool_calls": response_message.tool_calls,
                        }
                    )

                    # Process all tool calls in this response
                    for tool_call in response_message.tool_calls:
                        tool_call_data = {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        tool_calls.append(tool_call_data)

                        # Execute the tool
                        try:
                            result_value = self._execute_tool_call(
                                tool_call_data)
                            tool_result = {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "result": result_value,
                            }
                        except Exception as e:
                            tool_result = {
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "error": str(e),
                            }

                        tool_results.append(tool_result)

                        # Add tool result to conversation
                        conversation_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_result["tool_call_id"],
                                "name": tool_result["function_name"],
                                "content": str(
                                    tool_result.get(
                                        "result", tool_result.get("error", "")
                                    )
                                ),
                            }
                        )

                    # Store this turn's information
                    turn_info = {
                        "turn": turn_number,
                        "content": response_content,
                        "tool_calls": tool_calls,
                        "tool_results": tool_results,
                    }
                    result["conversation_turns"].append(turn_info)

                    # Make a follow-up call with the updated conversation
                    follow_up_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=conversation_messages,
                        tools=self.tools_schema,
                        tool_choice="auto",
                    )

                    # Update response for next iteration
                    response_message = follow_up_response.choices[0].message
                    response_content = response_message.content or ""

                    # Update the final content with the latest response
                    result["final_content"] = response_content

                    # Check if we have more tool calls
                    if not (
                        hasattr(response_message, "tool_calls")
                        and response_message.tool_calls
                    ):
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
            formatted_messages = self._format_gemini_messages(
                messages, context)

            # Initialize Gemini model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }

            model = self.client.GenerativeModel(
                model_name=self.model, generation_config=generation_config
            )

            # Initialize conversation history for this turn
            conversation_messages = formatted_messages.copy()

            # Start the initial LLM call
            response = model.generate_content(
                conversation_messages, tools=self.tools_schema
            )

            # Extract text content
            response_content = response.text

            # Initialize result dictionary
            result = {
                "content": response_content,
                "conversation_turns": [],
                "final_content": response_content,  # Default if no tool calls
            }

            # Process tool calls if they exist
            turn_number = 1
            has_tool_calls = False

            if (
                execute_tools
                and hasattr(response, "candidates")
                and response.candidates
            ):
                # Check for tool calls in the response
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    content = candidate.content
                    if hasattr(content, "parts") and content.parts:
                        for part in content.parts:
                            if hasattr(part, "function_call"):
                                has_tool_calls = True
                                break

            while has_tool_calls and turn_number <= MAX_TOOL_CALLS:
                # Process current response with tool calls
                tool_calls = []
                tool_results = []

                # Add the model message to conversation
                follow_up_message = {"role": "model",
                                     "parts": [response_content]}
                conversation_messages.append(follow_up_message)

                # Get tool calls from the response
                if hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content:
                        content = candidate.content
                        if hasattr(content, "parts") and content.parts:
                            for part in content.parts:
                                if hasattr(part, "function_call"):
                                    # Format Gemini function call
                                    tool_call_data = {
                                        "id": f"call_{turn_number}_{len(tool_calls)}",
                                        "type": "function",
                                        "function": {
                                            "name": part.function_call.name,
                                            "arguments": json.dumps(
                                                part.function_call.args
                                            ),
                                        },
                                    }
                                    tool_calls.append(tool_call_data)

                                    # Execute the tool
                                    try:
                                        result_value = self._execute_tool_call(
                                            tool_call_data
                                        )
                                        tool_result = {
                                            "tool_call_id": tool_call_data["id"],
                                            "function_name": part.function_call.name,
                                            "result": result_value,
                                        }
                                    except Exception as e:
                                        tool_result = {
                                            "tool_call_id": tool_call_data["id"],
                                            "function_name": part.function_call.name,
                                            "error": str(e),
                                        }

                                    tool_results.append(tool_result)

                                    # Add tool result to conversation (Gemini format)
                                    result_message = {
                                        "role": "user",
                                        "parts": [
                                            f"Tool {tool_result['function_name']} returned: {str(tool_result.get('result', tool_result.get('error', '')))}"
                                        ],
                                    }
                                    conversation_messages.append(
                                        result_message)

                # Store this turn's information
                if tool_calls:
                    turn_info = {
                        "turn": turn_number,
                        "content": response_content,
                        "tool_calls": tool_calls,
                        "tool_results": tool_results,
                    }
                    result["conversation_turns"].append(turn_info)

                    # Make a follow-up call with the updated conversation
                    follow_up_response = model.generate_content(
                        conversation_messages, tools=self.tools_schema
                    )

                    # Update response for next iteration
                    response = follow_up_response
                    response_content = response.text

                    # Update the final content with the latest response
                    result["final_content"] = response_content

                    # Check if we have more tool calls
                    has_tool_calls = False
                    if hasattr(response, "candidates") and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, "content") and candidate.content:
                            content = candidate.content
                            if hasattr(content, "parts") and content.parts:
                                for part in content.parts:
                                    if hasattr(part, "function_call"):
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

    async def generate_response_stream(
        self,
        messages: List[Any],
        context: Optional[str] = None,
    ) -> Any:
        """
        Stream a response from the LLM based on messages and optional context

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            context: Optional context from retrieved documents

        Yields:
            Chunks of the response in a format compatible with Vercel AI SDK
        """
        # Reset streaming state
        self.current_stream_content = ""
        self.current_stream_tool_calls = []
        self.current_stream_tool_results = []

        if self.provider == "openai":
            # Format messages for OpenAI
            openai_messages = self.convert_to_openai_messages(messages)

            # Start streaming response
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=self.tools_schema,
                max_tokens=512,
                stream=True,
            )

            draft_tool_calls = []
            draft_tool_calls_index = -1

            for chunk in stream:
                for choice in chunk.choices:
                    if choice.finish_reason == "stop":
                        continue

                    elif choice.finish_reason == "tool_calls":
                        for tool_call in draft_tool_calls:
                            yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                                id=tool_call["id"],
                                name=tool_call["name"],
                                args=tool_call["arguments"])

                        for tool_call in draft_tool_calls:
                            try:
                                # Execute the tool with proper error handling
                                tool_name = tool_call["name"]
                                tool_args = json.loads(tool_call["arguments"])

                                if tool_name in self.tools_map:
                                    tool_fn = self.tools_map[tool_name]

                                    # Execute the tool function
                                    from sqlalchemy.orm import Session
                                    from database import SessionLocal

                                    try:
                                        # Create a new session for this tool call
                                        db = SessionLocal()

                                        # Try to execute the tool with the session
                                        if tool_name == "get_information":
                                            # Special handling for get_information to pass db session
                                            tool_result = tool_fn(
                                                db=db, **tool_args)
                                        else:
                                            tool_result = tool_fn(**tool_args)

                                        # Commit the session if successful
                                        db.commit()
                                    except Exception as db_err:
                                        # Rollback on error
                                        db.rollback()
                                        raise db_err
                                    finally:
                                        # Always close the session
                                        db.close()

                                else:
                                    tool_result = {
                                        "error": f"Tool {tool_name} not found"}

                                yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                                    id=tool_call["id"],
                                    name=tool_call["name"],
                                    args=tool_call["arguments"],
                                    result=json.dumps(tool_result))

                                if isinstance(tool_result, dict) and "sources" in tool_result:
                                    print(f"sources: {tool_result['sources']}")
                                    for source in tool_result["sources"]:
                                        yield 'h:{{"sourceType":"url","id":"{id}","url":"{url}","title":"{title}"}}\n'.format(
                                            id=source["id"],
                                            url=source['url'],
                                            title=source['title']
                                        )

                            except Exception as e:
                                error_message = str(e)
                                yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{{"error":"{error_msg}"}}}}\n'.format(
                                    id=tool_call["id"],
                                    name=tool_call["name"],
                                    args=tool_call["arguments"],
                                    error_msg=error_message.replace('"', '\\"')
                                )

                    elif choice.delta.tool_calls:
                        for tool_call in choice.delta.tool_calls:
                            id = tool_call.id
                            name = tool_call.function.name
                            arguments = tool_call.function.arguments

                            if (id is not None):
                                draft_tool_calls_index += 1
                                draft_tool_calls.append(
                                    {"id": id, "name": name, "arguments": ""})

                            else:
                                draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments

                    else:
                        yield '0:{text}\n'.format(text=json.dumps(choice.delta.content))

                if chunk.choices == []:
                    usage = chunk.usage
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens

                    yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
                        reason="tool-calls" if len(
                            draft_tool_calls) > 0 else "stop",
                        prompt=prompt_tokens,
                        completion=completion_tokens
                    )

        elif self.provider == "gemini":
            # Format messages for Gemini
            formatted_messages = self._format_gemini_messages(
                messages, context)

            # Initialize Gemini model with streaming config
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

            # Start streaming generation
            stream = model.generate_content(
                formatted_messages,
                tools=self.tools_schema,
                stream=True
            )

            # Initialize tool tracking
            is_processing_tool_call = False
            current_tool_call = None

            try:
                # Process the streaming response
                async for chunk in stream:
                    # Process text chunks
                    if hasattr(chunk, "text"):
                        text_chunk = chunk.text
                        if text_chunk:
                            self.current_stream_content += text_chunk
                            yield {"content": text_chunk}

                    # Process any parts in the chunk
                    if hasattr(chunk, "candidates") and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, "content") and candidate.content:
                            content = candidate.content
                            if hasattr(content, "parts") and content.parts:
                                for part in content.parts:
                                    # Check for function calls
                                    if hasattr(part, "function_call") and not is_processing_tool_call:
                                        is_processing_tool_call = True
                                        function_call = part.function_call

                                        # Create tool call structure
                                        tool_call_id = f"gemini_call_{len(self.current_stream_tool_calls)}"
                                        current_tool_call = {
                                            "id": tool_call_id,
                                            "type": "function",
                                            "function": {
                                                "name": function_call.name,
                                                "arguments": json.dumps(function_call.args)
                                            }
                                        }

                                        # Add to tracking
                                        self.current_stream_tool_calls.append(
                                            current_tool_call)

                                        # Emit tool call
                                        yield {"type": "tool_calls", "tool_calls": [current_tool_call]}

                                        # Execute the tool
                                        try:
                                            tool_name = function_call.name
                                            tool_args = function_call.args

                                            if tool_name in self.tools_map:
                                                tool = self.tools_map[tool_name]
                                                result = tool(**tool_args)

                                                # Format result
                                                tool_result = {
                                                    "tool_call_id": tool_call_id,
                                                    "function_name": tool_name,
                                                    "result": result
                                                }

                                                # Add to tracking
                                                self.current_stream_tool_results.append(
                                                    tool_result)

                                                # Emit tool result
                                                yield {
                                                    "type": "tool_result",
                                                    "tool_call_id": tool_call_id,
                                                    "content": json.dumps(result)
                                                }

                                                # Make follow-up call with the tool result
                                                # Create tool result message
                                                result_message = {
                                                    "role": "user",
                                                    "parts": [
                                                        f"Tool {tool_name} returned: {json.dumps(result)}"
                                                    ]
                                                }

                                                # Add to messages and make new stream request
                                                follow_up_messages = formatted_messages.copy()
                                                follow_up_messages.append({
                                                    "role": "model",
                                                    "parts": [{"text": "I need to use a tool."}, part]
                                                })
                                                follow_up_messages.append(
                                                    result_message)

                                                follow_up_stream = model.generate_content(
                                                    follow_up_messages,
                                                    tools=self.tools_schema,
                                                    stream=True
                                                )

                                                # Process follow-up chunks
                                                async for follow_chunk in follow_up_stream:
                                                    if hasattr(follow_chunk, "text"):
                                                        text = follow_chunk.text
                                                        if text:
                                                            self.current_stream_content += text
                                                            yield {"content": text}
                                            else:
                                                error_msg = f"Tool {tool_name} not found"
                                                yield {
                                                    "type": "tool_result",
                                                    "tool_call_id": tool_call_id,
                                                    "content": json.dumps({"error": error_msg})
                                                }
                                        except Exception as e:
                                            error_msg = f"Error executing tool: {str(e)}"
                                            yield {
                                                "type": "tool_result",
                                                "tool_call_id": tool_call_id,
                                                "content": json.dumps({"error": error_msg})
                                            }

                                        # Reset tool call tracking
                                        is_processing_tool_call = False
                                        current_tool_call = None

                # Signal completion
                yield {"finish_reason": "stop"}

            except Exception as e:
                # Handle any errors during streaming
                error_msg = f"Streaming error: {str(e)}"
                yield {"content": f"\nError during response generation: {error_msg}", "finish_reason": "error"}

        else:
            # Fallback for unsupported providers
            # Generate a non-streaming response
            response = self.generate_response(messages, context)

            # Yield the entire content
            yield {"content": response["final_content"]}

            # Store for database
            self.current_stream_content = response["final_content"]

            # Collect tool calls and results
            for turn in response["conversation_turns"]:
                if turn.get("tool_calls"):
                    self.current_stream_tool_calls.extend(turn["tool_calls"])

                if turn.get("tool_results"):
                    self.current_stream_tool_results.extend(
                        turn["tool_results"])

            # Signal completion
            yield {"finish_reason": "stop"}

    async def get_final_streaming_content(self) -> str:
        """Get the complete content accumulated during streaming"""
        return self.current_stream_content


# Singleton pattern
llm_service = LLMService()
