"""Analysis tools for relationships and consistency detection with semantic capabilities."""

from typing import Dict
from .core.base_components import BaseTool
from .core.analyzers import RelationshipAnalyzer, ConsistencyChecker
from .core.formatters import TextFormatter
from .core.semantic_search import SemanticConsistencyChecker, SemanticSearcher

class FindRelationshipsTool(BaseTool):
    """Tool for finding relationships between files and columns with semantic capabilities."""
    
    description = "Find relationships like common columns, similar schemas, or semantic concept groups"
    
    def __init__(self, metadata_store):
        super().__init__(metadata_store)
        self.relationship_analyzer = RelationshipAnalyzer(metadata_store)
        self.consistency_checker = SemanticConsistencyChecker()
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["common_columns", "similar_schemas", "semantic_groups", "concept_evolution"],
                    "description": "Type of relationship analysis to perform",
                    "default": "common_columns"
                },
                "threshold": {
                    "type": "number",
                    "description": "Threshold for relationships (2+ for common_columns, 0.6-0.8 for semantic)",
                    "default": 2
                },
                "semantic": {
                    "type": "boolean",
                    "description": "Enable semantic analysis for intelligent relationship detection",
                    "default": False
                }
            },
            "required": []
        }
    
    def execute(self, analysis_type: str = "common_columns", threshold: float = 2, semantic: bool = False) -> str:
        """Find relationships between files and columns with optional semantic analysis."""
        try:
            # Handle semantic analysis types
            if analysis_type in ["similar_schemas", "semantic_groups", "concept_evolution"] and semantic:
                return self._semantic_analysis(analysis_type, threshold)
            else:
                return self._traditional_analysis(analysis_type, int(threshold))
            
        except Exception as e:
            self.logger.error(f"Error finding relationships: {str(e)}")
            return f"Error finding relationships: {str(e)}"
    
    def _traditional_analysis(self, analysis_type: str, threshold: int) -> str:
        """Perform traditional relationship analysis."""
        analyzer = RelationshipAnalyzer(self.store)
        results = analyzer.analyze(analysis_type, threshold=threshold)
        
        formatter = TextFormatter()
        context = {
            'format_type': 'analysis_results',
            'analysis_type': analysis_type
        }
        return formatter.format(results, context)
    
    def _semantic_analysis(self, analysis_type: str, threshold: float) -> str:
        """Perform semantic relationship analysis."""
        try:
            if analysis_type == "similar_schemas":
                return self._find_similar_schemas(threshold)
            elif analysis_type == "semantic_groups":
                return self._find_semantic_groups(threshold)
            elif analysis_type == "concept_evolution":
                return self._analyze_concept_evolution(threshold)
            else:
                return f"Semantic analysis type '{analysis_type}' not supported"
                
        except Exception as e:
            self.logger.error(f"Semantic analysis error: {e}")
            return f"Semantic analysis error: {e}"
    
    def _find_similar_schemas(self, threshold: float) -> str:
        """Find semantically similar schemas."""
        # Get all schemas
        files = self.store.list_all_files()
        schemas = {}
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Convert list format to column names list
                column_names = []
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        column_names.append(col_info['column_name'])
                schemas[file_info['file_name']] = column_names
        
        # Find similar schemas
        from .core.semantic_search import SchemaSimilarityAnalyzer
        semantic_analyzer = SchemaSimilarityAnalyzer()
        similar_schemas = semantic_analyzer.find_similar_schemas(schemas, threshold)
        
        if not similar_schemas:
            return f"No semantically similar schemas found (threshold: {threshold})"
        
        # Format results
        output = f"Found {len(similar_schemas)} semantically similar schema pairs:\n\n"
        
        for result in similar_schemas:
            output += f"🔗 **{result['file1']}** ↔ **{result['file2']}**\n"
            output += f"   Similarity: {result['similarity']:.3f}\n"
            
            if result['matching_concepts']:
                output += "   Matching concepts:\n"
                for concept in result['matching_concepts']:
                    output += f"   • {concept['column1']} ↔ {concept['column2']} "
                    output += f"({concept['concept']}, {concept['similarity']:.3f})\n"
            output += "\n"
        
        return output.strip()
    
    def _find_semantic_groups(self, threshold: float) -> str:
        """Group columns by semantic concepts."""
        # Get all columns
        files = self.store.list_all_files()
        all_columns = []
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Handle list format from MetadataStore
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        all_columns.append((col_info['column_name'], file_info['file_name']))
        
        from .core.semantic_search import SemanticSearcher
        searcher = SemanticSearcher()
        
        # Get concept groups
        concept_groups = searcher.get_concept_groups(all_columns, threshold)
        
        if not concept_groups:
            return f"No semantic concept groups found (threshold: {threshold})"
        
        # Format results
        output = "📊 **Semantic Concept Groups**\n\n"
        
        for concept, matches in concept_groups.items():
            output += f"**{concept.upper()}** ({len(matches)} columns):\n"
            for match in sorted(matches, key=lambda x: x.similarity, reverse=True):
                output += f"  • {match.file_name}: {match.column_name} ({match.similarity:.3f})\n"
            output += "\n"
        
        return output.strip()
    
    def _analyze_concept_evolution(self, threshold: float) -> str:
        """Analyze how concepts evolve across files."""
        # This is a more advanced analysis - track how similar concepts 
        # are named differently across files
        files = self.store.list_all_files()
        file_concepts = {}
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Handle list format from MetadataStore
                file_columns = []
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        file_columns.append((col_info['column_name'], file_info['file_name']))
                
                from .core.semantic_search import SemanticSearcher
                searcher = SemanticSearcher()
                concepts = searcher.get_concept_groups(file_columns, threshold)
                file_concepts[file_info['file_name']] = concepts
        
        if not file_concepts:
            return "No concept evolution data available"
        
        # Find concepts that appear across multiple files with different names
        output = "🔄 **Concept Evolution Across Files**\n\n"
        
        all_concepts = set()
        for concepts in file_concepts.values():
            all_concepts.update(concepts.keys())
        
        for concept in all_concepts:
            files_with_concept = []
            for file_name, concepts in file_concepts.items():
                if concept in concepts:
                    files_with_concept.append((file_name, concepts[concept]))
            
            if len(files_with_concept) > 1:
                output += f"**{concept.upper()}** appears in {len(files_with_concept)} files:\n"
                for file_name, matches in files_with_concept:
                    column_names = [match.column_name for match in matches]
                    output += f"  • {file_name}: {', '.join(column_names)}\n"
                output += "\n"
        
        return output.strip() if output.strip() != "🔄 **Concept Evolution Across Files**" else "No concept evolution patterns found"


