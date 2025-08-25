"""Model clients for TableTalk multi-model architecture."""

from .base_client import BaseModelClient, ModelResponse, QueryClassification
from .ollama_client import OllamaMultiModelClient
from .openai_client import OpenAIModelClient

__all__ = [
    "BaseModelClient",
    "ModelResponse",
    "QueryClassification",
    "OllamaMultiModelClient", 
    "OpenAIModelClient"
]