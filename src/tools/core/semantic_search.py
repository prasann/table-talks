"""
Semantic search capabilities for enhanced column and schema analysis.

Uses SentenceTransformer for semantic similarity with graceful fallback.
Provides intelligent matching beyond exact string matching.
"""

import logging
import warnings
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SemanticMatch:
    """Represents a semantic match with similarity score."""
    column_name: str
    file_name: str
    similarity: float
    match_type: str  # 'semantic', 'exact', 'pattern'


class SemanticSearcher:
    """
    Semantic search using SentenceTransformer.
    Provides intelligent column name matching beyond exact substring matching.
    """
    
    def __init__(self):
        self.model = None
        self._column_embeddings_cache = {}
        self._model_name = "all-MiniLM-L6-v2"  # 80MB, fast, good for short texts
        self._available = True  # Track if semantic search is available
        
        # Initialize model on first use
        self._initialize_model()
    
    @property
    def available(self) -> bool:
        """Check if semantic search is available."""
        return self._available and self.model is not None
    
    def _initialize_model(self):
        """Initialize the semantic model."""
        if self.model is None:
            try:
                logger.info(f"Loading semantic model: {self._model_name}")
                # Suppress FutureWarning about encoder_attention_mask deprecation
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning, 
                                          message=".*encoder_attention_mask.*")
                    self.model = SentenceTransformer(self._model_name)
                logger.info("Semantic model loaded successfully")
                self._available = True
            except Exception as e:
                logger.error(f"Failed to load semantic model: {e}")
                self._available = False
                self.model = None
    
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
            logger.warning("Semantic search not available, returning empty results")
            return []
        
        self._initialize_model()
        
        # Get embeddings for search term with warning suppression
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning, 
                                  message=".*encoder_attention_mask.*")
            search_embedding = self.model.encode([search_term])
        
        # Get embeddings for all columns (with caching)
        column_embeddings = []
        column_info = []
        
        for column_name, file_name in columns:
            if column_name not in self._column_embeddings_cache:
                # Enhance column name for better semantic matching
                enhanced_name = self._enhance_column_name(column_name)
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=FutureWarning, 
                                          message=".*encoder_attention_mask.*")
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
            logger.warning("Semantic search not available, returning empty concept groups")
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


class ConceptClassifier:
    """
    Semantic concept classification for database columns.
    Uses SentenceTransformer for intelligent concept detection.
    """
    
    def __init__(self, searcher: SemanticSearcher = None):
        if searcher is None:
            searcher = SemanticSearcher()
        self.searcher = searcher
        
        # Define concept templates with multiple examples
        self.concept_templates = {
            'identifier': [
                "unique identifier", "primary key", "id field", "reference number",
                "key column", "unique code", "identifier field"
            ],
            'timestamp': [
                "date field", "time column", "timestamp data", "datetime field",
                "creation date", "update time", "temporal data"
            ],
            'name': [
                "name field", "title column", "label text", "description field", 
                "text identifier", "display name"
            ],
            'user': [
                "user data", "customer information", "client field", "person data",
                "account holder", "profile information"
            ],
            'financial': [
                "money amount", "price data", "cost field", "financial value",
                "payment information", "currency amount"
            ],
            'quantity': [
                "count field", "quantity data", "number amount", "volume data",
                "measurement value", "numeric quantity"
            ],
            'status': [
                "status field", "state data", "condition flag", "active indicator",
                "enabled flag", "boolean status"
            ],
            'contact': [
                "email address", "phone number", "contact information", "address field",
                "communication data", "location information"
            ]
        }
    
    def classify_column(self, column_name: str, threshold: float = 0.6) -> str:
        """
        Classify a column into a semantic concept using AI similarity.
        
        Args:
            column_name: The column name to classify
            threshold: Minimum similarity threshold
            
        Returns:
            The best matching concept or 'other'
        """
        best_concept = 'other'
        best_similarity = 0.0
        
        # Test column against each concept template
        for concept, templates in self.concept_templates.items():
            # Find best match among templates for this concept
            concept_similarity = 0.0
            for template in templates:
                # Create dummy column list for semantic search
                dummy_columns = [(column_name, "test_file")]
                matches = self.searcher.find_similar_columns(template, dummy_columns, threshold=0.1)
                
                if matches:
                    concept_similarity = max(concept_similarity, matches[0].similarity)
            
            # Update best concept if this one is better
            if concept_similarity > best_similarity and concept_similarity >= threshold:
                best_similarity = concept_similarity
                best_concept = concept
        
        return best_concept


class SchemaSimilarityAnalyzer:
    """
    Semantic schema similarity and concept analysis.
    Finds schemas that are conceptually similar even with different column names.
    """
    
    def __init__(self):
        self.searcher = SemanticSearcher()
        self.classifier = ConceptClassifier(self.searcher)
    
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
                    'concept': self.classifier.classify_column(col1)
                })
        
        return concepts


class SemanticConsistencyChecker:
    """
    Detect semantic naming inconsistencies and concept violations.
    Finds similar concepts with different naming patterns.
    """
    
    def __init__(self):
        self.searcher = SemanticSearcher()
        self.classifier = ConceptClassifier(self.searcher)
    
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
                        'concept': self.classifier.classify_column(col1),
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
    
    def _suggest_consistent_type(self, columns: List[Dict]) -> str:
        """Suggest a consistent data type for a concept."""
        types = [col['type'] for col in columns]
        
        # Return most common type
        from collections import Counter
        return Counter(types).most_common(1)[0][0]
