"""
Semantic search capabilities for enhanced column and schema analysis.

Uses SentenceTransformer for semantic similarity with graceful fallback.
Provides intelligent matching beyond exact string matching.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import semantic dependencies
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    SentenceTransformer = None
    np = None

@dataclass
class SemanticMatch:
    """Represents a semantic match with similarity score."""
    column_name: str
    file_name: str
    similarity: float
    match_type: str  # 'semantic', 'exact', 'pattern'


class SemanticSearcher:
    """
    Optional semantic search using SentenceTransformer.
    Provides intelligent column name matching beyond exact substring matching.
    """
    
    def __init__(self):
        self.model = None
        self.available = SEMANTIC_AVAILABLE
        self._column_embeddings_cache = {}
        self._model_name = "all-MiniLM-L6-v2"  # 80MB, fast, good for short texts
        
        if self.available:
            try:
                self._initialize_model()
            except Exception as e:
                logger.warning(f"Failed to initialize semantic model: {e}")
                self.available = False
    
    def _initialize_model(self):
        """Initialize the semantic model lazily on first use."""
        if self.model is None and self.available:
            logger.info(f"Loading semantic model: {self._model_name}")
            self.model = SentenceTransformer(self._model_name)
            logger.info("Semantic model loaded successfully")
    
    def find_similar_columns(self, search_term: str, columns: List[Tuple[str, str]], 
                           threshold: float = 0.6) -> List[SemanticMatch]:
        """
        Find columns semantically similar to the search term.
        
        Args:
            search_term: What the user is looking for
            columns: List of (column_name, file_name) tuples
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of SemanticMatch objects sorted by similarity
        """
        if not self.available:
            return []
        
        try:
            self._initialize_model()
            
            # Get embeddings for search term
            search_embedding = self.model.encode([search_term])
            
            # Get embeddings for all columns (with caching)
            column_embeddings = []
            column_info = []
            
            for column_name, file_name in columns:
                if column_name not in self._column_embeddings_cache:
                    # Enhance column name for better semantic matching
                    enhanced_name = self._enhance_column_name(column_name)
                    self._column_embeddings_cache[column_name] = self.model.encode([enhanced_name])
                
                column_embeddings.append(self._column_embeddings_cache[column_name][0])
                column_info.append((column_name, file_name))
            
            if not column_embeddings:
                return []
            
            # Calculate similarities
            column_embeddings = np.array(column_embeddings)
            similarities = np.dot(search_embedding, column_embeddings.T)[0]
            
            # Create matches above threshold
            matches = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    column_name, file_name = column_info[i]
                    matches.append(SemanticMatch(
                        column_name=column_name,
                        file_name=file_name,
                        similarity=float(similarity),
                        match_type='semantic'
                    ))
            
            # Sort by similarity (highest first)
            matches.sort(key=lambda x: x.similarity, reverse=True)
            return matches
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _enhance_column_name(self, column_name: str) -> str:
        """
        Enhance column name for better semantic matching.
        Convert technical names to more semantic descriptions.
        """
        # Convert underscores to spaces for better semantic understanding
        enhanced = column_name.replace('_', ' ')
        
        # Add common interpretations
        if 'id' in enhanced.lower():
            enhanced += " identifier primary key"
        
        if any(date_word in enhanced.lower() for date_word in ['date', 'time', 'created', 'updated']):
            enhanced += " timestamp datetime"
        
        if any(name_word in enhanced.lower() for name_word in ['name', 'title']):
            enhanced += " text label"
        
        if any(user_word in enhanced.lower() for user_word in ['customer', 'user', 'client']):
            enhanced += " person account profile"
            
        return enhanced
    
    def get_concept_groups(self, columns: List[Tuple[str, str]], 
                          threshold: float = 0.7) -> Dict[str, List[SemanticMatch]]:
        """
        Group columns by semantic concepts.
        
        Args:
            columns: List of (column_name, file_name) tuples  
            threshold: Minimum similarity for grouping
            
        Returns:
            Dictionary mapping concept names to lists of matching columns
        """
        if not self.available:
            return {}
        
        concepts = {
            "identifiers": ["id", "identifier", "primary key", "unique key"],
            "timestamps": ["date", "time", "timestamp", "created", "updated"],
            "names": ["name", "title", "label", "text"],
            "users": ["customer", "user", "client", "person", "account"],
            "financial": ["price", "amount", "cost", "money", "payment"],
            "quantities": ["quantity", "count", "number", "amount"],
            "status": ["status", "active", "enabled", "state"],
            "ratings": ["rating", "score", "review", "feedback"]
        }
        
        groups = {}
        
        for concept_name, concept_terms in concepts.items():
            matches = []
            for term in concept_terms:
                term_matches = self.find_similar_columns(term, columns, threshold)
                matches.extend(term_matches)
            
            # Remove duplicates and sort by similarity
            seen = set()
            unique_matches = []
            for match in sorted(matches, key=lambda x: x.similarity, reverse=True):
                key = (match.column_name, match.file_name)
                if key not in seen:
                    seen.add(key)
                    unique_matches.append(match)
            
            if unique_matches:
                groups[concept_name] = unique_matches
        
        return groups


class SemanticSchemaAnalyzer:
    """
    Semantic schema similarity and concept analysis.
    Finds schemas that are conceptually similar even with different column names.
    """
    
    def __init__(self):
        self.searcher = SemanticSearcher()
        self.available = self.searcher.available
    
    def find_similar_schemas(self, schemas: Dict[str, List[str]], 
                           threshold: float = 0.6) -> List[Dict]:
        """
        Find schemas that are semantically similar.
        
        Args:
            schemas: Dict mapping file_name to list of column names
            threshold: Minimum similarity threshold
            
        Returns:
            List of similarity analyses
        """
        if not self.available:
            return []
        
        results = []
        file_names = list(schemas.keys())
        
        for i, file1 in enumerate(file_names):
            for file2 in file_names[i+1:]:
                similarity_score = self._calculate_schema_similarity(
                    schemas[file1], schemas[file2], threshold
                )
                
                if similarity_score > threshold:
                    results.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': similarity_score,
                        'matching_concepts': self._find_matching_concepts(
                            schemas[file1], schemas[file2], threshold
                        )
                    })
        
        return sorted(results, key=lambda x: x['similarity'], reverse=True)
    
    def _calculate_schema_similarity(self, columns1: List[str], columns2: List[str], 
                                   threshold: float) -> float:
        """Calculate semantic similarity between two schemas."""
        if not columns1 or not columns2:
            return 0.0
        
        # Create column tuples for semantic search
        cols1 = [(col, "schema1") for col in columns1]
        cols2 = [(col, "schema2") for col in columns2]
        
        matches = 0
        total_comparisons = 0
        
        for col1 in columns1:
            best_match = 0.0
            similar_columns = self.searcher.find_similar_columns(col1, cols2, threshold)
            if similar_columns:
                best_match = similar_columns[0].similarity
            matches += best_match
            total_comparisons += 1
        
        return matches / total_comparisons if total_comparisons > 0 else 0.0
    
    def _find_matching_concepts(self, columns1: List[str], columns2: List[str], 
                              threshold: float) -> List[Dict]:
        """Find matching semantic concepts between schemas."""
        concepts = []
        
        cols2_tuples = [(col, "schema2") for col in columns2]
        
        for col1 in columns1:
            similar_columns = self.searcher.find_similar_columns(col1, cols2_tuples, threshold)
            if similar_columns:
                best_match = similar_columns[0]
                concepts.append({
                    'column1': col1,
                    'column2': best_match.column_name,
                    'similarity': best_match.similarity,
                    'concept': self._infer_concept(col1)
                })
        
        return concepts
    
    def _infer_concept(self, column_name: str) -> str:
        """Infer the semantic concept of a column."""
        name_lower = column_name.lower()
        
        if 'id' in name_lower:
            return 'identifier'
        elif any(word in name_lower for word in ['date', 'time', 'created', 'updated']):
            return 'timestamp'
        elif any(word in name_lower for word in ['name', 'title']):
            return 'name'
        elif any(word in name_lower for word in ['customer', 'user', 'client']):
            return 'user'
        elif any(word in name_lower for word in ['price', 'amount', 'cost']):
            return 'financial'
        elif any(word in name_lower for word in ['quantity', 'count']):
            return 'quantity'
        else:
            return 'other'


class SemanticConsistencyChecker:
    """
    Detect semantic naming inconsistencies and concept violations.
    Finds similar concepts with different naming patterns.
    """
    
    def __init__(self):
        self.searcher = SemanticSearcher()
        self.available = self.searcher.available
    
    def find_naming_inconsistencies(self, columns: List[Tuple[str, str]], 
                                  threshold: float = 0.8) -> List[Dict]:
        """
        Find columns that represent similar concepts but use different names.
        
        Args:
            columns: List of (column_name, file_name) tuples
            threshold: Minimum similarity to consider inconsistent naming
            
        Returns:
            List of inconsistency reports
        """
        if not self.available:
            return []
        
        inconsistencies = []
        processed = set()
        
        for i, (col1, file1) in enumerate(columns):
            if (col1, file1) in processed:
                continue
                
            # Find semantically similar columns
            remaining_columns = columns[i+1:]
            similar_matches = self.searcher.find_similar_columns(col1, remaining_columns, threshold)
            
            if similar_matches:
                # Group similar columns
                group = [(col1, file1)]
                for match in similar_matches:
                    group.append((match.column_name, match.file_name))
                    processed.add((match.column_name, match.file_name))
                
                # Check if they have different naming patterns
                if self._has_naming_inconsistency(group):
                    inconsistencies.append({
                        'concept': self._infer_concept(col1),
                        'similar_columns': group,
                        'avg_similarity': sum(m.similarity for m in similar_matches) / len(similar_matches),
                        'suggestion': self._suggest_consistent_name(group)
                    })
                
                processed.add((col1, file1))
        
        return sorted(inconsistencies, key=lambda x: x['avg_similarity'], reverse=True)
    
    def _has_naming_inconsistency(self, columns: List[Tuple[str, str]]) -> bool:
        """Check if columns have inconsistent naming patterns."""
        if len(columns) < 2:
            return False
        
        # Extract column names
        names = [col[0] for col in columns]
        
        # Check for different patterns
        patterns = set()
        for name in names:
            if '_' in name:
                patterns.add('underscore')
            if any(c.isupper() for c in name):
                patterns.add('camelcase')
            if name.islower() and '_' not in name:
                patterns.add('lowercase')
        
        return len(patterns) > 1 or len(set(names)) == len(names)  # All different names
    
    def _suggest_consistent_name(self, columns: List[Tuple[str, str]]) -> str:
        """Suggest a consistent name for similar columns."""
        names = [col[0] for col in columns]
        
        # Find common parts
        if all('id' in name.lower() for name in names):
            if any('customer' in name.lower() for name in names):
                return 'customer_id'
            elif any('user' in name.lower() for name in names):
                return 'user_id'
            elif any('order' in name.lower() for name in names):
                return 'order_id'
        
        # Default to most common pattern
        return min(names, key=len)  # Suggest shortest name
    
    def _infer_concept(self, column_name: str) -> str:
        """Infer the semantic concept of a column."""
        name_lower = column_name.lower()
        
        if 'id' in name_lower:
            return 'identifier'
        elif any(word in name_lower for word in ['date', 'time', 'created', 'updated']):
            return 'timestamp'
        elif any(word in name_lower for word in ['name', 'title']):
            return 'name'
        elif any(word in name_lower for word in ['customer', 'user', 'client']):
            return 'user'
        elif any(word in name_lower for word in ['price', 'amount', 'cost']):
            return 'financial'
        else:
            return 'other'
    
    def check_concept_consistency(self, schemas: Dict[str, Dict[str, str]]) -> List[Dict]:
        """
        Check if same concepts use consistent data types across files.
        
        Args:
            schemas: Dict mapping file_name to dict of column_name: data_type
            
        Returns:
            List of concept consistency issues
        """
        if not self.available:
            return []
        
        # Group columns by concept
        concept_groups = {}
        
        for file_name, schema in schemas.items():
            for column_name, data_type in schema.items():
                concept = self._infer_concept(column_name)
                if concept not in concept_groups:
                    concept_groups[concept] = []
                concept_groups[concept].append({
                    'file': file_name,
                    'column': column_name,
                    'type': data_type
                })
        
        # Check for type inconsistencies
        issues = []
        for concept, columns in concept_groups.items():
            if len(columns) > 1:
                types = set(col['type'] for col in columns)
                if len(types) > 1:
                    issues.append({
                        'concept': concept,
                        'inconsistent_types': list(types),
                        'columns': columns,
                        'suggestion': self._suggest_consistent_type(columns)
                    })
        
        return issues
    
    def _suggest_consistent_type(self, columns: List[Dict]) -> str:
        """Suggest a consistent data type for a concept."""
        types = [col['type'] for col in columns]
        
        # Return most common type
        from collections import Counter
        return Counter(types).most_common(1)[0][0]
