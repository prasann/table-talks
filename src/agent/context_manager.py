"""Context management and query intent detection."""

import logging
import os
import sys
from typing import Dict, List, Optional, Tuple
import re

# Add src to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger


class ContextManager:
    """Manages conversation context and query intent detection."""
    
    def __init__(self):
        """Initialize the context manager."""
        self.logger = get_logger("tabletalk.context")
        
        # Intent patterns for query classification
        self.intent_patterns = {
            'schema_query': [
                r'schema\s+(?:of\s+|for\s+)?(.+)',
                r'structure\s+(?:of\s+|for\s+)?(.+)',
                r'columns?\s+(?:in\s+|of\s+|for\s+)?(.+)',
                r'what.*columns.*(?:in\s+|of\s+)(.+)',
                r'describe\s+(.+)',
                r'show.*schema.*(?:of\s+|for\s+)?(.+)'
            ],
            'file_list': [
                r'(?:what\s+)?files?\s+(?:do\s+)?(?:we\s+)?(?:have|available)',
                r'list\s+(?:all\s+)?files?',
                r'show\s+(?:me\s+)?(?:all\s+)?files?',
                r'which\s+files?'
            ],
            'column_search': [
                r'(?:which\s+)?files?\s+(?:have|contain).*?([a-zA-Z_][a-zA-Z0-9_]*)',
                r'find.*column.*?([a-zA-Z_][a-zA-Z0-9_]*)',
                r'search.*([a-zA-Z_][a-zA-Z0-9_]*)',
                r'where.*([a-zA-Z_][a-zA-Z0-9_]*)\s+column'
            ],
            'type_mismatch': [
                r'(?:type\s+)?(?:mismatch|inconsisten)',
                r'different\s+(?:data\s+)?types?',
                r'conflicting\s+types?',
                r'schema\s+(?:problem|issue|conflict)'
            ],
            'common_columns': [
                r'common\s+columns?',
                r'shared\s+columns?',
                r'columns?\s+(?:in\s+)?(?:multiple|several|many)\s+files?',
                r'overlap.*columns?'
            ],
            'summary': [
                r'(?:database\s+)?(?:summary|overview|stats|statistics)',
                r'how\s+many\s+files?',
                r'total\s+(?:files?|columns?)',
                r'general\s+(?:info|information)'
            ]
        }
    
    def detect_intent(self, query: str) -> Tuple[str, Optional[str]]:
        """Detect the intent of a user query.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (intent, extracted_parameter)
        """
        query_lower = query.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    # Extract parameter if available
                    param = None
                    if match.groups():
                        param = match.group(1).strip()
                        # Clean up common file extensions and extra words
                        param = re.sub(r'\.(csv|parquet)$', '', param)
                        param = re.sub(r'\s+(?:file|table)$', '', param)
                    
                    self.logger.debug(f"Detected intent: {intent} with parameter: {param}")
                    return intent, param
        
        # Default to general query if no specific intent detected
        return 'general', None
    
    def prepare_context(self, intent: str, parameter: Optional[str] = None) -> Dict[str, str]:
        """Prepare context information for the LLM based on intent.
        
        Args:
            intent: Detected intent
            parameter: Extracted parameter (e.g., file name, column name)
            
        Returns:
            Dictionary with context information
        """
        context = {
            'intent': intent,
            'parameter': parameter,
            'tool_suggestion': self._get_tool_suggestion(intent),
            'response_format': self._get_response_format(intent)
        }
        
        return context
    
    def _get_tool_suggestion(self, intent: str) -> str:
        """Get the suggested tool for a given intent.
        
        Args:
            intent: Query intent
            
        Returns:
            Suggested tool name
        """
        tool_mapping = {
            'schema_query': 'get_file_schema',
            'file_list': 'list_files',
            'column_search': 'find_columns',
            'type_mismatch': 'detect_type_mismatches',
            'common_columns': 'find_common_columns',
            'summary': 'database_summary'
        }
        
        return tool_mapping.get(intent, 'list_files')
    
    def _get_response_format(self, intent: str) -> str:
        """Get the suggested response format for a given intent.
        
        Args:
            intent: Query intent
            
        Returns:
            Response format description
        """
        format_mapping = {
            'schema_query': 'List columns with data types, null counts, and unique values',
            'file_list': 'Show file names with column counts and sizes',
            'column_search': 'List files containing the column with type information',
            'type_mismatch': 'Group by column name and show conflicting types',
            'common_columns': 'List shared columns with file counts',
            'summary': 'Show overall statistics about scanned files'
        }
        
        return format_mapping.get(intent, 'Provide helpful information about the data')
    
    def filter_context_for_llm(self, context: str, max_tokens: int = 2000) -> str:
        """Filter and truncate context to fit within token limits.
        
        Args:
            context: Context string to filter
            max_tokens: Maximum number of tokens (approximate)
            
        Returns:
            Filtered context string
        """
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(context) <= max_chars:
            return context
        
        # Truncate and add indication
        truncated = context[:max_chars - 50]
        
        # Try to break at a reasonable point
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.8:  # If we can break within 80% of limit
            truncated = truncated[:last_newline]
        
        return truncated + "\n... (output truncated for length)"
    
    def format_error_message(self, error: str, suggestion: str = None) -> str:
        """Format error messages for user display.
        
        Args:
            error: Error message
            suggestion: Optional suggestion for the user
            
        Returns:
            Formatted error message
        """
        message = f"I encountered an issue: {error}"
        
        if suggestion:
            message += f"\n\nSuggestion: {suggestion}"
        
        return message
    
    def get_help_text(self) -> str:
        """Get help text for users.
        
        Returns:
            Help text string
        """
        return """
TableTalk Commands and Examples:

Commands:
  /scan <directory>     - Scan files in directory for schema information
  /help                 - Show this help message
  /exit or /quit        - Exit TableTalk

Example Queries:
  • "Show me the schema of orders.csv"
  • "What files do we have?"
  • "Which files have a user_id column?"
  • "Find data type inconsistencies"
  • "What columns are common across files?"
  • "Give me a summary of the database"

Tips:
  - Start by scanning a directory: /scan data/
  - Ask questions in natural language
  - Be specific about file names when asking about schemas
        """.strip()
