"""Search tools for metadata operations."""

import logging
from typing import Dict, Any
from .core.base_components import BaseTool
from .core.searchers import ColumnSearcher, FileSearcher, TypeSearcher
from .core.formatters import TextFormatter
from .core.semantic_search import SemanticSearcher

logger = logging.getLogger(__name__)


class SearchMetadataTool(BaseTool):
    """Tool for searching across metadata with optional semantic capabilities."""
    
    description = "Search across metadata. search_type: 'column', 'file', 'type'. Use semantic=True for concept searches (e.g., 'customer identifier', 'date fields') or when exact names are unknown."
    
    def __init__(self, metadata_store):
        super().__init__(metadata_store)
        self.semantic_searcher = SemanticSearcher()
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string", 
                    "description": "Term to search for"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["column", "file", "type"],
                    "description": "Type of search to perform",
                    "default": "column"
                },
                "semantic": {
                    "type": "boolean",
                    "description": "Enable semantic search for concept-based queries (e.g., 'customer identifier' finds 'customer_id', 'user_id'). Use when searching for concepts rather than exact names.",
                    "default": False
                }
            },
            "required": ["search_term"]
        }
    
    def execute(self, search_term: str, search_type: str = "column", semantic: bool = False) -> str:
        """Search across metadata with optional semantic enhancement."""
        try:
            # Try semantic search first if enabled and available
            if semantic and search_type == "column" and self.semantic_searcher.available:
                return self._semantic_search(search_term, search_type)
            else:
                # Try traditional search first
                traditional_result = self._traditional_search(search_term, search_type)
                
                # If traditional search finds no results for columns and semantic search is available,
                # automatically try semantic search as fallback
                if (search_type == "column" and 
                    self.semantic_searcher.available and 
                    ("No results found" in traditional_result or "no matches" in traditional_result.lower())):
                    
                    semantic_result = self._semantic_search(search_term, search_type)
                    if semantic_result and "No semantic matches found" not in semantic_result:
                        return f"No exact matches found. Here are semantic matches:\n\n{semantic_result}"
                
                return traditional_result
            
        except Exception as e:
            self.logger.error(f"Error searching metadata: {str(e)}")
            return f"Error searching metadata: {str(e)}"
    
    def _traditional_search(self, search_term: str, search_type: str) -> str:
        """Perform traditional exact/substring search."""
        searchers = {
            "column": ColumnSearcher(self.store),
            "file": FileSearcher(self.store),
            "type": TypeSearcher(self.store)
        }
        
        if search_type not in searchers:
            return f"Invalid search type: {search_type}. Use: column, file, or type"
        
        results = searchers[search_type].search(search_term)
        
        formatter = TextFormatter()
        context = {
            'format_type': 'search_results',
            'search_term': search_term,
            'search_type': search_type
        }
        return formatter.format(results, context)
    
    def _semantic_search(self, search_term: str, search_type: str) -> str:
        """Perform semantic search using SentenceTransformer."""
        try:
            # Get all columns from all files
            all_columns = []
            files = self.store.list_all_files()
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    for col in schema:
                        all_columns.append((col['column_name'], file_info['file_name']))
            
            if not all_columns:
                return "No columns found for semantic search."
            
            # Find semantically similar columns
            semantic_matches = self.semantic_searcher.find_similar_columns(
                search_term, all_columns, threshold=0.6
            )
            
            if not semantic_matches:
                return f"No semantic matches found for '{search_term}'."
            
            return self._format_semantic_results(semantic_matches, search_term)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return f"Error in semantic search: {str(e)}"
    
    def _format_semantic_results(self, semantic_matches, search_term: str) -> str:
        """Format semantic search results."""
        # Convert semantic matches to format compatible with existing formatter
        results = []
        
        for match in semantic_matches:
            # Get detailed column info from the list format
            schema = self.store.get_file_schema(match.file_name)
            column_info = None
            
            if schema:
                # Find the specific column in the list
                for col_info in schema:
                    if isinstance(col_info, dict) and col_info.get('column_name') == match.column_name:
                        column_info = col_info
                        break
            
            if column_info:
                results.append({
                    'file_name': match.file_name,
                    'column_name': match.column_name,
                    'data_type': column_info.get('data_type', 'unknown'),
                    'nulls': column_info.get('null_count', 0),
                    'unique': column_info.get('unique_count', 0),
                    'semantic_similarity': round(match.similarity, 3),
                    'match_type': match.match_type
                })
        
        # Format results
        if not results:
            return f"No semantic matches found for '{search_term}'"
        
        # Create semantic-aware output
        output = f"Found {len(results)} semantically similar column(s) for '{search_term}':\n\n"
        
        for result in results:
            similarity_indicator = "🎯" if result['semantic_similarity'] > 0.8 else "📍"
            output += f"{similarity_indicator} {result['file_name']}\n"
            output += f"  └─ {result['column_name']} ({result['data_type']})\n"
            output += f"     Similarity: {result['semantic_similarity']}, "
            output += f"Nulls: {result['nulls']}, Unique: {result['unique']}\n\n"
        
        return output.strip()
