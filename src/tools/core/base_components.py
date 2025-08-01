"""Abstract base classes for unified tool architecture."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from utils.logger import get_logger


class BaseTool(ABC):
    """Base class for all tools - optimized for Ollama function calling."""
    
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.logger = get_logger(f"tabletalk.tools.{self.__class__.__name__}")
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM."""
        pass
        
    @abstractmethod
    def get_parameters_schema(self) -> Dict:
        """Return JSON schema for tool parameters (for Ollama function calling)."""
        pass
        
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters."""
        pass


class BaseSearcher(ABC):
    """Abstract base class for search strategy implementations."""
    
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.logger = get_logger(f"tabletalk.searchers.{self.__class__.__name__}")
        
    @abstractmethod
    def search(self, search_term: str) -> List[Dict[str, Any]]:
        """Perform search and return raw results."""
        pass


class BaseAnalyzer(ABC):
    """Abstract base class for analysis strategy implementations."""
    
    def __init__(self, metadata_store):
        self.store = metadata_store
        self.logger = get_logger(f"tabletalk.analyzers.{self.__class__.__name__}")
        
    @abstractmethod
    def analyze(self, analysis_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform analysis and return raw results."""
        pass


class BaseFormatter(ABC):
    """Abstract base class for output formatting strategies."""
    
    def __init__(self):
        self.logger = get_logger(f"tabletalk.formatters.{self.__class__.__name__}")
        
    @abstractmethod
    def format(self, data: List[Dict[str, Any]], context: Optional[Dict] = None) -> str:
        """Format data into human-readable string."""
        pass
