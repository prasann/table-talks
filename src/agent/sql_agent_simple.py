"""Simplified SQL Agent for efficient query processing and result formatting."""

import logging
from typing import Dict, List, Optional, Any
import re

try:
    from ..utils.logger import get_logger
    from .query_strategy import QueryProcessingStrategy
    from ..metadata.metadata_store import MetadataStore
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger
    from agent.query_strategy import QueryProcessingStrategy
    from metadata.metadata_store import MetadataStore


class SQLAgentSimple(QueryProcessingStrategy):
    """Simplified SQL Agent that directly generates and executes SQL with minimal overhead."""
    
    def __init__(self, llm_agent=None, metadata_store: MetadataStore = None, db_path: str = "./database/metadata.duckdb"):
        self.metadata_store = metadata_store or MetadataStore(db_path)
        self.logger = get_logger("tabletalk.sql_agent_simple")
        self.llm = llm_agent
        self.logger.info("[SQL_SIMPLE] Simple SQL Agent initialized")
    
    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse query using simple pattern matching and direct SQL generation."""
        return {
            "success": True,
            "parsed_query": {
                "intent": f"Simple SQL query: {query}",
                "entities": [],
                "files": available_files or []
            }
        }
    
    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute SQL plan with minimal steps."""
        try:
            query = plan.get("query", "").lower()
            self.logger.info(f"[SQL_SIMPLE] Processing: {query}")
            
            # Generate SQL directly
            sql_query = self._generate_sql(query)
            if not sql_query:
                return {"success": False, "error": "Could not generate SQL query"}
            
            # Execute SQL
            result = self._execute_sql(sql_query)
            if not result.get("success", False):
                return {"success": False, "error": result.get("error", "SQL execution failed")}
            
            # Format results concisely
            formatted_result = self._format_results_simple(
                result.get("data", []), 
                result.get("columns", []), 
                query
            )
            
            return {
                "success": True,
                "result": formatted_result
            }
            
        except Exception as e:
            self.logger.error(f"[SQL_SIMPLE] Error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_sql(self, query: str) -> str:
        """Generate SQL query using simple rules and optional LLM."""
        
        # Try rule-based SQL generation first (fast)
        sql = self._generate_sql_rules(query)
        if sql:
            self.logger.info(f"[SQL_SIMPLE] Rule-based SQL: {sql}")
            return sql
        
        # Fallback to LLM if available
        if self.llm and hasattr(self.llm, 'llm'):
            return self._generate_sql_llm(query)
        
        return ""
    
    def _generate_sql_rules(self, query: str) -> str:
        """Generate SQL using simple pattern matching rules."""
        query = query.lower().strip()
        
        # Schema/columns queries for customers - prioritize this pattern
        if ("schema" in query or "column" in query) and "customer" in query:
            return "SELECT column_name, data_type, null_count, unique_count FROM schema_info WHERE file_name LIKE '%customers%' ORDER BY column_name;"
        
        # Data types queries
        if "data type" in query and "customer" in query:
            return "SELECT DISTINCT column_name, data_type FROM schema_info WHERE file_name LIKE '%customers%' ORDER BY column_name;"
        
        # General schema queries for any file
        file_patterns = ["customer", "order", "review", "user"]
        for pattern in file_patterns:
            if pattern in query and ("structure" in query or "column" in query or "schema" in query):
                return f"SELECT column_name, data_type, null_count, unique_count FROM schema_info WHERE file_name LIKE '%{pattern}%' ORDER BY column_name;"
        
        # File listing
        if "file" in query and ("list" in query or "show" in query or "what" in query):
            return "SELECT DISTINCT file_name, total_rows, file_size_mb FROM schema_info ORDER BY file_name;"
        
        # Catch-all for table/schema questions
        if "table" in query or "schema" in query:
            return "SELECT DISTINCT file_name FROM schema_info ORDER BY file_name;"
        
        return ""
    
    def _generate_sql_llm(self, query: str) -> str:
        """Generate SQL using LLM with concise prompt."""
        prompt = f"""Generate a SQL query for: "{query}"

Schema: schema_info(file_name, column_name, data_type, null_count, unique_count, total_rows, file_size_mb)

Rules:
- Use LIKE '%customers%' for customer file queries  
- Use LIKE '%orders%' for order file queries
- Return only the SQL, no explanations, no comments
- End with semicolon
- Use standard SQL syntax (no backticks, use double quotes if needed)

Examples:
- For "customers schema": SELECT column_name, data_type FROM schema_info WHERE file_name LIKE '%customers%';
- For "customer columns": SELECT column_name, data_type FROM schema_info WHERE file_name LIKE '%customers%';

SQL:"""
        
        try:
            response = self.llm.llm.invoke(prompt)
            sql = response.content if hasattr(response, 'content') else str(response)
            
            # Clean the SQL more aggressively
            sql = re.sub(r'```sql|```', '', sql).strip()
            sql = re.sub(r'^(SELECT|WITH)', r'\1', sql, flags=re.IGNORECASE)
            
            # Fix backticks - replace with double quotes or remove
            sql = sql.replace('`', '"')
            
            # Remove comments and extra text
            sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
            sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
            
            # Remove double semicolons and extra whitespace
            sql = sql.replace(';;', ';')
            sql = re.sub(r'\s+', ' ', sql).strip()
            
            if not sql.endswith(';'):
                sql += ';'
            
            self.logger.info(f"[SQL_SIMPLE] LLM generated SQL: {sql}")
            return sql
            
        except Exception as e:
            self.logger.error(f"[SQL_SIMPLE] LLM SQL generation failed: {e}")
            return ""
    
    def _execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query against the metadata database."""
        try:
            import duckdb
            
            self.logger.info(f"[SQL_SIMPLE] Executing: {sql_query}")
            
            with duckdb.connect(str(self.metadata_store.db_path)) as conn:
                result = conn.execute(sql_query).fetchall()
                columns = [desc[0] for desc in conn.description] if conn.description else []
                
                return {
                    "success": True,
                    "data": result,
                    "columns": columns,
                    "row_count": len(result)
                }
                
        except Exception as e:
            self.logger.error(f"[SQL_SIMPLE] SQL execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_results_simple(self, data: List, columns: List[str], query: str) -> str:
        """Format results in a concise, readable format."""
        if not data:
            return f"No data found for: {query}"
        
        # For small result sets, show all data
        if len(data) <= 10 and len(columns) <= 4:
            return self._format_table(data, columns)
        
        # For larger sets, provide summary
        if "data type" in query.lower():
            return self._format_datatypes(data, columns)
        elif "schema" in query.lower() or "column" in query.lower():
            return self._format_schema(data, columns)
        elif "file" in query.lower():
            return self._format_files(data, columns)
        else:
            return self._format_table(data[:10], columns) + f"\n\n(Showing first 10 of {len(data)} rows)"
    
    def _format_table(self, data: List, columns: List[str]) -> str:
        """Format data as a simple table."""
        if not data or not columns:
            return "No data to display"
        
        # Calculate column widths
        widths = [len(col) for col in columns]
        for row in data:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Build table
        header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
        separator = "-+-".join("-" * width for width in widths)
        
        rows = []
        for row in data:
            formatted_row = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            rows.append(formatted_row)
        
        return f"{header}\n{separator}\n" + "\n".join(rows)
    
    def _format_datatypes(self, data: List, columns: List[str]) -> str:
        """Format data types in a concise list."""
        if "column_name" in columns and "data_type" in columns:
            col_idx = columns.index("column_name")
            type_idx = columns.index("data_type")
            
            lines = [f"Data types in customer file:"]
            for row in data:
                lines.append(f"  {row[col_idx]}: {row[type_idx]}")
            return "\n".join(lines)
        
        return self._format_table(data, columns)
    
    def _format_schema(self, data: List, columns: List[str]) -> str:
        """Format schema information concisely."""
        if len(columns) >= 2:
            lines = [f"Schema information:"]
            for row in data:
                col_name = row[0]
                data_type = row[1] if len(row) > 1 else "unknown"
                extra_info = []
                
                if len(row) > 2 and row[2] is not None:  # null_count
                    if row[2] > 0:
                        extra_info.append(f"{row[2]} nulls")
                
                if len(row) > 3 and row[3] is not None:  # unique_count
                    extra_info.append(f"{row[3]} unique")
                
                extra = f" ({', '.join(extra_info)})" if extra_info else ""
                lines.append(f"  {col_name}: {data_type}{extra}")
            
            return "\n".join(lines)
        
        return self._format_table(data, columns)
    
    def _format_files(self, data: List, columns: List[str]) -> str:
        """Format file information concisely."""
        lines = ["Available files:"]
        for row in data:
            file_name = row[0]
            details = []
            if len(row) > 1 and row[1] is not None:  # total_rows
                details.append(f"{row[1]} rows")
            if len(row) > 2 and row[2] is not None:  # file_size_mb
                details.append(f"{row[2]:.1f}MB")
            
            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"  {file_name}{detail_str}")
        
        return "\n".join(lines)
    
    def synthesize_response(self, results: str, query: str, plan: Dict[str, Any] = None) -> str:
        """Synthesize the final response for the user."""
        # For the simple agent, we return results directly since formatting is already done
        return results
    
    def get_help_text(self) -> str:
        """Get help text for this strategy."""
        return """Simple SQL Agent - Fast and lightweight data queries
        
Available query types:
• Data types: "what data types are in [file]"
• Schema info: "show me the schema for [file]" 
• File listing: "what files are available"
• Column details: "what are the columns in [file]"

Examples:
• "what data types are in customers file"
• "show me the schema for orders"
• "what files do we have"
"""
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        return {
            "name": "Simple SQL Agent",
            "type": "sql_agent_simple",
            "description": "Lightweight SQL agent with rule-based generation and concise formatting",
            "capabilities": ["rule_based_sql", "optional_llm_fallback", "concise_formatting", "fast_execution"]
        }
