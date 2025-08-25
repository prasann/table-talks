"""Model manager for coordinating multiple model clients in TableTalk."""

import asyncio
from typing import Dict, Any, List, Optional, Union
import yaml
import os

from .model_clients import BaseModelClient, OllamaMultiModelClient, OpenAIModelClient, QueryClassification
from ..utils.logger import get_logger


class ModelManager:
    """Manages multiple model clients and provides intelligent model selection."""
    
    def __init__(self, config_path: str = None):
        self.logger = get_logger("tabletalk.model_manager")
        self.clients: Dict[str, BaseModelClient] = {}
        self.config = {}
        self.is_initialized = False
        
        # Load configuration
        if config_path:
            self._load_config(config_path)
        else:
            # Default config path
            config_file = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
            self._load_config(config_file)
            
    def _load_config(self, config_path: str):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            self.logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            self.config = self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails."""
        return {
            "models": {
                "primary": {
                    "type": "ollama",
                    "model": "phi4-mini-fc",
                    "base_url": "http://localhost:11434",
                    "temperature": 0.1,
                    "max_tokens": 3000,
                    "timeout": 120
                }
            },
            "langgraph": {
                "routing": {
                    "method": "keyword_based",  # Fallback to keywords if no config
                    "confidence_threshold": 0.7,
                    "fallback_to_keywords": True
                }
            }
        }
        
    async def initialize(self) -> bool:
        """Initialize all configured model clients."""
        try:
            models_config = self.config.get("models", {})
            
            for model_name, model_config in models_config.items():
                model_type = model_config.get("type", "ollama").lower()
                
                if model_type == "ollama":
                    client = OllamaMultiModelClient(
                        base_url=model_config.get("base_url", "http://localhost:11434"),
                        config=model_config
                    )
                elif model_type == "openai":
                    client = OpenAIModelClient(
                        api_key=model_config.get("api_key"),
                        model_name=model_config.get("model", "gpt-4o-mini"),
                        config=model_config
                    )
                else:
                    self.logger.warning(f"Unknown model type '{model_type}' for model '{model_name}'")
                    continue
                    
                # Initialize the client
                if await client.initialize():
                    self.clients[model_name] = client
                    self.logger.info(f"Model client '{model_name}' initialized successfully")
                else:
                    self.logger.warning(f"Failed to initialize model client '{model_name}'")
                    
            self.is_initialized = len(self.clients) > 0
            
            if self.is_initialized:
                self.logger.info(f"Model manager initialized with {len(self.clients)} clients: {list(self.clients.keys())}")
            else:
                self.logger.error("No model clients were successfully initialized")
                
            return self.is_initialized
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model manager: {e}")
            return False
            
    async def classify_query(self, query: str, context: Dict[str, Any] = None) -> QueryClassification:
        """Intelligently classify a query to determine the appropriate workflow."""
        
        routing_config = self.config.get("langgraph", {}).get("routing", {})
        routing_method = routing_config.get("method", "keyword_based")
        
        if routing_method == "llm_based" and self.clients:
            # Use LLM-based classification
            classification_model = routing_config.get("classification_model", "primary")
            client = self.clients.get(classification_model)
            
            if not client:
                # Use first available client
                client = list(self.clients.values())[0]
                
            if client:
                try:
                    classification = await client.classify_query(query, context)
                    
                    # Check confidence threshold
                    threshold = routing_config.get("confidence_threshold", 0.7)
                    if classification.confidence >= threshold:
                        self.logger.info(f"Query classified as '{classification.workflow_type}' with confidence {classification.confidence:.2f}")
                        return classification
                    else:
                        self.logger.info(f"Low confidence classification ({classification.confidence:.2f}), using fallback")
                        
                except Exception as e:
                    self.logger.error(f"LLM classification failed: {e}")
                    
        # Fall back to keyword-based classification
        if routing_config.get("fallback_to_keywords", True):
            return self._keyword_classification(query)
        else:
            # Return basic query as ultimate fallback
            return QueryClassification(
                workflow_type="basic_query",
                confidence=0.5,
                reasoning="Fallback classification - no method available",
                suggested_tools=["get_files"],
                complexity="simple"
            )
            
    def _keyword_classification(self, query: str) -> QueryClassification:
        """Improved keyword-based classification as fallback."""
        query_lower = query.lower()
        
        # More comprehensive keyword sets
        schema_patterns = [
            "schema", "structure", "columns", "table", "database", "fields",
            "show me", "describe", "what is", "definition", "format"
        ]
        
        discovery_patterns = [
            "search", "find", "contains", "where", "which", "what files",
            "metadata", "look for", "locate", "identify", "discover"
        ]
        
        analysis_patterns = [
            "analyze", "analysis", "quality", "issues", "statistics", 
            "problems", "check", "validate", "examine", "assess"
        ]
        
        # Score each category
        schema_score = sum(1 for pattern in schema_patterns if pattern in query_lower)
        discovery_score = sum(1 for pattern in discovery_patterns if pattern in query_lower)
        analysis_score = sum(1 for pattern in analysis_patterns if pattern in query_lower)
        
        max_score = max(schema_score, discovery_score, analysis_score)
        
        if max_score == 0:
            return QueryClassification(
                workflow_type="basic_query",
                confidence=0.6,
                reasoning="No specific keywords found - using default workflow",
                suggested_tools=["get_files"],
                complexity="simple"
            )
            
        confidence = min(0.85, 0.6 + (max_score * 0.1))  # Scale confidence based on matches
        
        if schema_score == max_score:
            return QueryClassification(
                workflow_type="schema_exploration",
                confidence=confidence,
                reasoning=f"Schema keywords detected (score: {schema_score})",
                suggested_tools=["get_schemas", "get_sample_data"],
                complexity="simple" if schema_score == 1 else "moderate"
            )
        elif discovery_score == max_score:
            return QueryClassification(
                workflow_type="data_discovery",
                confidence=confidence,
                reasoning=f"Discovery keywords detected (score: {discovery_score})",
                suggested_tools=["search_metadata", "get_files", "find_relationships"],
                complexity="moderate" if discovery_score > 1 else "simple"
            )
        else:  # analysis_score == max_score
            return QueryClassification(
                workflow_type="analysis",
                confidence=confidence,
                reasoning=f"Analysis keywords detected (score: {analysis_score})",
                suggested_tools=["get_statistics", "analyze_quality"],
                complexity="moderate" if analysis_score > 1 else "simple"
            )
            
    def get_client(self, client_name: str = None) -> Optional[BaseModelClient]:
        """Get a specific model client or the primary one."""
        if not self.clients:
            return None
            
        if client_name and client_name in self.clients:
            return self.clients[client_name]
            
        # Return primary client or first available
        primary_client = self.clients.get("primary")
        if primary_client:
            return primary_client
            
        return list(self.clients.values())[0] if self.clients else None
        
    def get_best_client_for_task(self, task_type: str) -> Optional[BaseModelClient]:
        """Select the best client for a specific task type."""
        
        task_preferences = {
            "query_classification": ["primary", "general"],
            "code_generation": ["code_generation", "primary"],
            "schema_analysis": ["primary", "general"],
            "general": ["general", "primary"]
        }
        
        preferences = task_preferences.get(task_type, ["primary", "general"])
        
        for client_name in preferences:
            if client_name in self.clients:
                client = self.clients[client_name]
                if client.is_available:
                    return client
                    
        # Return any available client
        for client in self.clients.values():
            if client.is_available:
                return client
                
        return None
        
    def get_status(self) -> Dict[str, Any]:
        """Get status of all model clients."""
        status = {
            "initialized": self.is_initialized,
            "total_clients": len(self.clients),
            "available_clients": sum(1 for client in self.clients.values() if client.is_available),
            "clients": {}
        }
        
        for name, client in self.clients.items():
            status["clients"][name] = client.get_model_info()
            
        return status
        
    def get_cost_summary(self) -> Dict[str, float]:
        """Get cost summary for all clients that track costs."""
        costs = {}
        
        for name, client in self.clients.items():
            if hasattr(client, 'get_total_cost'):
                costs[name] = client.get_total_cost()
            else:
                costs[name] = 0.0  # Local models are free
                
        costs["total"] = sum(costs.values())
        return costs
        
    async def close_all(self):
        """Close all model clients and clean up resources."""
        for name, client in self.clients.items():
            try:
                if hasattr(client, 'close'):
                    await client.close()
                self.logger.debug(f"Closed client '{name}'")
            except Exception as e:
                self.logger.error(f"Error closing client '{name}': {e}")
                
        self.clients.clear()
        self.is_initialized = False
        self.logger.info("All model clients closed")
        
    def __del__(self):
        """Ensure resources are cleaned up."""
        if self.clients:
            # Can't run async in destructor, but log a warning
            self.logger.warning("ModelManager destroyed without calling close_all()")