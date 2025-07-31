"""Simplified schema extraction from CSV and Parquet files."""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

from utils.logger import get_logger


class SchemaExtractor:
    """Simplified schema extraction from files."""
    
    def __init__(self, max_file_size_mb: int = 100, sample_size: int = 1000):
        """Initialize the extractor."""
        self.max_file_size_mb = max_file_size_mb
        self.sample_size = sample_size
        self.logger = get_logger("tabletalk.extractor")
        self.supported_formats = {'.csv', '.parquet'}
    
    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract schema from a single file."""
        path = Path(file_path)
        
        # Basic validation
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported format: {path.suffix}")
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB > {self.max_file_size_mb}MB")
        
        # Load data
        try:
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(path, nrows=self.sample_size if self.sample_size > 0 else None)
            else:  # parquet
                df = pd.read_parquet(path)
                if self.sample_size > 0 and len(df) > self.sample_size:
                    df = df.sample(n=self.sample_size, random_state=42)
        except Exception as e:
            raise ValueError(f"Could not read file: {str(e)}")
        
        # Extract schema
        return self._extract_schema_info(df, path, file_size_mb)
    
    def extract_from_directory(self, directory_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract schema from all files in a directory."""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")
        
        results = {}
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    results[file_path.name] = self.extract_from_file(str(file_path))
                except Exception as e:
                    self.logger.warning(f"Skipping {file_path.name}: {str(e)}")
        
        return results
    
    def _extract_schema_info(self, df: pd.DataFrame, path: Path, file_size_mb: float) -> List[Dict[str, Any]]:
        """Extract schema information from DataFrame."""
        schema_info = []
        total_rows = len(df)
        
        for column in df.columns:
            series = df[column]
            data_type = self._normalize_dtype(series.dtype)
            
            schema_info.append({
                'file_name': path.name,
                'file_path': str(path.absolute()),
                'column_name': str(column),
                'data_type': data_type,
                'null_count': int(series.isnull().sum()),
                'unique_count': int(series.nunique()),
                'total_rows': total_rows,
                'file_size_mb': round(file_size_mb, 2)
            })
        
        return schema_info
    
    def _normalize_dtype(self, dtype) -> str:
        """Convert pandas dtype to standard string."""
        dtype_str = str(dtype).lower()
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
        else:
            return 'string'  # Default fallback
