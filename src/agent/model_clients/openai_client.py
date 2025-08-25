"""OpenAI GPT client for TableTalk code generation and advanced analysis."""

import time
import json
import os
from typing import Dict, Any, List, Optional
import openai

from .base_client import BaseModelClient, ModelResponse, QueryClassification
from ...utils.logger import get_logger


class OpenAIModelClient(BaseModelClient):
    """OpenAI GPT client for advanced code generation capabilities."""
    
    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
    }
    
    def __init__(self, api_key: Optional[str] = None, 
                 model_name: str = "gpt-4o-mini",
                 config: Dict[str, Any] = None):
        
        # Get API key from parameter, config, or environment
        self.api_key = api_key or (config or {}).get("api_key") or os.getenv("OPENAI_API_KEY")
        
        super().__init__(model_name, config or {})
        
        self.logger = get_logger("tabletalk.openai_client")
        self.client = None
        self.total_cost = 0.0
        
    async def initialize(self) -> bool:
        """Initialize OpenAI client and verify API access."""
        try:
            if not self.api_key:
                self.logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
                return False
                
            self.client = openai.OpenAI(api_key=self.api_key)
            
            # Test API access with a simple request
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            if response.choices:
                self.is_available = True
                self.logger.info(f"OpenAI client initialized successfully (model: {self.model_name})")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            
        self.is_available = False
        return False
        
    async def classify_query(self, query: str, context: Dict[str, Any] = None) -> QueryClassification:
        """Use GPT to intelligently classify queries with high accuracy."""
        
        classification_prompt = f"""
        You are an expert query classifier for TableTalk, a data analysis system.
        
        Analyze this user query and classify it into the most appropriate workflow:
        
        WORKFLOW TYPES:
        1. "schema_exploration" - Queries about database schemas, table structures, column definitions
        2. "data_discovery" - Queries about finding files, searching data, metadata exploration  
        3. "analysis" - Queries about data quality, statistics, analysis, identifying issues
        4. "basic_query" - General questions, file listings, or unclear requests
        
        USER QUERY: "{query}"
        
        CONTEXT: {json.dumps(context or {}, indent=2)}
        
        AVAILABLE TOOLS:
        - get_files: List available data files
        - get_schemas: Get database schemas and table structures  
        - search_metadata: Search for specific data elements
        - get_statistics: Get data quality and statistical information
        - find_relationships: Discover relationships between data elements
        - compare_schemas: Compare different schemas
        - analyze_quality: Analyze data quality issues
        - get_sample_data: Retrieve sample data from tables
        
        Respond with ONLY a valid JSON object:
        {{
            "workflow_type": "one of the four workflow types",
            "confidence": 0.95,
            "reasoning": "detailed explanation of classification decision",
            "suggested_tools": ["most_relevant", "tools", "for_this_query"],
            "complexity": "simple|moderate|complex"
        }}
        """
        
        try:
            if not self.client:
                return self._fallback_classification(query)
                
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            if response.choices and response.choices[0].message.content:
                # Track cost
                self._track_cost(response.usage)
                
                # Parse JSON response
                try:
                    content = response.choices[0].message.content.strip()
                    # Handle potential code blocks
                    if content.startswith("```json"):
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].strip()
                        
                    classification_data = json.loads(content)
                    
                    return QueryClassification(
                        workflow_type=classification_data.get("workflow_type", "basic_query"),
                        confidence=min(float(classification_data.get("confidence", 0.8)), 1.0),
                        reasoning=classification_data.get("reasoning", "GPT classification"),
                        suggested_tools=classification_data.get("suggested_tools", []),
                        complexity=classification_data.get("complexity", "moderate")
                    )
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to parse GPT classification response: {e}")
                    return self._fallback_classification(query)
                    
        except Exception as e:
            self.logger.error(f"GPT query classification failed: {e}")
            
        return self._fallback_classification(query)
        
    def _fallback_classification(self, query: str) -> QueryClassification:
        """Fallback classification when GPT is unavailable."""
        query_lower = query.lower()
        
        # More sophisticated keyword matching than the basic version
        schema_keywords = ["schema", "structure", "columns", "table", "database", "fields"]
        discovery_keywords = ["search", "find", "contains", "where", "which", "what files", "metadata"]
        analysis_keywords = ["analyze", "analysis", "quality", "issues", "statistics", "problems", "check"]
        
        if any(word in query_lower for word in schema_keywords):
            return QueryClassification(
                workflow_type="schema_exploration",
                confidence=0.8,
                reasoning="Schema keywords detected (fallback classification)",
                suggested_tools=["get_schemas", "get_sample_data"],
                complexity="simple"
            )
        elif any(word in query_lower for word in discovery_keywords):
            return QueryClassification(
                workflow_type="data_discovery",
                confidence=0.8, 
                reasoning="Discovery keywords detected (fallback classification)",
                suggested_tools=["search_metadata", "get_files"],
                complexity="moderate"
            )
        elif any(word in query_lower for word in analysis_keywords):
            return QueryClassification(
                workflow_type="analysis",
                confidence=0.8,
                reasoning="Analysis keywords detected (fallback classification)", 
                suggested_tools=["get_statistics", "analyze_quality"],
                complexity="moderate"
            )
        else:
            return QueryClassification(
                workflow_type="basic_query",
                confidence=0.6,
                reasoning="Default classification (no clear keywords found)",
                suggested_tools=["get_files"],
                complexity="simple"
            )
            
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> ModelResponse:
        """Generate response using GPT."""
        start_time = time.time()
        
        try:
            if not self.client:
                return ModelResponse(
                    content="",
                    model_used=self.model_name,
                    success=False,
                    error_message="Client not initialized"
                )
                
            messages = [{"role": "user", "content": prompt}]
            
            # Add context if provided
            if context:
                context_str = json.dumps(context, indent=2)
                messages.insert(0, {
                    "role": "system", 
                    "content": f"Additional context:\n{context_str}"
                })
                
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.config.get("temperature", 0.1),
                max_tokens=self.config.get("max_tokens", 3000)
            )
            
            if response.choices and response.choices[0].message.content:
                execution_time = time.time() - start_time
                cost = self._track_cost(response.usage)
                
                return ModelResponse(
                    content=response.choices[0].message.content,
                    model_used=self.model_name,
                    tokens_used=response.usage.total_tokens,
                    cost=cost,
                    execution_time=execution_time,
                    success=True
                )
                
        except Exception as e:
            return ModelResponse(
                content="",
                model_used=self.model_name,
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
        return ModelResponse(
            content="",
            model_used=self.model_name,
            success=False,
            error_message="No response generated"
        )
        
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI model capabilities."""
        return {
            "function_calling": True,
            "code_generation": True,
            "local_execution": False,
            "cost_per_token": self.PRICING.get(self.model_name, {"input": 0.01, "output": 0.03}),
            "max_context_length": self._get_context_length(),
            "supports_streaming": True,
            "supports_vision": self.model_name in ["gpt-4-vision-preview", "gpt-4o"],
            "quality_rating": "high"  # Generally higher quality than local models
        }
        
    def _get_context_length(self) -> int:
        """Get context window size for the model."""
        context_lengths = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-3.5-turbo": 16385,
            "gpt-3.5-turbo-16k": 16385
        }
        return context_lengths.get(self.model_name, 8192)
        
    def estimate_cost(self, query: str) -> float:
        """Estimate cost for processing the query."""
        pricing = self.PRICING.get(self.model_name)
        if not pricing:
            return 0.01  # Default estimate
            
        # Rough token estimation (4 chars per token)
        estimated_input_tokens = len(query) / 4
        estimated_output_tokens = min(estimated_input_tokens * 2, 1000)  # Assume 2x output, max 1k
        
        cost = (estimated_input_tokens / 1000 * pricing["input"] + 
                estimated_output_tokens / 1000 * pricing["output"])
                
        return round(cost, 4)
        
    def _track_cost(self, usage) -> float:
        """Track actual cost from API usage."""
        if not usage:
            return 0.0
            
        pricing = self.PRICING.get(self.model_name)
        if not pricing:
            return 0.0
            
        cost = (usage.prompt_tokens / 1000 * pricing["input"] + 
                usage.completion_tokens / 1000 * pricing["output"])
                
        self.total_cost += cost
        return round(cost, 4)
        
    def get_total_cost(self) -> float:
        """Get total cost accumulated during this session."""
        return round(self.total_cost, 4)
        
    def reset_cost_tracking(self):
        """Reset cost tracking counter."""
        self.total_cost = 0.0