"""
SIMPLIFIED AGENT CONCEPT - Combining Strategy Pattern into Single Smart Agent
This demonstrates how we could simplify the current strategy-based architecture.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any


class SmartAgent:
    """Simplified agent that auto-detects capabilities and uses best approach."""
    
    def __init__(self, schema_tools, model_name: str = "phi3", base_url: str = "http://localhost:11434"):
        """Initialize smart agent with auto-capability detection."""
        self.schema_tools = schema_tools
        self.model_name = model_name
        self.base_url = base_url
        self.logger = logging.getLogger("tabletalk.agent")
        
        # Auto-detect capabilities once at startup
        self.supports_function_calling = self._detect_function_calling()
        self.llm = self._init_llm() if not self.supports_function_calling else None
        
        self.logger.info(f"Initialized with {'function calling' if self.supports_function_calling else 'structured output'}")
    
    def _detect_function_calling(self) -> bool:
        """Simple capability detection."""
        return "phi4" in self.model_name.lower() and ("fc" in self.model_name.lower() or "function" in self.model_name.lower())
    
    def _init_llm(self):
        """Initialize LLM for structured output (only when needed)."""
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(model=self.model_name, base_url=self.base_url, temperature=0.1)
        except Exception as e:
            self.logger.warning(f"LLM init failed: {e}")
            return None
    
    def process_query(self, query: str) -> str:
        """Process query using best available method."""
        try:
            if self.supports_function_calling:
                return self._process_with_function_calling(query)
            elif self.llm:
                return self._process_with_structured_output(query)
            else:
                return self._process_with_patterns(query)
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return f"Error: {e}"
    
    def _process_with_function_calling(self, query: str) -> str:
        """Native function calling approach."""
        # Tool definitions (same as current function_calling_strategy.py)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_file_schema",
                    "description": "Get detailed schema for a specific file",
                    "parameters": {
                        "type": "object",
                        "properties": {"file_name": {"type": "string"}},
                        "required": ["file_name"]
                    }
                }
            },
            # ... other tools
        ]
        
        # Make API call
        response = requests.post(f"{self.base_url}/api/chat", json={
            "model": self.model_name,
            "messages": [{"role": "user", "content": query}],
            "tools": tools
        })
        
        # Process response and execute tools
        if response.status_code == 200:
            return self._execute_function_calls(response.json())
        else:
            return "Function calling failed"
    
    def _process_with_structured_output(self, query: str) -> str:
        """LangChain structured output approach."""
        # Prompt for structured output (same as current structured_output_strategy.py)
        prompt = f"""
        Analyze this query and respond with JSON:
        Query: {query}
        
        Response format:
        {{
            "tool": "tool_name",
            "parameters": {{}},
            "explanation": "why this tool"
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            parsed = json.loads(response.content)
            return self._execute_structured_plan(parsed)
        except Exception as e:
            return self._process_with_patterns(query)  # Fallback
    
    def _process_with_patterns(self, query: str) -> str:
        """Simple pattern matching fallback."""
        query_lower = query.lower()
        
        if "files" in query_lower or "tables" in query_lower:
            return self.schema_tools.list_all_files()
        elif "schema" in query_lower:
            # Try to extract filename
            words = query.split()
            for word in words:
                if ".csv" in word or ".parquet" in word:
                    return self.schema_tools.get_file_schema(word)
            return "Please specify a filename"
        else:
            return "Try asking about 'files' or 'schema of filename.csv'"
    
    def _execute_function_calls(self, response_data: dict) -> str:
        """Execute function calls and return results."""
        # Implementation same as current function calling strategy
        pass
    
    def _execute_structured_plan(self, plan: dict) -> str:
        """Execute structured plan and return results."""
        # Implementation same as current structured output strategy  
        pass
    
    def get_status(self) -> dict:
        """Get current agent status."""
        return {
            'mode': 'function_calling' if self.supports_function_calling else 'structured_output' if self.llm else 'pattern_matching',
            'model': self.model_name,
            'capabilities': ['function_calling'] if self.supports_function_calling else ['structured_output'] if self.llm else ['pattern_matching']
        }


# BENEFITS OF THIS APPROACH:
# 1. Single file instead of 5 files (query_strategy.py, function_calling_strategy.py, structured_output_strategy.py, strategy_factory.py, llm_agent.py)
# 2. No abstract base classes or factory pattern overhead
# 3. Auto-detection at startup (no runtime strategy switching complexity)
# 4. Same functionality, much simpler architecture
# 5. Easier to understand, test, and maintain
# 6. Natural fallback chain: function_calling -> structured_output -> pattern_matching
