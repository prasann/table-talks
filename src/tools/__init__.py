"""Modular tool functions for schema queries."""

# Import tool registry
from .tool_registry import ToolRegistry

# Import from modular files
from .basic_tools import GetFilesTool, GetSchemasTool, GetStatisticsTool
from .search_tools import SearchMetadataTool
from .comparison_tools import FindRelationshipsTool, DetectInconsistenciesTool
from .utility_tools import CompareItemsTool, RunAnalysisTool

__all__ = [
    'ToolRegistry',
    # Basic Information Tools
    'GetFilesTool', 'GetSchemasTool', 'GetStatisticsTool',
    # Search Tools
    'SearchMetadataTool',
    # Analysis Tools
    'FindRelationshipsTool', 'DetectInconsistenciesTool',
    # Utility Tools
    'CompareItemsTool', 'RunAnalysisTool'
]
