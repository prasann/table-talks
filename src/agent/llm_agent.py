"""LLM Agent for natural language query processing."""

import logging
from typing import List
import requests

try:
    from ..utils.logger import get_logger
    from .strategy_factory import QueryStrategyFactory
    from ..tools.schema_tools import SchemaTools
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger
    from agent.strategy_factory import QueryStrategyFactory
    from tools.schema_tools import SchemaTools


class LLMAgent:
    """Agent for processing natural language queries about data schemas."""
    
    def __init__(self, schema_tools: SchemaTools, model_name: str = "phi3", base_url: str = "http://localhost:11434"):
        """Initialize the LLM agent with strategy-based query processing."""
        self.schema_tools = schema_tools
        self.model_name = model_name
        self.base_url = base_url
        self.logger = get_logger("tabletalk.llm_agent")
        
        # Initialize strategy factory
        self.strategy_factory = QueryStrategyFactory()
        
        # For structured output strategy, we might need LangChain LLM
        self.llm = None
        if not self.strategy_factory._supports_function_calling(model_name):
            self._initialize_llm()
        
        # Create appropriate strategy
        self.query_strategy = self.strategy_factory.create_strategy(
            model_name=model_name,
            base_url=base_url,
            llm_agent=self if self.llm else None,
            schema_tools=schema_tools
        )
        
        # Log strategy selection
        strategy_info = self.query_strategy.get_strategy_info()
        self.logger.info(f"Initialized with {strategy_info['name']} ({strategy_info['type']})")
    
    def _initialize_llm(self):
        """Initialize the LLM connection with structured output support."""
        try:
            from langchain_ollama import ChatOllama
            
            # Test if Ollama is available
            test_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if test_response.status_code == 200:
                self.llm = ChatOllama(
                    model=self.model_name,
                    base_url=self.base_url,
                    temperature=0.1
                )
                self.logger.info(f"LLM initialized with model: {self.model_name}")
                
                # Check if model supports structured JSON output
                model_details = None
                try:
                    model_response = requests.get(f"{self.base_url}/api/tags", timeout=5).json()
                    # Log available models for debugging
                    self.logger.debug(f"Available models: {[m.get('name') for m in model_response.get('models', [])]}") 
                    
                    # Phi models generally have good structured output capabilities
                    structured_output_supported = "phi" in self.model_name.lower()
                    if not structured_output_supported:
                        self.logger.warning(
                            f"Model {self.model_name} may have limited structured output capabilities. "
                            f"Consider using phi3 or phi4 for better results."
                        )
                except Exception as e:
                    self.logger.warning(f"Could not check model capabilities: {e}")
                
            else:
                self.logger.warning("Ollama not available, using basic mode")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {str(e)}. Using basic mode.")
    
    def process_query(self, query: str) -> dict:
        """Process a natural language query using the configured strategy."""
        try:
            # Log query processing start
            strategy_info = self.query_strategy.get_strategy_info()
            self.logger.info(f"Processing query using {strategy_info['name']}: {query[:100]}...")
            
            # Parse query using strategy
            parsing_result = self.query_strategy.parse_query(query)
            if not parsing_result["success"]:
                return {
                    "success": False,
                    "error": parsing_result.get("error", "Failed to parse query"),
                    "query": query
                }
            
            # Execute the plan
            execution_result = self.query_strategy.execute_plan(parsing_result["parsed_query"], self.schema_tools)
            if not execution_result["success"]:
                return {
                    "success": False,
                    "error": execution_result.get("error", "Failed to execute query plan"),
                    "query": query,
                    "parsed_query": parsing_result["parsed_query"]
                }
            
            # Synthesize response
            synthesis_result = self.query_strategy.synthesize_response(
                query, 
                parsing_result["parsed_query"], 
                execution_result["result"]
            )
            
            return {
                "success": synthesis_result["success"],
                "response": synthesis_result.get("response", ""),
                "error": synthesis_result.get("error"),
                "query": query,
                "parsed_query": parsing_result["parsed_query"],
                "execution_result": execution_result["result"]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "query": query
            }
    
    def query(self, user_query: str) -> str:
        """Process a user query and return a response using the configured strategy."""
        self.logger.info(f"Processing query: {user_query[:100]}...")
        
        try:
            # Get available files for context
            available_files = self._get_available_files()
            
            # Process query using strategy
            result = self.process_query(user_query)
            
            if result["success"]:
                return result["response"]
            else:
                error_msg = result.get("error", "Unknown error occurred")
                self.logger.error(f"Query processing failed: {error_msg}")
                return f"I encountered an error: {error_msg}\n\nPlease try rephrasing your question."
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return f"I encountered an error: {str(e)}\n\nPlease try rephrasing your question."
    
    def _get_available_files(self) -> List[str]:
        """Get list of available files for context."""
        try:
            files_result = self.schema_tools.list_all_files()
            # Simple extraction - just get lines with file extensions
            lines = files_result.split('\n')
            file_names = []
            for line in lines:
                if '.csv' in line or '.parquet' in line:
                    # Extract filename from lines like "- customers.csv: 6 cols, 6 rows"
                    if ':' in line:
                        filename = line.split(':')[0].strip().lstrip('- ')
                        if filename.endswith(('.csv', '.parquet')):
                            file_names.append(filename)
            return file_names
        except Exception:
            return []
    
    def check_llm_availability(self) -> bool:
        """Check if LLM is available."""
        return self.llm is not None

    def get_status(self) -> dict:
        """Get agent status information."""
        strategy_info = self.query_strategy.get_strategy_info()
        return {
            'strategy_name': strategy_info['name'],
            'strategy_type': strategy_info['type'],
            'llm_available': self.llm is not None,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'function_calling': strategy_info['type'] == 'function_calling'
        }
