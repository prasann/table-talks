"""TableTalk - A conversational EDA assistant for exploring data schemas."""

__version__ = "0.1.0"

# Main entry points
from .main import main, run_tabletalk_commands
from .cli.chat_interface import ChatInterface
from .cli.rich_formatter import CLIFormatter
from .metadata.metadata_store import MetadataStore
from .metadata.schema_extractor import SchemaExtractor
from .agent.schema_agent import SchemaAgent

__all__ = [
    "main",
    "run_tabletalk_commands", 
    "ChatInterface",
    "CLIFormatter",
    "MetadataStore",
    "SchemaExtractor",
    "SchemaAgent",
]
