"""Base model client interface for TableTalk multi-model architecture."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ModelResponse:
    """Standard response format from model clients."""
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    execution_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class QueryClassification:
    """Result of query intent classification."""
    workflow_type: str  # "schema_exploration", "data_discovery", "analysis", "basic_query"
    confidence: float   # 0.0 to 1.0
    reasoning: str      # Explanation of classification
    suggested_tools: List[str]  # Tools likely needed
    complexity: str     # "simple", "moderate", "complex"


class BaseModelClient(ABC):
    """Abstract base class for all model clients."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        self.model_name = model_name
        self.config = config
        self.is_available = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the model client and check availability."""
        pass
        
    @abstractmethod
    async def classify_query(self, query: str, context: Dict[str, Any] = None) -> QueryClassification:
        """Classify query to determine appropriate workflow and tools."""
        pass
        
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> ModelResponse:
        """Generate a response for the given prompt."""
        pass
        
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get model capabilities and metadata."""
        pass
        
    @abstractmethod
    def estimate_cost(self, query: str) -> float:
        """Estimate cost for processing the query (0.0 for local models)."""
        pass
        
    def is_local(self) -> bool:
        """Check if this is a local model (no API costs)."""
        return self.estimate_cost("test") == 0.0
        
    def supports_function_calling(self) -> bool:
        """Check if model supports function calling."""
        capabilities = self.get_capabilities()
        return capabilities.get("function_calling", False)
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get basic model information."""
        return {
            "name": self.model_name,
            "type": self.__class__.__name__,
            "available": self.is_available,
            "local": self.is_local(),
            "function_calling": self.supports_function_calling(),
            "capabilities": self.get_capabilities()
        }