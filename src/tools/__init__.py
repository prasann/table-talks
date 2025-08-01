"""Unified tool functions for schema queries."""

# Import new unified tools
from .tool_registry import ToolRegistry
from .unified_tools import (
    GetFilesTool, GetSchemasTool, SearchMetadataTool, GetStatisticsTool,
    FindRelationshipsTool, DetectInconsistenciesTool, CompareItemsTool, RunAnalysisTool
)

# Import legacy tools (for backward compatibility during migration)
try:
    from .atomic_schema_tools import AtomicSchemaTools
    from .composite_schema_tools import CompositeSchemaTools
    from .schema_tools import SchemaTools
    LEGACY_TOOLS_AVAILABLE = True
except ImportError:
    LEGACY_TOOLS_AVAILABLE = False

__all__ = [
    'ToolRegistry',
    'GetFilesTool', 'GetSchemasTool', 'SearchMetadataTool', 'GetStatisticsTool',
    'FindRelationshipsTool', 'DetectInconsistenciesTool', 'CompareItemsTool', 'RunAnalysisTool'
]

# Add legacy tools to exports if available
if LEGACY_TOOLS_AVAILABLE:
    __all__.extend(['AtomicSchemaTools', 'CompositeSchemaTools', 'SchemaTools'])
