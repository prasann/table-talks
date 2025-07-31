"""Great Expectations-based data quality analysis for TableTalk."""

import os
import sys
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.logger import get_logger

try:
    import great_expectations as gx
    from great_expectations.core.batch import RuntimeBatchRequest
    from great_expectations.data_context.types.base import DataContextConfig
    from great_expectations.datasource.fluent import PandasDatasource
    GX_AVAILABLE = True
except ImportError:
    GX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ExpectationsAnalyzer:
    """Data quality analysis using Great Expectations.
    
    Provides comprehensive data validation, profiling, and quality assessment
    capabilities using the Great Expectations framework.
    """
    
    def __init__(self, database_path: str):
        """Initialize Great Expectations analyzer.
        
        Args:
            database_path: Path to DuckDB database file
        """
        if not GX_AVAILABLE:
            raise ImportError(
                "Great Expectations is required. "
                "Install with: pip install great-expectations"
            )
        
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "Pandas is required. "
                "Install with: pip install pandas"
            )
        
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.expectations_analyzer")
        
        # Initialize Great Expectations context with minimal configuration
        self.context = self._create_context()
        self.datasource_name = "duckdb_datasource"
        
        # Check if context was created successfully
        if self.context is None:
            self.logger.warning("Great Expectations context creation failed - GX features will be limited")
        
        self.logger.info(f"Great Expectations Analyzer initialized for: {database_path}")
    
    def _create_context(self) -> gx.DataContext:
        """Create a lightweight Great Expectations context.
        
        Returns:
            Configured DataContext instance
        """
        try:
            # Use ephemeral context (in-memory) for simplicity
            # This avoids file system configuration issues
            context = gx.get_context(mode="ephemeral")
            self.logger.debug("Created ephemeral GX context")
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to create GX context: {e}")
            # Return None and disable GX functionality
            return None
    
    def _setup_datasource(self) -> bool:
        """Set up DuckDB datasource for Great Expectations.
        
        Returns:
            True if datasource was set up successfully, False otherwise
        """
        try:
            # Check if context is available
            if self.context is None:
                self.logger.error("GX context is not available")
                return False
            
            # Check if datasource already exists
            existing_datasources = self.context.list_datasources()
            if any(ds.name == self.datasource_name for ds in existing_datasources):
                self.logger.debug(f"Datasource '{self.datasource_name}' already exists")
                return True
            
            # Create pandas datasource (we'll feed it data from DuckDB)
            datasource = self.context.sources.add_pandas(self.datasource_name)
            self.logger.debug(f"Created datasource: {self.datasource_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup datasource: {e}")
            return False
    
    def validate_table(self, table_name: str, data_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Validate a table using Great Expectations.
        
        Args:
            table_name: Name of the table to validate
            data_df: Optional DataFrame with table data (if not provided, will be loaded from DuckDB)
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Check if context is available
            if self.context is None:
                return {'error': 'Great Expectations context not available'}
            
            if not self._setup_datasource():
                return {'error': 'Failed to setup datasource'}
            
            # Get data if not provided
            if data_df is None:
                data_df = self._load_table_data(table_name)
                if data_df is None:
                    return {'error': f'Failed to load data for table: {table_name}'}
            
            # Add data asset to datasource
            datasource = self.context.get_datasource(self.datasource_name)
            data_asset = datasource.add_dataframe_asset(name=table_name, dataframe=data_df)
            
            # Create batch request
            batch_request = data_asset.build_batch_request()
            
            # Create expectation suite
            suite_name = f"{table_name}_validation_suite"
            suite = self.context.add_expectation_suite(expectation_suite_name=suite_name)
            
            # Add basic expectations
            validator = self.context.get_validator(
                batch_request=batch_request,
                expectation_suite=suite
            )
            
            # Basic data quality expectations
            validation_results = self._add_basic_expectations(validator, data_df)
            
            self.logger.debug(f"Validation completed for table '{table_name}'")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Table validation failed for '{table_name}': {e}")
            return {'error': str(e)}
    
    def _load_table_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """Load table data from DuckDB into pandas DataFrame.
        
        Args:
            table_name: Name of the table to load
            
        Returns:
            DataFrame with table data or None if loading fails
        """
        try:
            import duckdb
            
            # Connect to DuckDB and load data
            conn = duckdb.connect(str(self.database_path))
            df = conn.execute(f"SELECT * FROM {table_name}").df()
            conn.close()
            
            self.logger.debug(f"Loaded {len(df)} rows for table '{table_name}'")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load data for table '{table_name}': {e}")
            return None
    
    def _add_basic_expectations(self, validator, data_df: pd.DataFrame) -> Dict[str, Any]:
        """Add basic data quality expectations to validator.
        
        Args:
            validator: Great Expectations validator
            data_df: DataFrame with table data
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'total_expectations': 0,
            'successful_expectations': 0,
            'failed_expectations': [],
            'data_quality_score': 0.0,
            'row_count': len(data_df),
            'column_count': len(data_df.columns),
            'expectations_details': []
        }
        
        try:
            # Expectation 1: Table should not be empty
            expectation = validator.expect_table_row_count_to_be_between(min_value=1)
            results['total_expectations'] += 1
            if expectation.success:
                results['successful_expectations'] += 1
            else:
                results['failed_expectations'].append('Table is empty')
            results['expectations_details'].append({
                'expectation': 'table_row_count_to_be_between',
                'success': expectation.success,
                'result': expectation.result
            })
            
            # Expectation 2: Check for columns with all null values
            for column in data_df.columns:
                if data_df[column].isnull().all():
                    results['failed_expectations'].append(f'Column "{column}" has all null values')
                    results['expectations_details'].append({
                        'expectation': 'column_values_to_not_be_null',
                        'column': column,
                        'success': False,
                        'result': 'All values are null'
                    })
                else:
                    results['successful_expectations'] += 1
                    results['expectations_details'].append({
                        'expectation': 'column_values_to_not_be_null',
                        'column': column,
                        'success': True,
                        'result': 'Column has non-null values'
                    })
                results['total_expectations'] += 1
            
            # Expectation 3: Check for duplicate rows
            duplicate_count = data_df.duplicated().sum()
            if duplicate_count > 0:
                results['failed_expectations'].append(f'Found {duplicate_count} duplicate rows')
                results['expectations_details'].append({
                    'expectation': 'table_row_count_to_equal_duplicate_count',
                    'success': False,
                    'result': f'{duplicate_count} duplicate rows found'
                })
            else:
                results['successful_expectations'] += 1
                results['expectations_details'].append({
                    'expectation': 'table_row_count_to_equal_duplicate_count',
                    'success': True,
                    'result': 'No duplicate rows found'
                })
            results['total_expectations'] += 1
            
            # Calculate data quality score
            if results['total_expectations'] > 0:
                results['data_quality_score'] = (
                    results['successful_expectations'] / results['total_expectations']
                ) * 100
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to add basic expectations: {e}")
            results['error'] = str(e)
            return results
    
    def profile_table(self, table_name: str) -> Dict[str, Any]:
        """Generate data profile for a table.
        
        Args:
            table_name: Name of the table to profile
            
        Returns:
            Dictionary with data profiling results
        """
        try:
            data_df = self._load_table_data(table_name)
            if data_df is None:
                return {'error': f'Failed to load data for table: {table_name}'}
            
            profile = {
                'table_name': table_name,
                'row_count': len(data_df),
                'column_count': len(data_df.columns),
                'columns': {}
            }
            
            # Profile each column
            for column in data_df.columns:
                col_data = data_df[column]
                
                column_profile = {
                    'name': column,
                    'data_type': str(col_data.dtype),
                    'null_count': col_data.isnull().sum(),
                    'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                    'unique_count': col_data.nunique(),
                    'unique_percentage': (col_data.nunique() / len(col_data)) * 100
                }
                
                # Add statistics for numeric columns
                if pd.api.types.is_numeric_dtype(col_data):
                    column_profile.update({
                        'min_value': col_data.min(),
                        'max_value': col_data.max(),
                        'mean_value': col_data.mean(),
                        'std_deviation': col_data.std()
                    })
                
                # Add statistics for string columns
                elif pd.api.types.is_string_dtype(col_data):
                    non_null_data = col_data.dropna()
                    if len(non_null_data) > 0:
                        column_profile.update({
                            'min_length': non_null_data.str.len().min(),
                            'max_length': non_null_data.str.len().max(),
                            'avg_length': non_null_data.str.len().mean()
                        })
                
                profile['columns'][column] = column_profile
            
            self.logger.debug(f"Generated profile for table '{table_name}'")
            return profile
            
        except Exception as e:
            self.logger.error(f"Table profiling failed for '{table_name}': {e}")
            return {'error': str(e)}
    
    def analyze_data_quality(self, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform comprehensive data quality analysis.
        
        Args:
            tables: List of table names to analyze (if None, analyze all tables)
            
        Returns:
            Dictionary with comprehensive data quality results
        """
        try:
            if tables is None:
                # Get all tables from database
                import duckdb
                conn = duckdb.connect(str(self.database_path))
                tables_result = conn.execute("SHOW TABLES").fetchall()
                tables = [row[0] for row in tables_result]
                conn.close()
            
            analysis = {
                'database_path': str(self.database_path),
                'total_tables': len(tables),
                'tables_analyzed': {},
                'overall_quality_score': 0.0,
                'issues_summary': []
            }
            
            total_score = 0.0
            tables_processed = 0
            
            for table_name in tables:
                try:
                    # Validate table
                    validation_results = self.validate_table(table_name)
                    
                    # Profile table
                    profile_results = self.profile_table(table_name)
                    
                    # Combine results
                    table_analysis = {
                        'validation': validation_results,
                        'profile': profile_results
                    }
                    
                    analysis['tables_analyzed'][table_name] = table_analysis
                    
                    # Add to overall score
                    if 'data_quality_score' in validation_results:
                        total_score += validation_results['data_quality_score']
                        tables_processed += 1
                    
                    # Collect issues
                    if 'failed_expectations' in validation_results:
                        for issue in validation_results['failed_expectations']:
                            analysis['issues_summary'].append(f"{table_name}: {issue}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to analyze table '{table_name}': {e}")
                    analysis['tables_analyzed'][table_name] = {'error': str(e)}
            
            # Calculate overall quality score
            if tables_processed > 0:
                analysis['overall_quality_score'] = total_score / tables_processed
            
            self.logger.info(f"Data quality analysis completed for {len(tables)} tables")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Data quality analysis failed: {e}")
            return {'error': str(e)}


def create_analyzer(database_path: str) -> Optional[ExpectationsAnalyzer]:
    """Factory function to create Great Expectations analyzer.
    
    Args:
        database_path: Path to DuckDB database
        
    Returns:
        ExpectationsAnalyzer instance or None if creation fails
    """
    try:
        return ExpectationsAnalyzer(database_path)
    except Exception as e:
        logger = get_logger("tabletalk.expectations_analyzer")
        logger.error(f"Failed to create Great Expectations analyzer: {e}")
        return None
