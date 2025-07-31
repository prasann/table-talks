"""Simplified SQLAlchemy database introspection."""

from typing import Dict, List, Any
from pathlib import Path

from utils.logger import get_logger
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


class SQLAlchemyInspector:
    """Simplified database introspection using SQLAlchemy."""
    
    def __init__(self, database_path: str):
        """Initialize SQLAlchemy inspector."""
        self.database_path = Path(database_path)
        self.logger = get_logger("tabletalk.sqlalchemy_inspector")
        self.engine = create_engine(f"duckdb:///{database_path}")
        self.inspector = inspect(self.engine)
    
    def get_table_names(self) -> List[str]:
        """Get all table names."""
        try:
            return self.inspector.get_table_names()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting table names: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get comprehensive table information."""
        try:
            columns = self.inspector.get_columns(table_name)
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            
            return {
                'table_name': table_name,
                'columns': [{'name': col['name'], 'type': str(col['type'])} for col in columns],
                'column_count': len(columns),
                'row_count': row_count
            }
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting table info for {table_name}: {e}")
            return {'table_name': table_name, 'columns': [], 'column_count': 0, 'row_count': 0}
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database summary statistics."""
        try:
            tables = self.get_table_names()
            total_rows = 0
            total_columns = 0
            
            table_details = []
            for table_name in tables:
                table_info = self.get_table_info(table_name)
                total_rows += table_info['row_count']
                total_columns += table_info['column_count']
                table_details.append(table_info)
            
            return {
                'total_tables': len(tables),
                'total_rows': total_rows,
                'total_columns': total_columns,
                'tables': table_details
            }
        except Exception as e:
            self.logger.error(f"Error getting database summary: {e}")
            return {'total_tables': 0, 'total_rows': 0, 'total_columns': 0, 'tables': []}
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except SQLAlchemyError as e:
            self.logger.error(f"Error executing query: {e}")
            return []
    
    def close(self):
        """Close database connections."""
        if hasattr(self, 'engine'):
            self.engine.dispose()


def create_inspector(database_path: str):
    """Factory function to create SQLAlchemy inspector."""
    try:
        return SQLAlchemyInspector(database_path)
    except Exception as e:
        get_logger("tabletalk.sqlalchemy_inspector").error(f"Failed to create inspector: {e}")
        return None
