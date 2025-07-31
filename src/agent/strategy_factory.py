"""Strategy factory for creating query processing strategies in TableTalk."""

import logging
from typing import Dict, Any, Optional

try:
    from ..utils.logger import get_logger
    from .query_strategy import QueryProcessingStrategy
    from .function_calling_strategy import FunctionCallingStrategy
    from .structured_output_strategy import StructuredOutputStrategy
    from .sql_agent_strategy import SQLAgentStrategy
    from .sql_agent_langgraph import SQLAgentLangGraph
    from .sql_agent_simple import SQLAgentSimple
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger
    from agent.query_strategy import QueryProcessingStrategy
    from agent.function_calling_strategy import FunctionCallingStrategy
    from agent.structured_output_strategy import StructuredOutputStrategy
    from agent.sql_agent_strategy import SQLAgentStrategy
    from agent.sql_agent_langgraph import SQLAgentLangGraph
    from agent.sql_agent_simple import SQLAgentSimple


class QueryStrategyFactory:
    """Factory for creating appropriate query processing strategies."""
    
    def __init__(self):
        """Initialize the strategy factory."""
        self.logger = get_logger("tabletalk.strategy_factory")
        
    def create_strategy(self, 
                       model_name: str, 
                       base_url: str = "http://localhost:11434",
                       llm_agent: Optional[Any] = None,
                       schema_tools: Optional[Any] = None,
                       strategy_type: Optional[str] = None) -> QueryProcessingStrategy:
        """Create the appropriate strategy based on model capabilities or explicit type.
        
        Args:
            model_name: Name of the LLM model
            base_url: Base URL for Ollama API
            llm_agent: LLM agent instance (for structured output strategy)
            schema_tools: Schema tools instance (for function calling strategy)
            strategy_type: Explicit strategy type ("function_calling", "structured_output", "sql_agent")
            
        Returns:
            Appropriate QueryProcessingStrategy instance
        """
        
        # If explicit strategy type is specified, use it
        if strategy_type:
            if strategy_type == "sql_agent":
                self.logger.info(f"Creating SQLAgentStrategy for model: {model_name}")
                return SQLAgentStrategy(llm_agent=llm_agent)
            elif strategy_type == "sql_agent_langgraph":
                self.logger.info(f"Creating SQLAgentLangGraph for model: {model_name}")
                return SQLAgentLangGraph(llm_agent=llm_agent)
            elif strategy_type == "sql_agent_simple":
                self.logger.info(f"Creating SQLAgentSimple for model: {model_name}")
                return SQLAgentSimple(llm_agent=llm_agent)
            elif strategy_type == "function_calling":
                self.logger.info(f"Creating FunctionCallingStrategy for model: {model_name}")
                return FunctionCallingStrategy(base_url=base_url, model=model_name, schema_tools=schema_tools)
            elif strategy_type == "structured_output":
                self.logger.info(f"Creating StructuredOutputStrategy for model: {model_name}")
                return StructuredOutputStrategy(llm_agent=llm_agent)
        
        # Auto-determine strategy based on model capabilities
        if self._supports_function_calling(model_name):
            self.logger.info(f"Creating FunctionCallingStrategy for model: {model_name}")
            return FunctionCallingStrategy(base_url=base_url, model=model_name, schema_tools=schema_tools)
        else:
            self.logger.info(f"Creating StructuredOutputStrategy for model: {model_name}")
            return StructuredOutputStrategy(llm_agent=llm_agent)
    
    def _supports_function_calling(self, model_name: str) -> bool:
        """Determine if a model supports native function calling.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if the model supports function calling, False otherwise
        """
        # Check for models that support native function calling
        function_calling_models = [
            "phi4-mini-fc",  # Our custom function calling model
            "phi4-mini:fc",  # Alternative naming
            "phi4:fc",       # Alternative naming
        ]
        
        # Exact match for known function calling models
        if model_name in function_calling_models:
            return True
            
        # Pattern-based detection for phi4 models with function calling indicators
        if "phi4" in model_name.lower() and ("fc" in model_name.lower() or "function" in model_name.lower()):
            return True
            
        return False
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available strategies.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            "function_calling": {
                "name": "Function Calling Strategy",
                "description": "Native Ollama function calling for precise tool selection",
                "supported_models": ["phi4-mini-fc", "phi4-mini:fc", "phi4:fc"],
                "capabilities": ["native_function_calling", "parameter_extraction", "optimal_reliability"],
                "performance": "optimal",
                "recommended": True
            },
            "structured_output": {
                "name": "Structured Output Strategy", 
                "description": "LangChain integration with structured prompting",
                "supported_models": ["phi3:mini", "phi3", "phi4", "llama2", "mistral"],
                "capabilities": ["structured_prompting", "json_parsing", "pattern_fallback"],
                "performance": "good",
                "recommended": False
            },
            "sql_agent": {
                "name": "SQL Agent Strategy",
                "description": "Direct SQL execution with simple retry logic",
                "supported_models": ["phi3", "phi4", "llama2", "mistral", "gpt-4", "claude"],
                "capabilities": ["natural_language_to_sql", "direct_execution", "basic_retry"],
                "performance": "good",
                "recommended": False,
                "use_case": "Simple SQL generation and execution"
            },
            "sql_agent_simple": {
                "name": "Simple SQL Agent Strategy",
                "description": "Lightweight SQL agent with rule-based generation and concise formatting",
                "supported_models": ["phi3", "phi4", "llama2", "mistral", "gpt-4", "claude"],
                "capabilities": ["rule_based_sql", "optional_llm_fallback", "concise_formatting", "fast_execution"],
                "performance": "fast",
                "recommended": True,
                "use_case": "Quick data queries with minimal overhead"
            },
            "sql_agent_langgraph": {
                "name": "LangGraph SQL Agent Strategy",
                "description": "Advanced LangGraph agent with multi-step reasoning and intelligent formatting",
                "supported_models": ["phi3", "phi4", "llama2", "mistral", "gpt-4", "claude"],
                "capabilities": ["advanced_sql_generation", "multi_step_reasoning", "intelligent_formatting", "error_recovery"],
                "performance": "excellent",
                "recommended": False,
                "use_case": "Complex data analysis with detailed explanations"
            }
        }
    
    def recommend_strategy(self, model_name: str) -> Dict[str, Any]:
        """Recommend the best strategy for a given model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with recommendation information
        """
        if self._supports_function_calling(model_name):
            return {
                "recommended_strategy": "function_calling",
                "reason": "Model supports native function calling for optimal performance",
                "confidence": "high",
                "alternative": None
            }
        elif "phi" in model_name.lower():
            return {
                "recommended_strategy": "structured_output",
                "reason": "Phi models work well with structured output prompting",
                "confidence": "medium",
                "alternative": "Consider upgrading to phi4-mini-fc for function calling"
            }
        else:
            return {
                "recommended_strategy": "structured_output",
                "reason": "Default strategy for general models",
                "confidence": "low", 
                "alternative": "Consider using a Phi model for better performance"
            }
