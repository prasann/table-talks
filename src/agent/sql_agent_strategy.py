"""SQL Agent strategy for query processing using LangChain SQL agents."""

import logging
from typing import Dict, List, Optional, Any
import json

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


class SQLAgentStrategy(QueryProcessingStrategy):
    """Query processing strategy using LangChain SQL Agent with DuckDB."""
    
    def __init__(self, llm_agent=None, metadata_store: MetadataStore = None, db_path: str = "./database/metadata.duckdb"):
        """Initialize the SQL agent strategy."""
        self.llm = llm_agent
        self.logger = get_logger("tabletalk.sql_agent")
        self.metadata_store = metadata_store or MetadataStore(db_path)
        self.db_path = db_path
        
        # Log initialization details
        self.logger.info(f"[SQL_AGENT] Initializing SQL Agent Strategy")
        self.logger.debug(f"[SQL_AGENT] LLM Agent provided: {llm_agent is not None}")
        self.logger.debug(f"[SQL_AGENT] MetadataStore provided: {metadata_store is not None}")
        self.logger.debug(f"[SQL_AGENT] Database path: {db_path}")
        
        # Initialize SQL tools and agent
        self._sql_db = None
        self._sql_agent = None
        self._initialize_sql_agent()
        
        # Define available operation types for the agent
        self.operation_types = {
            "schema_analysis": {
                "description": "Analyze file schemas, columns, and data types",
                "examples": ["show schema of customers.csv", "what columns are in orders", "describe file structure"]
            },
            "file_discovery": {
                "description": "Find and list available files",
                "examples": ["what files do we have", "list all files", "show available data"]
            },
            "column_search": {
                "description": "Find files containing specific columns",
                "examples": ["which files have user_id", "find email column", "search for price fields"]
            },
            "data_quality": {
                "description": "Detect data quality issues and inconsistencies",
                "examples": ["find type mismatches", "detect inconsistencies", "data quality problems"]
            },
            "relationship_analysis": {
                "description": "Find relationships and common patterns across files",
                "examples": ["common columns", "shared fields", "file relationships"]
            },
            "database_overview": {
                "description": "Get overall statistics and summaries",
                "examples": ["database summary", "overall stats", "how many files and columns"]
            }
        }
    
    def _initialize_sql_agent(self):
        """Initialize SQL agent using existing MetadataStore to avoid connection conflicts."""
        try:
            self.logger.info(f"[SQL_AGENT] Starting SQL Agent initialization")
            
            # Instead of creating a new DuckDB connection through LangChain,
            # use our existing MetadataStore which already has a working connection
            if self.llm and hasattr(self.llm, 'llm'):
                self.logger.debug(f"[SQL_AGENT] LLM is available and has 'llm' attribute")
                self.logger.debug(f"[SQL_AGENT] LLM type: {type(self.llm)}")
                
                if hasattr(self.llm, 'model_name'):
                    self.logger.debug(f"[SQL_AGENT] LLM model: {self.llm.model_name}")
                
                # We'll use our MetadataStore for SQL execution
                # and the LLM for query generation
                self._sql_agent = "direct_execution"  # Use direct SQL execution
                
                self.logger.info(f"[SQL_AGENT] SQL Agent initialized with direct MetadataStore execution")
                self.logger.debug(f"[SQL_AGENT] MetadataStore database path: {self.metadata_store.db_path}")
                
                # Test the connection
                try:
                    import duckdb
                    with duckdb.connect(str(self.metadata_store.db_path)) as conn:
                        # Quick test query to verify schema_info table exists
                        test_result = conn.execute("SELECT COUNT(*) FROM schema_info").fetchone()
                        self.logger.info(f"[SQL_AGENT] Database connection test successful, schema_info has {test_result[0]} rows")
                except Exception as test_error:
                    self.logger.warning(f"[SQL_AGENT] Database connection test failed: {test_error}")
                    self.logger.warning(f"[SQL_AGENT] This might mean the database is not initialized yet")
                
            else:
                self.logger.warning(f"[SQL_AGENT] LLM not available for SQL Agent")
                self.logger.debug(f"[SQL_AGENT] LLM object: {self.llm}")
                self.logger.debug(f"[SQL_AGENT] LLM has 'llm' attr: {hasattr(self.llm, 'llm') if self.llm else 'N/A'}")
                self.logger.warning(f"[SQL_AGENT] Using fallback mode")
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT] Failed to initialize SQL Agent: {e}")
            self.logger.error(f"[SQL_AGENT] Exception type: {type(e)}")
            import traceback
            self.logger.error(f"[SQL_AGENT] Full traceback: {traceback.format_exc()}")
            # For connection errors, we should still allow fallback to work
            self._sql_agent = None
    
    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse query and determine if it should use SQL agent or fallback.
        
        Returns:
            Dictionary with success/error status and parsed query plan
        """
        try:
            if not self._sql_agent:
                self.logger.warning("SQL Agent not available, using fallback parsing")
                return {
                    "success": True,
                    "parsed_query": self._fallback_parse(query, available_files)
                }
            
            # Analyze query to determine operation type
            operation_type = self._classify_query(query)
            
            return {
                "success": True,
                "parsed_query": {
                    "intent": f"SQL Agent query: {query}",
                    "operation_type": operation_type,
                    "query": query,
                    "strategy": "sql_agent",
                    "agent_mode": True
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing query: {e}")
            return {
                "success": False,
                "error": f"Failed to parse query: {str(e)}"
            }
    
    def _classify_query(self, query: str) -> str:
        """Classify the query into operation types."""
        query_lower = query.lower()
        
        # Simple classification based on keywords
        if any(word in query_lower for word in ["schema", "columns", "structure", "describe"]):
            return "schema_analysis"
        elif any(word in query_lower for word in ["files", "list", "show", "available"]):
            return "file_discovery"
        elif any(word in query_lower for word in ["find", "search", "which", "contains"]):
            return "column_search"
        elif any(word in query_lower for word in ["mismatch", "inconsistent", "quality", "problems"]):
            return "data_quality"
        elif any(word in query_lower for word in ["common", "shared", "relationship", "overlap"]):
            return "relationship_analysis"
        elif any(word in query_lower for word in ["summary", "overview", "stats", "total"]):
            return "database_overview"
        else:
            return "general_analysis"
    
    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute the query plan using SQL agent or fallback tools.
        
        Args:
            plan: The plan returned by parse_query
            schema_tools: SchemaTools instance (for fallback)
            
        Returns:
            Dictionary with success status and results
        """
        try:
            self.logger.info(f"[SQL_AGENT] Executing plan: {plan}")
            
            if plan.get("agent_mode") and self._sql_agent == "direct_execution":
                # Use direct SQL execution through MetadataStore
                query = plan.get("query", "")
                self.logger.info(f"[SQL_AGENT] Processing query via SQL Agent: '{query}'")
                
                # Generate SQL query using LLM
                self.logger.debug(f"[SQL_AGENT] Step 1: Generating SQL query from natural language")
                sql_query = self._generate_sql_query(query)
                
                if sql_query and (sql_query.strip().upper().startswith('SELECT') or sql_query.strip().upper().startswith('WITH')):
                    self.logger.info(f"[SQL_AGENT] Step 2: Generated valid SQL query: {sql_query}")
                    
                    # Execute the SQL query with retry logic
                    self.logger.debug(f"[SQL_AGENT] Step 3: Executing SQL query against DuckDB with retry logic")
                    execution_result = self._execute_sql_with_retry(sql_query, query)
                    
                    if execution_result['success']:
                        self.logger.info(f"[SQL_AGENT] Step 4: SQL execution successful")
                        
                        # Format the result
                        self.logger.debug(f"[SQL_AGENT] Step 5: Formatting SQL result")
                        formatted_result = self._format_sql_result(query, sql_query, execution_result['result'])
                        
                        self.logger.info(f"[SQL_AGENT] Query processing completed successfully")
                        return {
                            "success": True,
                            "result": formatted_result
                        }
                    else:
                        # SQL execution failed even with retries, fall back
                        self.logger.warning(f"[SQL_AGENT] SQL execution failed with retries: {execution_result.get('error')}, falling back to schema_tools")
                        return self._execute_fallback(plan, schema_tools)
                else:
                    # Invalid or unsafe SQL, fall back to schema_tools
                    self.logger.warning(f"[SQL_AGENT] Generated SQL was invalid or non-SELECT: '{sql_query}', using fallback")
                    return self._execute_fallback(plan, schema_tools)
            else:
                # Fallback to schema_tools for backward compatibility
                self.logger.info(f"[SQL_AGENT] Using fallback mode - agent_mode: {plan.get('agent_mode')}, sql_agent: {self._sql_agent}")
                return self._execute_fallback(plan, schema_tools)
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT] Error executing SQL Agent plan: {e}")
            self.logger.error(f"[SQL_AGENT] Exception type: {type(e)}")
            import traceback
            self.logger.error(f"[SQL_AGENT] Full traceback: {traceback.format_exc()}")
            
            # Try fallback on error
            try:
                self.logger.info(f"[SQL_AGENT] Attempting fallback after error")
                return self._execute_fallback(plan, schema_tools)
            except Exception as fallback_error:
                self.logger.error(f"[SQL_AGENT] Fallback also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": f"SQL Agent failed: {str(e)}, Fallback failed: {str(fallback_error)}"
                }
    
    def _execute_sql_with_retry(self, sql_query: str, original_query: str, max_retries: int = 2) -> dict:
        """Execute SQL with simple retry logic for common errors."""
        for attempt in range(max_retries + 1):
            self.logger.info(f"[SQL_AGENT] SQL execution attempt {attempt + 1}/{max_retries + 1}")
            
            result = self._execute_sql_direct(sql_query)
            
            if result is not None:
                return {'success': True, 'result': result}
            
            # If this was the last attempt, give up
            if attempt == max_retries:
                self.logger.error(f"[SQL_AGENT] All {max_retries + 1} attempts failed")
                return {'success': False, 'error': 'SQL execution failed after retries'}
            
            # Try to generate a simpler query for the next attempt
            self.logger.info(f"[SQL_AGENT] Attempting to generate simpler SQL for retry {attempt + 1}")
            simplified_prompt = f"""The previous complex SQL query failed. Generate a simpler SQL query for: {original_query}

Use only basic SELECT statements from the 'schema_info' table. Avoid:
- CTEs (WITH clauses)
- Complex JOINs
- Subqueries
- String aggregation

Simple query for: {original_query}
SQL:"""
            
            try:
                if self.llm and hasattr(self.llm, 'llm'):
                    response = self.llm.llm.invoke(simplified_prompt)
                    if hasattr(response, 'content'):
                        sql_query = response.content.strip()
                    else:
                        sql_query = str(response).strip()
                    
                    sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                    self.logger.info(f"[SQL_AGENT] Generated simpler SQL for retry: {sql_query}")
                else:
                    break
            except Exception as e:
                self.logger.error(f"[SQL_AGENT] Failed to generate retry SQL: {e}")
                break
        
        return {'success': False, 'error': 'SQL execution and retries failed'}

    def _execute_sql_direct(self, sql_query: str):
        """Execute SQL query directly using MetadataStore's DuckDB connection."""
        try:
            import duckdb
            
            self.logger.info(f"[SQL_AGENT] Executing SQL query: {sql_query}")
            self.logger.debug(f"[SQL_AGENT] Using database path: {self.metadata_store.db_path}")
            
            # Use MetadataStore's database path for direct connection
            with duckdb.connect(str(self.metadata_store.db_path)) as conn:
                self.logger.debug(f"[SQL_AGENT] Connected to DuckDB successfully")
                
                self.logger.debug(f"[SQL_AGENT] About to execute query...")
                result = conn.execute(sql_query).fetchall()
                self.logger.info(f"[SQL_AGENT] Query executed successfully, got {len(result)} rows")
                
                # Log sample of results if available
                if result:
                    self.logger.debug(f"[SQL_AGENT] First few results: {result[:3] if len(result) > 3 else result}")
                
                # Convert result to string format
                if not result:
                    self.logger.info(f"[SQL_AGENT] No results returned from query")
                    return "No results found"
                
                # Format as simple string representation
                formatted_rows = []
                for i, row in enumerate(result):
                    formatted_row = " | ".join(str(col) for col in row)
                    formatted_rows.append(formatted_row)
                    if i < 3:  # Log first few rows for debugging
                        self.logger.debug(f"[SQL_AGENT] Row {i}: {formatted_row}")
                
                final_result = "\n".join(formatted_rows)
                self.logger.info(f"[SQL_AGENT] Successfully formatted {len(formatted_rows)} result rows")
                
                return final_result
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"[SQL_AGENT] Direct SQL execution failed: {error_msg}")
            self.logger.error(f"[SQL_AGENT] Exception type: {type(e)}")
            self.logger.error(f"[SQL_AGENT] Failed query: {sql_query}")
            
            # Provide helpful error context with more detail
            if "Ambiguous reference" in error_msg:
                self.logger.error(f"[SQL_AGENT] AMBIGUOUS REFERENCE ERROR detected")
                self.logger.error(f"[SQL_AGENT] This means column names need table aliases (e.g., s1.column_name)")
                self.logger.info(f"[SQL_AGENT] Will try fallback due to ambiguous column references")
            elif "Binder Error" in error_msg:
                self.logger.error(f"[SQL_AGENT] BINDER ERROR detected")
                self.logger.error(f"[SQL_AGENT] This usually means column or table names don't exist")
                self.logger.info(f"[SQL_AGENT] Will try fallback due to binding issues")
            elif "no such table" in error_msg.lower():
                self.logger.error(f"[SQL_AGENT] TABLE NOT FOUND error")
                self.logger.error(f"[SQL_AGENT] The 'schema_info' table may not exist or database not initialized")
                self.logger.info(f"[SQL_AGENT] Will try fallback - database may not be initialized")
            elif "syntax" in error_msg.lower():
                self.logger.error(f"[SQL_AGENT] SYNTAX ERROR detected")
                self.logger.error(f"[SQL_AGENT] The generated SQL has syntax issues")
            else:
                self.logger.error(f"[SQL_AGENT] Unknown error type: {error_msg}")
            
            import traceback
            self.logger.error(f"[SQL_AGENT] Full traceback: {traceback.format_exc()}")
            
            return None
    
    def _generate_sql_query(self, natural_language_query: str) -> str:
        """Generate SQL query from natural language using LLM."""
        try:
            system_prompt = """You are a SQL expert. Convert natural language questions about a metadata database into SQL queries.

The database has a table called 'schema_info' with these columns:
- file_name: Name of the CSV file (e.g., 'customers.csv')  
- file_path: Full path to the file
- column_name: Name of a column in that file
- data_type: Data type of the column (TEXT, INTEGER, REAL, etc.)
- null_count: Number of null values in the column
- unique_count: Number of unique values in the column
- total_rows: Total number of rows in the file  
- file_size_mb: File size in megabytes
- last_scanned: When the file was last analyzed

IMPORTANT RULES:
1. Only return the SQL query, no explanations
2. Use only SELECT statements (read-only)
3. Always query the 'schema_info' table
4. Use table aliases when doing joins or subqueries (e.g., 's1', 's2')
5. Always qualify column names with table aliases when ambiguous
6. For type mismatches, use explicit table aliases
7. Use STRING_AGG or GROUP_CONCAT for concatenating values

Examples:
"list all files" → SELECT DISTINCT file_name, total_rows, file_size_mb FROM schema_info

"find type mismatches" → 
SELECT s1.column_name, s1.data_type, STRING_AGG(s1.file_name, ', ') as files 
FROM schema_info s1 
WHERE s1.column_name IN (
    SELECT s2.column_name 
    FROM schema_info s2 
    GROUP BY s2.column_name 
    HAVING COUNT(DISTINCT s2.data_type) > 1
) 
GROUP BY s1.column_name, s1.data_type

"common columns" → 
SELECT s.column_name, COUNT(DISTINCT s.file_name) as file_count 
FROM schema_info s 
GROUP BY s.column_name 
HAVING COUNT(DISTINCT s.file_name) > 1

Query: {query}
SQL:"""

            prompt = system_prompt.format(query=natural_language_query)
            
            self.logger.info(f"[SQL_AGENT] Generating SQL for query: '{natural_language_query}'")
            self.logger.debug(f"[SQL_AGENT] Full prompt sent to LLM:\n{prompt}")
            
            if self.llm and hasattr(self.llm, 'llm'):
                self.logger.debug(f"[SQL_AGENT] Calling LLM model: {getattr(self.llm, 'model_name', 'unknown')}")
                
                response = self.llm.llm.invoke(prompt)
                
                # Log the raw response from LLM
                self.logger.info(f"[SQL_AGENT] Raw LLM response type: {type(response)}")
                
                if hasattr(response, 'content'):
                    raw_content = response.content
                    self.logger.info(f"[SQL_AGENT] Raw LLM response content: '{raw_content}'")
                    sql_query = raw_content.strip()
                else:
                    raw_content = str(response)
                    self.logger.info(f"[SQL_AGENT] Raw LLM response (as string): '{raw_content}'")
                    sql_query = raw_content.strip()
                
                # Log the cleaning process
                self.logger.debug(f"[SQL_AGENT] Before cleaning: '{sql_query}'")
                
                # Clean up the SQL query
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                
                self.logger.debug(f"[SQL_AGENT] After cleaning: '{sql_query}'")
                
                # Basic validation - ensure it's a SELECT query (including CTEs that start with WITH)
                sql_upper = sql_query.strip().upper()
                if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
                    self.logger.warning(f"[SQL_AGENT] Generated query is not a SELECT statement: '{sql_query[:50]}...'")
                    self.logger.warning(f"[SQL_AGENT] Query starts with: '{sql_query[:20] if sql_query else 'EMPTY'}'")
                    return None
                
                self.logger.info(f"[SQL_AGENT] Final generated SQL: {sql_query}")
                return sql_query
            else:
                self.logger.error(f"[SQL_AGENT] LLM not available - llm: {self.llm}, has_llm_attr: {hasattr(self.llm, 'llm') if self.llm else False}")
                return None
            
        except Exception as e:
            self.logger.error(f"[SQL_AGENT] Error generating SQL query: {e}")
            self.logger.error(f"[SQL_AGENT] Exception type: {type(e)}")
            import traceback
            self.logger.error(f"[SQL_AGENT] Full traceback: {traceback.format_exc()}")
            return None
    
    def _format_sql_result(self, original_query: str, sql_query: str, result: str) -> str:
        """Format SQL result into a natural language response."""
        try:
            if not result or result.strip() == "[]":
                return f"No results found for your query: '{original_query}'"
            
            # Basic formatting
            formatted = f"Results for '{original_query}':\n\n"
            formatted += f"SQL Query: {sql_query}\n\n"
            formatted += f"Results:\n{result}"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting SQL result: {e}")
            return f"Query completed but formatting failed: {str(e)}"

    def _execute_fallback(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute using traditional schema_tools as fallback."""
        operation_type = plan.get("operation_type", "general_analysis")
        
        try:
            if operation_type == "file_discovery":
                result = schema_tools.list_all_files()
            elif operation_type == "schema_analysis":
                # Try to extract file name from query
                query = plan.get("query", "").lower()
                for word in ["customers", "orders", "reviews", "legacy"]:
                    if word in query:
                        filename = f"{word}.csv"
                        result = schema_tools.get_file_schema(filename)
                        break
                else:
                    result = schema_tools.list_all_files()
            elif operation_type == "data_quality":
                result = schema_tools.detect_type_mismatches()
            elif operation_type == "relationship_analysis":
                result = schema_tools.find_common_columns()
            elif operation_type == "database_overview":
                result = schema_tools.get_database_summary()
            else:
                result = schema_tools.list_all_files()
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback execution failed: {str(e)}"
            }
    
    def _fallback_parse(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Fallback parsing when SQL agent is not available."""
        operation_type = self._classify_query(query)
        
        return {
            "intent": f"Fallback analysis: {query}",
            "operation_type": operation_type,
            "query": query,
            "strategy": "sql_agent_fallback",
            "agent_mode": False
        }
    
    def synthesize_response(self, query: str, plan: Dict[str, Any], result: str) -> Dict[str, Any]:
        """Synthesize the final response using LLM or simple formatting.
        
        Args:
            query: Original user query
            plan: The execution plan
            result: Raw results from execution
            
        Returns:
            Dictionary with success status and formatted response
        """
        try:
            if plan.get("agent_mode") and self._sql_agent:
                # SQL agent already provides formatted response
                return {
                    "success": True,
                    "response": result
                }
            else:
                # Simple formatting for fallback mode
                operation_type = plan.get("operation_type", "analysis")
                response = f"Analysis Results ({operation_type}):\n\n{result}"
                
                return {
                    "success": True,
                    "response": response
                }
                
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return {
                "success": False,
                "error": f"Failed to synthesize response: {str(e)}"
            }
    
    def get_help_text(self) -> str:
        """Get help text for SQL agent strategy."""
        return """
TableTalk - SQL Agent Mode

This mode uses an intelligent SQL agent to analyze your data schema using natural language queries.
The agent writes and executes SQL queries against your metadata database to answer questions.

Example Queries:
  • "What files do we have and how big are they?"
  • "Show me the schema of customers.csv"
  • "Which files contain a user_id column?"
  • "Find columns with data type mismatches across files"
  • "What columns appear in multiple files?"
  • "Give me an overview of the entire database"
  • "How many unique columns do we have across all files?"
  • "Which files have the most null values?"

Advanced Queries:
  • "Find files where the same column has different data types"
  • "Show me files with more than 10 columns"
  • "Which columns have the highest percentage of null values?"
  • "Compare file sizes and row counts across all data"

The SQL agent can understand complex questions and break them down into appropriate SQL queries.
        """.strip()
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        agent_available = self._sql_agent is not None and self.metadata_store is not None
        return {
            "name": "SQL Agent Strategy",
            "type": "sql_agent",
            "llm_available": self.llm is not None,
            "agent_available": agent_available,
            "capabilities": [
                "natural_language_to_sql", 
                "direct_sql_execution", 
                "metadata_exploration",
                "automatic_query_generation"
            ] if agent_available else ["basic_fallback"],
            "reliability": "high" if agent_available else "medium",
            "performance": "excellent" if agent_available else "good"
        }
