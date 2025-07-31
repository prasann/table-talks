"""Metadata storage using DuckDB for schema information."""

from pathlib import Path
from typing import List, Dict, Optional, Any
import duckdb
import logging
from datetime import datetime
import os
import sys

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Always use absolute imports from src
from utils.logger import get_logger


class MetadataStore:
    """Handles schema metadata storage and retrieval using DuckDB."""
    
    def __init__(self, db_path: str = "./database/metadata.duckdb"):
        """Initialize the metadata store.
        
        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("tabletalk.metadata")
        
        # Initialize database and create tables
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database and create schema_info table if it doesn't exist."""
        with duckdb.connect(str(self.db_path)) as conn:
            # Check if table exists
            table_exists = conn.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'schema_info'
            """).fetchone()[0] > 0
            
            if not table_exists:
                conn.execute("""
                    CREATE TABLE schema_info (
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
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_file_name ON schema_info(file_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_column_name ON schema_info(column_name)")
                
                self.logger.info(f"Database initialized at {self.db_path}")
            else:
                self.logger.debug(f"Database already exists at {self.db_path}")
    
    def store_schema_info(self, schema_data: List[Dict[str, Any]]) -> None:
        """Store schema information for a file.
        
        Args:
            schema_data: List of dictionaries containing schema information
        """
        if not schema_data:
            return
            
        with duckdb.connect(str(self.db_path)) as conn:
            # Clear existing data for this file
            file_name = schema_data[0]['file_name']
            conn.execute("DELETE FROM schema_info WHERE file_name = ?", [file_name])
            
            # Insert new data
            conn.executemany("""
                INSERT INTO schema_info 
                (file_name, file_path, column_name, data_type, null_count, 
                 unique_count, total_rows, file_size_mb, last_scanned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    row['file_name'],
                    row['file_path'],
                    row['column_name'],
                    row['data_type'],
                    row['null_count'],
                    row['unique_count'],
                    row['total_rows'],
                    row['file_size_mb'],
                    datetime.now()
                )
                for row in schema_data
            ])
            
        self.logger.info(f"Stored schema info for {file_name} ({len(schema_data)} columns)")
    
    def get_file_schema(self, file_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific file.
        
        Args:
            file_name: Name of the file
            
        Returns:
            List of dictionaries containing column information
        """
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT column_name, data_type, null_count, unique_count, total_rows
                FROM schema_info 
                WHERE file_name = ?
                ORDER BY column_name
            """, [file_name]).fetchall()
            
            return [
                {
                    'column_name': row[0],
                    'data_type': row[1],
                    'null_count': row[2],
                    'unique_count': row[3],
                    'total_rows': row[4]
                }
                for row in result
            ]
    
    def list_all_files(self) -> List[Dict[str, Any]]:
        """Get list of all scanned files with basic statistics.
        
        Returns:
            List of dictionaries containing file information
        """
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT 
                    file_name,
                    file_path,
                    COUNT(column_name) as column_count,
                    MAX(total_rows) as total_rows,
                    MAX(file_size_mb) as file_size_mb,
                    MAX(last_scanned) as last_scanned
                FROM schema_info 
                GROUP BY file_name, file_path
                ORDER BY file_name
            """).fetchall()
            
            return [
                {
                    'file_name': row[0],
                    'file_path': row[1],
                    'column_count': row[2],
                    'total_rows': row[3],
                    'file_size_mb': row[4],
                    'last_scanned': row[5]
                }
                for row in result
            ]
    
    def find_columns_by_name(self, column_name: str) -> List[Dict[str, Any]]:
        """Find all files that contain a specific column name.
        
        Args:
            column_name: Name of the column to search for
            
        Returns:
            List of dictionaries containing file and column information
        """
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT file_name, column_name, data_type, null_count, unique_count
                FROM schema_info 
                WHERE column_name ILIKE ?
                ORDER BY file_name
            """, [f"%{column_name}%"]).fetchall()
            
            return [
                {
                    'file_name': row[0],
                    'column_name': row[1],
                    'data_type': row[2],
                    'null_count': row[3],
                    'unique_count': row[4]
                }
                for row in result
            ]
    
    def detect_type_mismatches(self) -> List[Dict[str, Any]]:
        """Detect columns with the same name but different data types across files.
        
        Returns:
            List of dictionaries containing mismatch information
        """
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT 
                    column_name,
                    data_type,
                    COUNT(*) as file_count,
                    string_agg(file_name, ', ') as files
                FROM schema_info
                GROUP BY column_name, data_type
                HAVING column_name IN (
                    SELECT column_name 
                    FROM schema_info 
                    GROUP BY column_name 
                    HAVING COUNT(DISTINCT data_type) > 1
                )
                ORDER BY column_name, data_type
            """).fetchall()
            
            return [
                {
                    'column_name': row[0],
                    'data_type': row[1],
                    'file_count': row[2],
                    'files': row[3]
                }
                for row in result
            ]
    
    def get_common_columns(self) -> List[Dict[str, Any]]:
        """Find columns that appear in multiple files.
        
        Returns:
            List of dictionaries containing common column information
        """
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute("""
                SELECT 
                    column_name,
                    COUNT(DISTINCT file_name) as file_count,
                    COUNT(DISTINCT data_type) as type_variations,
                    string_agg(DISTINCT data_type, ', ') as data_types,
                    string_agg(DISTINCT file_name, ', ') as files
                FROM schema_info
                GROUP BY column_name
                HAVING COUNT(DISTINCT file_name) > 1
                ORDER BY file_count DESC, column_name
            """).fetchall()
            
            return [
                {
                    'column_name': row[0],
                    'file_count': row[1],
                    'type_variations': row[2],
                    'data_types': row[3],
                    'files': row[4]
                }
                for row in result
            ]
    
    def clear_file_data(self, file_name: str) -> None:
        """Remove all data for a specific file.
        
        Args:
            file_name: Name of the file to remove
        """
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM schema_info WHERE file_name = ?", [file_name])
        
        self.logger.info(f"Cleared data for {file_name}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        with duckdb.connect(str(self.db_path)) as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(DISTINCT file_name) as total_files,
                    COUNT(*) as total_columns,
                    COUNT(DISTINCT column_name) as unique_columns,
                    AVG(file_size_mb) as avg_file_size_mb,
                    MAX(last_scanned) as last_scan_time
                FROM schema_info
            """).fetchone()
            
            return {
                'total_files': stats[0] or 0,
                'total_columns': stats[1] or 0,
                'unique_columns': stats[2] or 0,
                'avg_file_size_mb': round(stats[3] or 0, 2),
                'last_scan_time': stats[4]
            }