class DetectInconsistenciesTool(BaseTool):
    """Tool for detecting data inconsistencies with semantic naming analysis."""
    
    description = "Detect inconsistencies like type mismatches, naming issues, or semantic conflicts"
    
    def __init__(self, metadata_store):
        super().__init__(metadata_store)
        self.semantic_checker = SemanticConsistencyChecker()
    
    def get_parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "check_type": {
                    "type": "string",
                    "enum": ["data_types", "naming_patterns", "semantic_naming", "concept_consistency", "abbreviation_detection"],
                    "description": "Type of consistency check to perform",
                    "default": "data_types"
                },
                "threshold": {
                    "type": "number",
                    "description": "Similarity threshold for semantic checks (0.6-0.9)",
                    "default": 0.8
                }
            },
            "required": []
        }
    
    def execute(self, check_type: str = "data_types", threshold: float = 0.8) -> str:
        """Detect data inconsistencies with optional semantic analysis."""
        try:
            # Handle case where LLM passes a list instead of string
            if isinstance(check_type, list):
                check_type = check_type[0] if check_type else "data_types"
            
            # Handle semantic check types
            if check_type in ["semantic_naming", "concept_consistency", "abbreviation_detection"]:
                return self._semantic_consistency_check(check_type, threshold)
            else:
                return self._traditional_consistency_check(check_type)
            
        except Exception as e:
            self.logger.error(f"Error detecting inconsistencies: {str(e)}")
            return f"Error detecting inconsistencies: {str(e)}"
    
    def _traditional_consistency_check(self, check_type: str) -> str:
        """Perform traditional consistency checks."""
        checker = ConsistencyChecker(self.store)
        results = checker.analyze(check_type)
        
        formatter = TextFormatter()
        context = {
            'format_type': 'analysis_results',
            'analysis_type': check_type
        }
        return formatter.format(results, context)
    
    def _semantic_consistency_check(self, check_type: str, threshold: float) -> str:
        """Perform semantic consistency checks."""
        try:
            if check_type == "semantic_naming":
                return self._check_semantic_naming(threshold)
            elif check_type == "concept_consistency":
                return self._check_concept_consistency()
            elif check_type == "abbreviation_detection":
                return self._check_abbreviations(threshold)
            else:
                return f"Semantic check type '{check_type}' not supported"
                
        except Exception as e:
            self.logger.error(f"Semantic consistency check error: {e}")
            return f"Semantic consistency check error: {e}"
    
    def _check_semantic_naming(self, threshold: float) -> str:
        """Find columns with similar meanings but different names."""
        # Get all columns
        files = self.store.list_all_files()
        all_columns = []
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Handle list format from MetadataStore
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        all_columns.append((col_info['column_name'], file_info['file_name']))
        
        # Find naming inconsistencies
        inconsistencies = self.semantic_checker.find_naming_inconsistencies(all_columns, threshold)
        
        if not inconsistencies:
            return f"No semantic naming inconsistencies found (threshold: {threshold})"
        
        # Format results
        output = f"⚠️  **Semantic Naming Inconsistencies** (threshold: {threshold})\n\n"
        
        for issue in inconsistencies:
            output += f"**{issue['concept'].upper()} CONCEPT** (similarity: {issue['avg_similarity']:.3f})\n"
            output += f"  Suggested name: `{issue['suggestion']}`\n"
            output += f"  Current variations:\n"
            
            for col_name, file_name in issue['similar_columns']:
                output += f"    • {file_name}: `{col_name}`\n"
            output += "\n"
        
        return output.strip()
    
    def _check_concept_consistency(self) -> str:
        """Check if same concepts use consistent data types."""
        # Get all schemas with data types
        files = self.store.list_all_files()
        schemas = {}
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Convert list format to format expected by semantic checker
                type_schema = {}
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        type_schema[col_info['column_name']] = col_info.get('data_type', 'unknown')
                schemas[file_info['file_name']] = type_schema
        
        # Check concept consistency
        issues = self.semantic_checker.check_concept_consistency(schemas)
        
        if not issues:
            return "No concept consistency issues found"
        
        # Format results
        output = "🔍 **Concept Data Type Consistency Issues**\n\n"
        
        for issue in issues:
            output += f"**{issue['concept'].upper()}** has inconsistent types:\n"
            output += f"  Types found: {', '.join(issue['inconsistent_types'])}\n"
            output += f"  Suggested type: `{issue['suggestion']}`\n"
            output += f"  Columns:\n"
            
            for col in issue['columns']:
                output += f"    • {col['file']}: `{col['column']}` ({col['type']})\n"
            output += "\n"
        
        return output.strip()
    
    def _check_abbreviations(self, threshold: float) -> str:
        """Detect abbreviations vs full names for same concepts."""
        # Get all columns
        files = self.store.list_all_files()
        all_columns = []
        
        for file_info in files:
            schema = self.store.get_file_schema(file_info['file_name'])
            if schema:
                # Handle list format from MetadataStore
                for col_info in schema:
                    if isinstance(col_info, dict) and 'column_name' in col_info:
                        all_columns.append((col_info['column_name'], file_info['file_name']))
        
        # Find potential abbreviations (columns with high semantic similarity but different lengths)
        abbreviations = []
        
        searcher = SemanticSearcher()
        
        processed = set()
        
        for col_name, file_name in all_columns:
            if (col_name, file_name) in processed:
                continue
            
            # Find similar columns
            remaining_columns = [(c, f) for c, f in all_columns if (c, f) != (col_name, file_name)]
            similar_matches = searcher.find_similar_columns(col_name, remaining_columns, threshold)
            
            for match in similar_matches:
                # Check if it looks like an abbreviation (significant length difference)
                len_diff = abs(len(col_name) - len(match.column_name))
                if len_diff >= 3:  # Significant length difference
                    shorter = col_name if len(col_name) < len(match.column_name) else match.column_name
                    longer = match.column_name if len(col_name) < len(match.column_name) else col_name
                    
                    abbreviations.append({
                        'short': shorter,
                        'long': longer,
                        'similarity': match.similarity,
                        'files': [file_name, match.file_name] if col_name == shorter else [match.file_name, file_name]
                    })
                    
                    processed.add((col_name, file_name))
                    processed.add((match.column_name, match.file_name))
        
        if not abbreviations:
            return f"No abbreviation patterns found (threshold: {threshold})"
        
        # Format results
        output = f"📝 **Potential Abbreviation Inconsistencies** (threshold: {threshold})\n\n"
        
        for abbrev in sorted(abbreviations, key=lambda x: x['similarity'], reverse=True):
            output += f"**{abbrev['short']}** ↔ **{abbrev['long']}** (similarity: {abbrev['similarity']:.3f})\n"
            output += f"  Files: {abbrev['files'][0]} → {abbrev['files'][1]}\n"
            output += f"  Suggestion: Use consistent naming (`{abbrev['long']}`)\n\n"
        
        return output.strip()
