"""Ollama multi-model client for TableTalk."""

import time
import json
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp

from .base_client import BaseModelClient, ModelResponse, QueryClassification
from ...utils.logger import get_logger


class OllamaMultiModelClient(BaseModelClient):
    """Enhanced Ollama client with multi-model support."""
    
    # Model configurations for different tasks
    MODEL_CONFIGS = {
        "function_calling": {
            "model": "phi4-mini-fc",
            "description": "Function calling enabled model for tool selection",
            "good_for": ["query_classification", "tool_selection", "structured_output"]
        },
        "code_generation": {
            "model": "codellama:34b", 
            "description": "Code generation specialist",
            "good_for": ["python_scripts", "jupyter_notebooks", "code_analysis"]
        },
        "general": {
            "model": "llama3.1:8b",
            "description": "Fast general purpose model",
            "good_for": ["simple_queries", "text_processing", "summaries"]
        },
        "advanced_code": {
            "model": "qwen2.5-coder",
            "description": "Advanced coding and analysis",
            "good_for": ["complex_algorithms", "optimization", "code_review"]
        }
    }
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 default_model_type: str = "function_calling",
                 config: Dict[str, Any] = None):
        self.base_url = base_url.rstrip('/')
        self.default_model_type = default_model_type
        self.available_models = {}
        
        # Use the default model name for the base class
        default_model = self.MODEL_CONFIGS[default_model_type]["model"]
        super().__init__(default_model, config or {})
        
        self.logger = get_logger("tabletalk.ollama_client")
        self.session = None
        
    async def initialize(self) -> bool:
        """Initialize Ollama client and check available models."""
        try:
            self.session = aiohttp.ClientSession()
            
            # Check if Ollama is running
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    installed_models = {model["name"].split(":")[0] for model in models_data["models"]}
                    
                    # Check which of our configured models are available
                    for model_type, config in self.MODEL_CONFIGS.items():
                        model_name = config["model"].split(":")[0]
                        if model_name in installed_models:
                            self.available_models[model_type] = config
                            
                    self.is_available = len(self.available_models) > 0
                    
                    if self.is_available:
                        self.logger.info(f"Ollama client initialized. Available models: {list(self.available_models.keys())}")
                    else:
                        self.logger.warning("Ollama is running but no configured models are available")
                        
                    return self.is_available
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama client: {e}")
            self.is_available = False
            if self.session:
                await self.session.close()
                self.session = None
                
        return False
        
    async def classify_query(self, query: str, context: Dict[str, Any] = None) -> QueryClassification:
        """Use the function calling model to intelligently classify queries."""
        
        # Create classification prompt
        classification_prompt = f"""
        You are a query classifier for a data analysis system called TableTalk. 
        Analyze the following user query and classify it into one of these workflow types:
        
        1. "schema_exploration" - Questions about database schemas, table structures, columns
        2. "data_discovery" - Questions about finding files, searching for data, metadata queries  
        3. "analysis" - Questions about data quality, statistics, analysis, issues
        4. "basic_query" - General questions or unclear requests
        
        Query: "{query}"
        
        Available context: {json.dumps(context or {}, indent=2)}
        
        Respond with a JSON object containing:
        {{
            "workflow_type": "one of the four types above",
            "confidence": number between 0.0 and 1.0,
            "reasoning": "explanation of why you chose this classification",
            "suggested_tools": ["list", "of", "tools", "likely", "needed"],
            "complexity": "simple, moderate, or complex"
        }}
        """
        
        try:
            # Use function calling model for classification
            model_config = self.available_models.get("function_calling", self.available_models[list(self.available_models.keys())[0]])
            response = await self._generate_response(classification_prompt, model_config["model"])
            
            if response.success:
                # Parse the JSON response - handle markdown code blocks from Ollama models
                try:
                    response_content = response.content.strip()
                    
                    # Extract JSON from markdown code blocks if present
                    if response_content.startswith('```json') and response_content.endswith('```'):
                        # Remove markdown formatting
                        json_content = response_content[7:-3].strip()  # Remove ```json and ```
                    elif response_content.startswith('```') and response_content.endswith('```'):
                        # Handle generic code blocks
                        json_content = response_content[3:-3].strip()
                    else:
                        json_content = response_content
                    
                    classification_data = json.loads(json_content)
                    return QueryClassification(
                        workflow_type=classification_data.get("workflow_type", "basic_query"),
                        confidence=float(classification_data.get("confidence", 0.5)),
                        reasoning=classification_data.get("reasoning", "Default classification"),
                        suggested_tools=classification_data.get("suggested_tools", []),
                        complexity=classification_data.get("complexity", "moderate")
                    )
                except (json.JSONDecodeError, ValueError) as e:
                    self.logger.warning(f"Failed to parse classification JSON: {e}")
                    self.logger.debug(f"Raw response content: {response.content}")
                    # Fall back to keyword-based classification
                    return self._fallback_classification(query)
            else:
                return self._fallback_classification(query)
                
        except Exception as e:
            self.logger.error(f"Query classification failed: {e}")
            return self._fallback_classification(query)
            
    def _fallback_classification(self, query: str) -> QueryClassification:
        """Fallback keyword-based classification if LLM classification fails."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["schema", "structure", "columns", "table"]):
            return QueryClassification(
                workflow_type="schema_exploration",
                confidence=0.7,
                reasoning="Keyword-based classification (fallback)",
                suggested_tools=["get_schemas"],
                complexity="simple"
            )
        elif any(word in query_lower for word in ["search", "find", "contains", "where"]):
            return QueryClassification(
                workflow_type="data_discovery", 
                confidence=0.7,
                reasoning="Keyword-based classification (fallback)",
                suggested_tools=["search_metadata"],
                complexity="moderate"
            )
        elif any(word in query_lower for word in ["analyze", "analysis", "quality", "issues", "statistics"]):
            return QueryClassification(
                workflow_type="analysis",
                confidence=0.7, 
                reasoning="Keyword-based classification (fallback)",
                suggested_tools=["get_statistics"],
                complexity="moderate"
            )
        else:
            return QueryClassification(
                workflow_type="basic_query",
                confidence=0.5,
                reasoning="Default classification (fallback)",
                suggested_tools=["get_files"],
                complexity="simple"
            )
            
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> ModelResponse:
        """Generate response using the most appropriate model."""
        
        # For now, use the default model type
        model_config = self.available_models.get(self.default_model_type)
        if not model_config:
            # Use any available model
            model_config = self.available_models[list(self.available_models.keys())[0]]
            
        return await self._generate_response(prompt, model_config["model"], context)
        
    async def _generate_response(self, prompt: str, model_name: str, context: Dict[str, Any] = None) -> ModelResponse:
        """Internal method to generate response from specific model."""
        start_time = time.time()
        
        try:
            if not self.session:
                return ModelResponse(
                    content="",
                    model_used=model_name,
                    success=False,
                    error_message="Client not initialized"
                )
                
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.get("temperature", 0.1),
                    "num_predict": self.config.get("max_tokens", 3000)
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.get("timeout", 120))
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    execution_time = time.time() - start_time
                    
                    return ModelResponse(
                        content=result.get("response", ""),
                        model_used=model_name,
                        tokens_used=result.get("eval_count"),
                        execution_time=execution_time,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    return ModelResponse(
                        content="",
                        model_used=model_name,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            return ModelResponse(
                content="",
                model_used=model_name,
                execution_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
            
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Ollama model capabilities."""
        return {
            "function_calling": "function_calling" in self.available_models,
            "code_generation": "code_generation" in self.available_models,
            "local_execution": True,
            "cost_per_token": 0.0,
            "available_model_types": list(self.available_models.keys()),
            "supports_streaming": True,
            "max_context_length": 32768  # Typical for most Ollama models
        }
        
    def estimate_cost(self, query: str) -> float:
        """Ollama models are free to use locally."""
        return 0.0
        
    async def close(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
            
    def select_best_model_for_task(self, task_type: str) -> Optional[str]:
        """Select the best available model for a specific task."""
        task_preferences = {
            "query_classification": ["function_calling", "general"],
            "code_generation": ["code_generation", "advanced_code", "function_calling"],
            "analysis": ["function_calling", "general"],
            "general": ["general", "function_calling"]
        }
        
        preferences = task_preferences.get(task_type, ["function_calling", "general"])
        
        for model_type in preferences:
            if model_type in self.available_models:
                return self.available_models[model_type]["model"]
                
        # Return any available model
        if self.available_models:
            return list(self.available_models.values())[0]["model"]
            
        return None