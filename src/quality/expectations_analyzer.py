"""Simplified Great Expectations data quality analysis."""

from typing import Dict, List, Any
from pathlib import Path

from utils.logger import get_logger
import great_expectations as gx
import pandas as pd
import duckdb


class ExpectationsAnalyzer:
    """Simplified data quality analysis using Great Expectations."""
    
    def __init__(self, database_path: str):
        """Initialize Great Expectations analyzer."""
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.expectations_analyzer")
        
        # Initialize Great Expectations context
        try:
            self.context = gx.get_context()
        except Exception as e:
            self.logger.warning(f"GX context setup failed: {e}")
            self.context = None
    
    def analyze_data_quality(self, tables: List[str] = None) -> Dict[str, Any]:
        """Analyze data quality for specified tables."""
        if not self.context:
            return {'error': 'Great Expectations context not available'}
        
        try:
            # Connect to database
            conn = duckdb.connect(str(self.database_path))
            
            if not tables:
                tables = [row[0] for row in conn.execute("SHOW TABLES").fetchall()]
            
            results = {}
            for table_name in tables:
                try:
                    # Load table data
                    df = conn.execute(f"SELECT * FROM {table_name}").df()
                    
                    # Basic quality checks
                    quality_score = self._calculate_quality_score(df)
                    
                    results[table_name] = {
                        'table_name': table_name,
                        'row_count': len(df),
                        'column_count': len(df.columns),
                        'quality_score': quality_score,
                        'issues': self._find_basic_issues(df)
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {table_name}: {e}")
                    results[table_name] = {'error': str(e)}
            
            conn.close()
            return {'tables': results, 'summary': self._create_summary(results)}
            
        except Exception as e:
            self.logger.error(f"Data quality analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate a simple quality score (0-100)."""
        if df.empty:
            return 0.0
        
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        
        # Simple score: percentage of non-null cells
        return round((1 - null_cells / total_cells) * 100, 1) if total_cells > 0 else 0.0
    
    def _find_basic_issues(self, df: pd.DataFrame) -> List[str]:
        """Find basic data quality issues."""
        issues = []
        
        if df.empty:
            issues.append("Table is empty")
        
        # Check for columns with all nulls
        for col in df.columns:
            if df[col].isnull().all():
                issues.append(f"Column '{col}' is entirely null")
        
        # Check for duplicate rows
        if df.duplicated().any():
            issues.append(f"{df.duplicated().sum()} duplicate rows found")
        
        return issues
    
    def _create_summary(self, results: Dict) -> Dict[str, Any]:
        """Create summary of quality analysis."""
        valid_results = [r for r in results.values() if 'error' not in r]
        
        if not valid_results:
            return {'total_tables': 0, 'avg_quality_score': 0}
        
        total_tables = len(valid_results)
        avg_score = sum(r['quality_score'] for r in valid_results) / total_tables
        
        return {
            'total_tables': total_tables,
            'avg_quality_score': round(avg_score, 1),
            'total_issues': sum(len(r['issues']) for r in valid_results)
        }
    
    def close(self):
        """Clean up resources."""
        pass  # GX context doesn't need explicit cleanup


def create_analyzer(database_path: str):
    """Factory function to create ExpectationsAnalyzer."""
    try:
        return ExpectationsAnalyzer(database_path)
    except Exception as e:
        get_logger("tabletalk.expectations_analyzer").error(f"Failed to create analyzer: {e}")
        return None
