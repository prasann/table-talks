"""Simplified metadata storage using DuckDB."""

from pathlib import Path
from typing import List, Dict, Any
import duckdb
from datetime import datetime

from src.utils.logger import get_logger


class MetadataStore:
    """Simplified schema metadata storage using DuckDB."""
    
    def __init__(self, db_path: str = "./database/metadata.duckdb"):
        """Initialize the metadata store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("tabletalk.metadata")
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_info (
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    null_count INTEGER,
                    unique_count INTEGER,
                    total_rows INTEGER,
                    file_size_mb REAL,
                    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_name ON schema_info(file_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_column_name ON schema_info(column_name)")
    
    def _execute_query(self, query: str, params: List = None) -> List[tuple]:
        """Execute query and return results."""
        with duckdb.connect(str(self.db_path)) as conn:
            return conn.execute(query, params or []).fetchall()
    
    def store_schema_info(self, schema_data: List[Dict[str, Any]]) -> None:
        """Store schema information for a file."""
        if not schema_data:
            return
            
        with duckdb.connect(str(self.db_path)) as conn:
            file_name = schema_data[0]['file_name']
            conn.execute("DELETE FROM schema_info WHERE file_name = ?", [file_name])
            
            conn.executemany("""
                INSERT INTO schema_info 
                (file_name, file_path, column_name, data_type, null_count, 
                 unique_count, total_rows, file_size_mb, last_scanned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (row['file_name'], row['file_path'], row['column_name'], row['data_type'],
                 row['null_count'], row['unique_count'], row['total_rows'], 
                 row['file_size_mb'], datetime.now())
                for row in schema_data
            ])
    
    def get_file_schema(self, file_name: str) -> List[Dict[str, Any]]:
        """Get schema for a specific file."""
        rows = self._execute_query("""
            SELECT column_name, data_type, null_count, unique_count, total_rows
            FROM schema_info WHERE file_name = ? ORDER BY column_name
        """, [file_name])
        
        return [{'column_name': r[0], 'data_type': r[1], 'null_count': r[2], 
                'unique_count': r[3], 'total_rows': r[4]} for r in rows]
    
    def list_all_files(self) -> List[Dict[str, Any]]:
        """Get list of all files."""
        rows = self._execute_query("""
            SELECT file_name, file_path, COUNT(column_name) as column_count,
                   MAX(total_rows) as total_rows, MAX(file_size_mb) as file_size_mb,
                   MAX(last_scanned) as last_scanned
            FROM schema_info GROUP BY file_name, file_path ORDER BY file_name
        """)
        
        return [{'file_name': r[0], 'file_path': r[1], 'column_count': r[2],
                'total_rows': r[3], 'file_size_mb': r[4], 'last_scanned': r[5]} for r in rows]
    
    def find_columns_by_name(self, column_name: str) -> List[Dict[str, Any]]:
        """Find files containing a column."""
        rows = self._execute_query("""
            SELECT file_name, column_name, data_type, null_count, unique_count
            FROM schema_info WHERE column_name ILIKE ? ORDER BY file_name
        """, [f"%{column_name}%"])
        
        return [{'file_name': r[0], 'column_name': r[1], 'data_type': r[2],
                'null_count': r[3], 'unique_count': r[4]} for r in rows]
    
    def detect_type_mismatches(self) -> List[Dict[str, Any]]:
        """Detect columns with different types across files."""
        rows = self._execute_query("""
            SELECT column_name, data_type, COUNT(*) as file_count,
                   string_agg(file_name, ', ') as files
            FROM schema_info
            GROUP BY column_name, data_type
            HAVING column_name IN (
                SELECT column_name FROM schema_info 
                GROUP BY column_name HAVING COUNT(DISTINCT data_type) > 1
            )
            ORDER BY column_name, data_type
        """)
        
        return [{'column_name': r[0], 'data_type': r[1], 'file_count': r[2], 'files': r[3]} for r in rows]
    
    def get_common_columns(self) -> List[Dict[str, Any]]:
        """Find columns appearing in multiple files."""
        rows = self._execute_query("""
            SELECT column_name, COUNT(DISTINCT file_name) as file_count,
                   COUNT(DISTINCT data_type) as type_variations,
                   string_agg(DISTINCT data_type, ', ') as data_types,
                   string_agg(DISTINCT file_name, ', ') as files
            FROM schema_info
            GROUP BY column_name
            HAVING COUNT(DISTINCT file_name) > 1
            ORDER BY file_count DESC, column_name
        """)
        
        return [{'column_name': r[0], 'file_count': r[1], 'type_variations': r[2],
                'data_types': r[3], 'files': r[4]} for r in rows]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = self._execute_query("""
            SELECT COUNT(DISTINCT file_name) as total_files,
                   COUNT(*) as total_columns,
                   COUNT(DISTINCT column_name) as unique_columns,
                   AVG(file_size_mb) as avg_file_size_mb,
                   MAX(last_scanned) as last_scan_time
            FROM schema_info
        """)[0]
        
        return {
            'total_files': stats[0] or 0,
            'total_columns': stats[1] or 0,
            'unique_columns': stats[2] or 0,
            'avg_file_size_mb': round(stats[3] or 0, 2),
            'last_scan_time': stats[4]
        }
