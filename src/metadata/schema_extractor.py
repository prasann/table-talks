"""Schema extraction from CSV and Parquet files."""

import pandas as pd
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger


class SchemaExtractor:
    """Extracts schema information from CSV and Parquet files."""
    
    def __init__(self, max_file_size_mb: int = 100, sample_size: int = 1000):
        """Initialize the schema extractor.
        
        Args:
            max_file_size_mb: Maximum file size to process (in MB)
            sample_size: Number of rows to sample for statistics
        """
        self.max_file_size_mb = max_file_size_mb
        self.sample_size = sample_size
        self.logger = get_logger("tabletalk.extractor")
        
        # Supported file formats
        self.supported_formats = {'.csv', '.parquet'}
    
    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract schema information from a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of dictionaries containing column schema information
        """
        path = Path(file_path)
        
        # Validate file
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        try:
            # Load data based on file type
            if path.suffix.lower() == '.csv':
                df = self._load_csv(path)
            elif path.suffix.lower() == '.parquet':
                df = self._load_parquet(path)
            else:
                raise ValueError(f"Unsupported format: {path.suffix}")
            
            # Extract schema information
            schema_info = self._extract_schema_info(df, path, file_size_mb)
            
            self.logger.info(f"Extracted schema from {path.name}: {len(schema_info)} columns")
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Error extracting schema from {file_path}: {str(e)}")
            raise
    
    def extract_from_directory(self, directory_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract schema information from all supported files in a directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Dictionary mapping file names to their schema information
        """
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        results = {}
        
        # Find all supported files
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    schema_info = self.extract_from_file(str(file_path))
                    results[file_path.name] = schema_info
                except Exception as e:
                    self.logger.warning(f"Skipping {file_path.name}: {str(e)}")
        
        self.logger.info(f"Processed {len(results)} files from {directory_path}")
        return results
    
    def _load_csv(self, path: Path) -> pd.DataFrame:
        """Load CSV file with appropriate settings.
        
        Args:
            path: Path to the CSV file
            
        Returns:
            Pandas DataFrame
        """
        # Try different encodings and separators
        encodings = ['utf-8', 'latin-1', 'cp1252']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    # Read a sample first to determine the best parameters
                    sample_df = pd.read_csv(
                        path, 
                        encoding=encoding, 
                        separator=sep, 
                        nrows=10,
                        low_memory=False
                    )
                    
                    # If we get reasonable columns, use this configuration
                    if len(sample_df.columns) > 1:
                        # Read the full file (or sample)
                        df = pd.read_csv(
                            path,
                            encoding=encoding,
                            separator=sep,
                            nrows=self.sample_size if self.sample_size > 0 else None,
                            low_memory=False
                        )
                        
                        self.logger.debug(f"Loaded CSV {path.name} with encoding={encoding}, sep='{sep}'")
                        return df
                        
                except Exception:
                    continue
        
        # Fallback to pandas default
        try:
            df = pd.read_csv(
                path,
                nrows=self.sample_size if self.sample_size > 0 else None,
                low_memory=False
            )
            return df
        except Exception as e:
            raise ValueError(f"Could not read CSV file: {str(e)}")
    
    def _load_parquet(self, path: Path) -> pd.DataFrame:
        """Load Parquet file.
        
        Args:
            path: Path to the Parquet file
            
        Returns:
            Pandas DataFrame
        """
        try:
            # For parquet, we can read metadata first to get row count
            df = pd.read_parquet(path)
            
            # Sample if the file is large
            if self.sample_size > 0 and len(df) > self.sample_size:
                df = df.sample(n=self.sample_size, random_state=42)
            
            return df
            
        except Exception as e:
            raise ValueError(f"Could not read Parquet file: {str(e)}")
    
    def _extract_schema_info(self, df: pd.DataFrame, path: Path, file_size_mb: float) -> List[Dict[str, Any]]:
        """Extract schema information from a DataFrame.
        
        Args:
            df: Pandas DataFrame
            path: Path to the original file
            file_size_mb: Size of the file in MB
            
        Returns:
            List of dictionaries containing column information
        """
        schema_info = []
        total_rows = len(df)
        
        for column in df.columns:
            try:
                # Get basic statistics
                series = df[column]
                null_count = series.isnull().sum()
                unique_count = series.nunique()
                
                # Convert pandas dtype to more readable string
                data_type = self._normalize_dtype(series.dtype)
                
                column_info = {
                    'file_name': path.name,
                    'file_path': str(path.absolute()),
                    'column_name': str(column),
                    'data_type': data_type,
                    'null_count': int(null_count),
                    'unique_count': int(unique_count),
                    'total_rows': total_rows,
                    'file_size_mb': round(file_size_mb, 2)
                }
                
                schema_info.append(column_info)
                
            except Exception as e:
                self.logger.warning(f"Error processing column {column}: {str(e)}")
                # Add basic info even if statistics fail
                schema_info.append({
                    'file_name': path.name,
                    'file_path': str(path.absolute()),
                    'column_name': str(column),
                    'data_type': 'unknown',
                    'null_count': 0,
                    'unique_count': 0,
                    'total_rows': total_rows,
                    'file_size_mb': round(file_size_mb, 2)
                })
        
        return schema_info
    
    def _normalize_dtype(self, dtype) -> str:
        """Normalize pandas dtype to a standard string representation.
        
        Args:
            dtype: Pandas dtype
            
        Returns:
            Normalized data type string
        """
        dtype_str = str(dtype).lower()
        
        # Map common pandas dtypes to standard names
        if 'int' in dtype_str:
            return 'integer'
        elif 'float' in dtype_str:
            return 'float'
        elif 'bool' in dtype_str:
            return 'boolean'
        elif 'datetime' in dtype_str:
            return 'datetime'
        elif 'object' in dtype_str:
            return 'string'
        elif 'category' in dtype_str:
            return 'category'
        else:
            return dtype_str
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.supported_formats)
