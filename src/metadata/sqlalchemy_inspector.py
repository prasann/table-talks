"""SQLAlchemy-based database introspection for TableTalk."""

import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from utils.logger import get_logger

try:
    from sqlalchemy import create_engine, inspect, MetaData, text
    from sqlalchemy.engine import reflection
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class SQLAlchemyInspector:
    """Database introspection using SQLAlchemy.
    
    Provides rich database metadata access using SQLAlchemy's reflection capabilities.
    Supports advanced features like constraints, indexes, and relationships.
    """
    
    def __init__(self, database_path: str):
        """Initialize SQLAlchemy inspector.
        
        Args:
            database_path: Path to DuckDB database file
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy and duckdb-engine are required. "
                "Install with: pip install sqlalchemy duckdb-engine"
            )
        
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.sqlalchemy_inspector")
        
        # Create DuckDB engine using duckdb-engine
        self.engine = create_engine(f"duckdb:///{database_path}")
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        
        self.logger.info(f"SQLAlchemy Inspector initialized for: {database_path}")
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database.
        
        Returns:
            List of table names
        """
        try:
            # Force refresh the inspector cache
            self.inspector = inspect(self.engine)
            
            tables = self.inspector.get_table_names()
            self.logger.debug(f"Found {len(tables)} tables: {tables}")
            return tables
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get table names: {e}")
            return []
    
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed column information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column dictionaries with name, type, nullable, default, etc.
        """
        try:
            columns = self.inspector.get_columns(table_name)
            
            # Enhance column info with additional metadata
            enhanced_columns = []
            for col in columns:
                enhanced_col = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True),
                    'default': col.get('default'),
                    'autoincrement': col.get('autoincrement', False),
                    'primary_key': col.get('primary_key', False)
                }
                enhanced_columns.append(enhanced_col)
            
            self.logger.debug(f"Found {len(enhanced_columns)} columns for table '{table_name}'")
            return enhanced_columns
            
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get columns for table '{table_name}': {e}")
            return []
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """Get primary key columns for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of primary key column names
        """
        try:
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            pk_columns = pk_constraint.get('constrained_columns', [])
            self.logger.debug(f"Primary keys for '{table_name}': {pk_columns}")
            return pk_columns
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get primary keys for table '{table_name}': {e}")
            return []
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key constraints for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of foreign key constraint dictionaries
        """
        try:
            fk_constraints = self.inspector.get_foreign_keys(table_name)
            self.logger.debug(f"Found {len(fk_constraints)} foreign keys for table '{table_name}'")
            return fk_constraints
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get foreign keys for table '{table_name}': {e}")
            return []
    
    def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of index dictionaries
        """
        try:
            indexes = self.inspector.get_indexes(table_name)
            self.logger.debug(f"Found {len(indexes)} indexes for table '{table_name}'")
            return indexes
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get indexes for table '{table_name}': {e}")
            return []
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics using SQL queries.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table statistics
        """
        try:
            with self.engine.connect() as conn:
                # Get row count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
                
                # Get table size (approximation for DuckDB)
                size_result = conn.execute(text(f"SELECT COUNT(*) * 1000 FROM {table_name}"))  # Rough estimate
                estimated_size = size_result.scalar()
                
                stats = {
                    'row_count': row_count,
                    'estimated_size_bytes': estimated_size,
                    'columns_count': len(self.get_columns(table_name))
                }
                
                self.logger.debug(f"Table stats for '{table_name}': {stats}")
                return stats
                
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to get table stats for '{table_name}': {e}")
            return {'row_count': 0, 'estimated_size_bytes': 0, 'columns_count': 0}
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get comprehensive database summary.
        
        Returns:
            Dictionary with database-wide statistics and metadata
        """
        try:
            tables = self.get_tables()
            
            summary = {
                'database_path': str(self.database_path),
                'total_tables': len(tables),
                'tables': {}
            }
            
            total_rows = 0
            total_columns = 0
            
            for table in tables:
                table_info = {
                    'columns': self.get_columns(table),
                    'primary_keys': self.get_primary_keys(table),
                    'foreign_keys': self.get_foreign_keys(table),
                    'indexes': self.get_indexes(table),
                    'stats': self.get_table_stats(table)
                }
                
                summary['tables'][table] = table_info
                total_rows += table_info['stats']['row_count']
                total_columns += table_info['stats']['columns_count']
            
            summary['total_rows'] = total_rows
            summary['total_columns'] = total_columns
            
            self.logger.info(f"Database summary: {len(tables)} tables, {total_rows} total rows")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate database summary: {e}")
            return {
                'database_path': str(self.database_path),
                'total_tables': 0,
                'tables': {},
                'total_rows': 0,
                'total_columns': 0,
                'error': str(e)
            }
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a custom SQL query and return results.
        
        Args:
            query: SQL query string
            
        Returns:
            List of result dictionaries
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Convert to list of dictionaries
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                
                self.logger.debug(f"Query executed successfully, returned {len(rows)} rows")
                return rows
                
        except SQLAlchemyError as e:
            self.logger.error(f"Query execution failed: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        try:
            self.engine.dispose()
            self.logger.debug("SQLAlchemy Inspector connection closed")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")


def create_inspector(database_path: str) -> Optional[SQLAlchemyInspector]:
    """Factory function to create SQLAlchemy inspector.
    
    Args:
        database_path: Path to DuckDB database
        
    Returns:
        SQLAlchemyInspector instance or None if creation fails
    """
    try:
        return SQLAlchemyInspector(database_path)
    except Exception as e:
        logger = get_logger("tabletalk.sqlalchemy_inspector")
        logger.error(f"Failed to create SQLAlchemy inspector: {e}")
        return None
