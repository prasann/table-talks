"""Search tools for metadata queries with semantic capabilities."""

from typing import Dict, List, Any
from .core.base_components import BaseTool
from .core.searchers import ColumnSearcher, FileSearcher, TypeSearcher
from .core.formatters import TextFormatter


class SearchMetadataTool(BaseTool):
    """Tool for searching across metadata with optional semantic capabilities."""
    
    description = "Search across metadata. search_type: 'column', 'file', 'type'. Use semantic=True for intelligent matching."
    
    def __init__(self, metadata_store):
        super().__init__(metadata_store)
        # Initialize semantic searcher
        from .core.semantic_search import SemanticSearcher
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
                    "description": "Enable semantic search for intelligent matching (finds similar concepts)",
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
                return self._traditional_search(search_term, search_type)
            
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
        """Perform semantic search with fallback to traditional search."""
        try:
            # Get all columns for semantic analysis
            files = self.store.list_all_files()
            all_columns = []
            
            for file_info in files:
                schema = self.store.get_file_schema(file_info['file_name'])
                if schema:
                    # Handle list format from MetadataStore
                    for column_info in schema:
                        if isinstance(column_info, dict) and 'column_name' in column_info:
                            all_columns.append((column_info['column_name'], file_info['file_name']))
            
            # Perform semantic search
            semantic_matches = self.semantic_searcher.find_similar_columns(
                search_term, all_columns, threshold=0.6
            )
            
            # If semantic search finds results, format them
            if semantic_matches:
                return self._format_semantic_results(search_term, semantic_matches)
            else:
                # Fallback to traditional search
                self.logger.info(f"No semantic matches found for '{search_term}', falling back to traditional search")
                return self._traditional_search(search_term, search_type)
            
        except Exception as e:
            self.logger.warning(f"Semantic search failed: {e}, falling back to traditional search")
            return self._traditional_search(search_term, search_type)
    
    def _format_semantic_results(self, search_term: str, semantic_matches) -> str:
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
