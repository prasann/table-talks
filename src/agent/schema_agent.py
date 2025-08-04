"""Schema Agent with function calling capabilities."""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Third-party imports
import requests

# Internal imports
from ..utils.logger import get_logger
from ..tools.tool_registry import ToolRegistry


class SchemaAgent:
    """Unified agent for processing natural language queries about data schemas.
    
    Uses function calling only with Ollama models that support it.
    Requires phi4-mini-fc or similar function calling enabled models.
    """
    
    def __init__(self, metadata_store, model_name: str = "phi4-mini-fc", base_url: str = "http://localhost:11434"):
        """Initialize SchemaAgent with function calling only."""
        self.tool_registry = ToolRegistry(metadata_store)
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger("tabletalk.schema_agent")
        
        # Detect function calling support - required for this simplified agent
        self.supports_function_calling = self._detect_function_calling()
        
        if not self.supports_function_calling:
            raise ValueError(f"Model {model_name} doesn't support function calling. Please use a function calling enabled model like phi4-mini-fc")
            
        self.logger.info(f"SchemaAgent initialized with function calling mode for model: {model_name}")
        # Detailed initialization logged only in debug mode
        self.logger.debug(f"Base URL: {base_url}, Tool registry initialized with {len(self.tool_registry.tools)} tools")
    
    def _detect_function_calling(self) -> bool:
        """Detect if model supports native function calling."""
        function_calling_indicators = ["phi4-mini-fc", "phi4-mini:fc", "phi4:fc"]
        
        # Exact match for known function calling models
        if self.model_name in function_calling_indicators:
            return True
            
        # Pattern-based detection
        if "phi4" in self.model_name.lower() and ("fc" in self.model_name.lower() or "function" in self.model_name.lower()):
            return True
            
        return False
    
    def query(self, user_query: str) -> str:
        """Process a user query using function calling only."""
        # Log only the essential query info
        self.logger.debug(f"Processing query with function calling: {user_query[:100]}...")
        
        try:
            result, tools_used = self._process_with_function_calling(user_query)
            # Store the tools used for the session logger
            self._last_tools_used = tools_used
            # No need to log result length - session logger handles this
            return result
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            raise

    def get_last_tools_used(self) -> List[str]:
        """Get the tools used in the last query."""
        return getattr(self, '_last_tools_used', [])
    
    def _process_with_function_calling(self, query: str) -> Tuple[str, List[str]]:
        """Process query using native Ollama function calling."""
        self.logger.debug("Starting function calling processing")
        tools = self._get_function_calling_tools()
        
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a data schema analysis assistant. You have access to specialized tools for analyzing database schemas, data files, and metadata. Each tool has a clear description of its purpose and parameters.\n\nChoose the most appropriate tool(s) based on the user's question. When tools have optional parameters, use them to provide more targeted results (e.g., filter for specific files or columns when the user asks about specific entities).\n\nAlways aim to give precise, relevant answers rather than overwhelming the user with all available data."
                    },
                    {
                        "role": "user", 
                        "content": query
                    }
                ],
                "tools": tools,
                "stream": False
            }
            self.logger.debug(f"Sending function calling request with {len(tools)} tools")
            
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                self.logger.debug(f"Function calling API response: {response_data}")
                
                # Debug: Show what the LLM decided to do
                message = response_data.get("message", {})
                if message.get("tool_calls"):
                    tool_calls = message.get("tool_calls", [])
                    self.logger.debug(f"LLM decided to call {len(tool_calls)} functions:")
                    for i, tool_call in enumerate(tool_calls):
                        func_name = tool_call.get("function", {}).get("name", "unknown")
                        func_args = tool_call.get("function", {}).get("arguments", {})
                        self.logger.debug(f"  Function {i+1}: {func_name}({func_args})")
                else:
                    self.logger.debug(f"LLM chose not to call any functions. Direct response: {message.get('content', 'No content')[:200]}...")
                
                return self._execute_function_calls(response_data, query)
            else:
                self.logger.error(f"Function calling API error: {response.status_code} - {response.text}")
                return "I'm having trouble connecting to the language model. Please try again.", []
                
        except Exception as e:
            self.logger.error(f"Function calling failed: {e}")
            return "I'm having trouble with function calling. Please try rephrasing your question.", []
    
    def _get_function_calling_tools(self) -> List[Dict]:
        """Get tool definitions for function calling from the unified tool registry."""
        return self.tool_registry.get_ollama_function_schemas()
    
    def _execute_function_calls(self, response_data: dict, original_query: str) -> Tuple[str, List[str]]:
        """Execute function calls and return formatted results and tools used."""
        try:
            message = response_data.get("message", {})
            tool_calls = message.get("tool_calls", [])
            tools_used = []
            
            if not tool_calls:
                # No function calls, return direct response
                content = message.get("content", "No response generated")
                self.logger.debug(f"LLM chose not to call any functions. Direct response: {content[:100]}...")
                return content, []
            
            self.logger.info(f"LLM decided to call {len(tool_calls)} functions:")
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function", {})
                function_name = function.get("name")
                arguments = function.get("arguments", {})
                self.logger.info(f"  Function {i+1}: {function_name}({arguments})")
            
            self.logger.debug(f"Executing {len(tool_calls)} function calls")
            results = []
            
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function", {})
                function_name = function.get("name")
                arguments = function.get("arguments", {})
                
                self.logger.debug(f"Function call {i+1}: {function_name} with args: {arguments}")
                
                try:
                    # Execute the function using the tool registry
                    result = self.tool_registry.execute_tool(function_name, **arguments)
                    self.logger.debug(f"Function {function_name} result length: {len(result)} characters")
                    results.append(result)
                    tools_used.append(function_name)
                    
                except Exception as e:
                    error_msg = f"Function execution failed: {str(e)}"
                    self.logger.error(f"Function execution failed: {str(e)}")
                    results.append(error_msg)
                    # Still track the tool even if it failed
                    tools_used.append(function_name)
            
            combined_result = "\n\n".join(results)
            self.logger.debug(f"Combined function call results length: {len(combined_result)} characters")
            return combined_result, tools_used
            
        except Exception as e:
            self.logger.error(f"Function execution failed: {e}")
            return f"Error executing functions: {e}", []
    
    def check_llm_availability(self) -> bool:
        """Check if function calling is available."""
        return self.supports_function_calling
    
    def get_status(self) -> dict:
        """Get agent status information."""
        return {
            'agent_type': 'SchemaAgent',
            'mode': 'function_calling',
            'model_name': self.model_name,
            'base_url': self.base_url,
            'llm_available': self.supports_function_calling,  # For backward compatibility
            'function_calling': self.supports_function_calling,
            'tools_available': len(self.tool_registry.tools),
            'tool_names': list(self.tool_registry.tools.keys()),
            'capabilities': ["native_function_calling", "parameter_extraction", "optimal_reliability"]
        }
