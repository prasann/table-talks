"""LangGraph-based SQL Agent for advanced query processing and result formatting."""

import logging
from typing import Dict, List, Optional, Any, TypedDict, Annotated
import json
import operator
from dataclasses import dataclass

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.tools import tool
except ImportError:
    print("LangGraph dependencies not installed. Run: pip install langgraph")
    raise

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


class AgentState(TypedDict):
    """State for the SQL Agent."""
    messages: Annotated[List[Any], operator.add]
    original_query: str
    current_sql: Optional[str]
    sql_results: Optional[Any]
    formatted_results: Optional[str]
    error_count: int
    next_action: str


@dataclass
class SQLTool:
    """Tool for executing SQL queries."""
    metadata_store: MetadataStore
    logger: logging.Logger
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query and return structured results."""
        try:
            import duckdb
            
            self.logger.info(f"[SQL_TOOL] Executing full query: {sql_query}")
            
            with duckdb.connect(str(self.metadata_store.db_path)) as conn:
                result = conn.execute(sql_query).fetchall()
                columns = [desc[0] for desc in conn.description] if conn.description else []
                
                self.logger.info(f"[SQL_TOOL] Query returned {len(result)} rows")
                
                return {
                    'success': True,
                    'data': result,
                    'columns': columns,
                    'row_count': len(result)
                }
                
        except Exception as e:
            self.logger.error(f"[SQL_TOOL] Execution failed: {e}")
            self.logger.error(f"[SQL_TOOL] Failed query was: {sql_query}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the schema_info table structure."""
        try:
            schema_query = """
            SELECT column_name, data_type, COUNT(*) as sample_count
            FROM schema_info 
            GROUP BY column_name, data_type 
            ORDER BY column_name
            """
            return self.execute_sql(schema_query)
        except Exception as e:
            return {'success': False, 'error': str(e)}


class SQLAgentLangGraph(QueryProcessingStrategy):
    """LangGraph-based SQL Agent for advanced query processing."""
    
    def __init__(self, llm_agent=None, metadata_store: MetadataStore = None, db_path: str = "./database/metadata.duckdb"):
        """Initialize the LangGraph SQL agent."""
        self.llm = llm_agent
        self.logger = get_logger("tabletalk.sql_agent_langgraph")
        self.metadata_store = metadata_store or MetadataStore(db_path)
        self.db_path = db_path
        
        # Debug LLM availability
        self.logger.info(f"[SQL_AGENT_LG] Initializing with LLM: {llm_agent is not None}")
        self.logger.debug(f"[SQL_AGENT_LG] LLM type: {type(llm_agent)}")
        if llm_agent:
            self.logger.debug(f"[SQL_AGENT_LG] LLM has 'llm' attr: {hasattr(llm_agent, 'llm')}")
            if hasattr(llm_agent, 'model_name'):
                self.logger.debug(f"[SQL_AGENT_LG] LLM model: {llm_agent.model_name}")
        
        # Initialize SQL tool
        self.sql_tool = SQLTool(self.metadata_store, self.logger)
        
        # Initialize the agent graph
        self.graph = None
        self._initialize_agent()
        
        self.logger.info("[SQL_AGENT_LG] LangGraph SQL Agent initialized")
    
    def _initialize_agent(self):
        """Initialize the LangGraph agent workflow."""
        try:
            # Create the state graph
            workflow = StateGraph(AgentState)
            
            # Add nodes
            workflow.add_node("analyze_query", self._analyze_query)
            workflow.add_node("generate_sql", self._generate_sql)
            workflow.add_node("execute_sql", self._execute_sql)
            workflow.add_node("format_results", self._format_results)
            workflow.add_node("handle_error", self._handle_error)
            
            # Set entry point
            workflow.set_entry_point("analyze_query")
            
            # Add edges
            workflow.add_conditional_edges(
                "analyze_query",
                self._should_generate_sql,
                {
                    "generate_sql": "generate_sql",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "generate_sql",
                self._should_execute_sql,
                {
                    "execute_sql": "execute_sql",
                    "handle_error": "handle_error"
                }
            )
            
            workflow.add_conditional_edges(
                "execute_sql",
                self._should_format_results,
                {
                    "format_results": "format_results",
                    "handle_error": "handle_error"
                }
            )
            
            workflow.add_edge("format_results", END)
            workflow.add_conditional_edges(
                "handle_error",
                self._should_retry,
                {
                    "generate_sql": "generate_sql",
                    "end": END
                }
            )
            
            # Compile the graph without checkpointer for now
            self.graph = workflow.compile()
            
            self.logger.info("[SQL_AGENT_LG] Agent workflow compiled successfully")
            
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Failed to initialize agent: {e}")
            self.graph = None
    
    def _analyze_query(self, state: AgentState) -> AgentState:
        """Analyze the user query to understand intent."""
        try:
            self.logger.info(f"[SQL_AGENT_LG] Analyzing query: {state['original_query']}")
            
            analysis_prompt = f"""
            Analyze this user query about database schema metadata: "{state['original_query']}"
            
            Available data: The 'schema_info' table contains:
            - file_name, file_path: File information
            - column_name, data_type: Column details
            - null_count, unique_count, total_rows: Statistics
            - file_size_mb, last_scanned: Metadata
            
            Determine:
            1. What type of analysis is needed
            2. What information should be included in results
            3. How results should be formatted for best user experience
            
            Query type and approach:
            """
            
            if self.llm and hasattr(self.llm, 'llm'):
                response = self.llm.llm.invoke(analysis_prompt)
                analysis = response.content if hasattr(response, 'content') else str(response)
                
                state["messages"].append(AIMessage(content=f"Analysis: {analysis}"))
                state["next_action"] = "generate_sql"
                
                self.logger.info(f"[SQL_AGENT_LG] Query analysis complete")
            else:
                self.logger.warning(f"[SQL_AGENT_LG] LLM not available for analysis")
                state["next_action"] = "generate_sql"  # Still proceed
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Analysis failed: {e}")
            state["next_action"] = "generate_sql"  # Proceed anyway
        
        return state
    
    def _generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL query based on analysis."""
        try:
            self.logger.info(f"[SQL_AGENT_LG] Generating SQL for: {state['original_query']}")
            
            sql_prompt = f"""
            Generate ONLY a SQL query for: "{state['original_query']}"
            
            Database schema:
            Table: schema_info
            Columns: file_name, file_path, column_name, data_type, null_count, unique_count, total_rows, file_size_mb, last_scanned
            
            CRITICAL REQUIREMENTS:
            1. Return ONLY the SQL query - no explanations, no notes, no comments
            2. Use SELECT statements only
            3. For file queries, use file_name LIKE '%filename%' (e.g., LIKE '%customers%' for customer files)
            4. Use proper SQL syntax - no markdown formatting
            5. End the query with semicolon
            
            Example queries:
            - For customer data types: SELECT DISTINCT column_name, data_type FROM schema_info WHERE file_name LIKE '%customers%';
            - For customer schema: SELECT column_name, data_type FROM schema_info WHERE file_name LIKE '%customers%' ORDER BY column_name;
            - For all files: SELECT DISTINCT file_name FROM schema_info;
            
            Query: {state['original_query']}
            
            SQL:"""
            
            if self.llm and hasattr(self.llm, 'llm'):
                response = self.llm.llm.invoke(sql_prompt)
                sql_query = response.content if hasattr(response, 'content') else str(response)
                
                # Aggressive cleaning of the SQL
                sql_query = sql_query.strip()
                
                # Remove any markdown or code block formatting
                sql_query = sql_query.replace('```sql', '').replace('```', '')
                
                # Remove any lines that start with explanatory text
                lines = sql_query.split('\n')
                sql_lines = []
                for line in lines:
                    line = line.strip()
                    if line and not any(line.lower().startswith(word) for word in 
                                      ['note:', 'explanation:', 'this query', 'the above', 'here', 'result:']):
                        sql_lines.append(line)
                
                sql_query = ' '.join(sql_lines).strip()
                
                # Ensure it ends with semicolon
                if not sql_query.endswith(';'):
                    sql_query += ';'
                
                self.logger.info(f"[SQL_AGENT_LG] Cleaned SQL: {sql_query}")
                
                state["current_sql"] = sql_query
                state["messages"].append(AIMessage(content=f"Generated SQL: {sql_query}"))
                state["next_action"] = "execute_sql"
                
                self.logger.info(f"[SQL_AGENT_LG] SQL generated: {sql_query[:100]}...")
            else:
                self.logger.error(f"[SQL_AGENT_LG] LLM not available for SQL generation")
                state["next_action"] = "handle_error"
                state["error_count"] += 1
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] SQL generation failed: {e}")
            state["next_action"] = "handle_error"
            state["error_count"] += 1
        
        return state
    
    def _execute_sql(self, state: AgentState) -> AgentState:
        """Execute the generated SQL query."""
        messages = state["messages"]
        sql_query = state.get("current_sql", "")
        
        self.logger.info(f"[LANGGRAPH] Executing SQL query: '{sql_query}'")
        self.logger.info(f"[LANGGRAPH] State keys: {list(state.keys())}")
        
        if not sql_query:
            error_msg = "No SQL query to execute"
            self.logger.error(f"[LANGGRAPH] {error_msg}")
            messages.append(AIMessage(content=error_msg))
            return {
                "messages": messages,
                "current_sql": sql_query,
                "sql_results": None,
                "error_count": state.get("error_count", 0) + 1
            }
        
        # Validate and clean SQL before execution
        cleaned_sql = self._validate_and_clean_sql(sql_query)
        if not cleaned_sql:
            error_msg = "Generated SQL query appears to be invalid or empty after cleaning"
            self.logger.error(f"[LANGGRAPH] {error_msg}")
            messages.append(AIMessage(content=error_msg))
            return {
                "messages": messages,
                "sql_query": sql_query,
                "sql_result": None,
                "error_count": state.get("error_count", 0) + 1
            }
        
        # Execute the cleaned SQL
        result = self.sql_tool.execute_sql(cleaned_sql)
        
        if result['success']:
            self.logger.info(f"[LANGGRAPH] SQL execution successful: {result['row_count']} rows returned")
            return {
                "messages": messages,
                "current_sql": cleaned_sql,
                "sql_results": result,
                "error_count": state.get("error_count", 0),
                "next_action": "format_results"
            }
        else:
            error_msg = f"SQL execution failed: {result['error']}"
            self.logger.error(f"[LANGGRAPH] {error_msg}")
            messages.append(AIMessage(content=error_msg))
            return {
                "messages": messages,
                "current_sql": cleaned_sql,
                "sql_results": result,
                "error_count": state.get("error_count", 0) + 1,
                "next_action": "handle_error"
            }
    
    def _validate_and_clean_sql(self, sql_query: str) -> str:
        """Validate and clean SQL query before execution."""
        if not sql_query or not sql_query.strip():
            return ""
        
        # Remove common problematic prefixes/suffixes
        lines = sql_query.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip lines that are clearly comments or explanations
            if any(line.lower().startswith(prefix) for prefix in [
                'note:', 'explanation:', 'this query', 'the sql', 'here is', 'here\'s',
                'based on', 'according to', 'as requested', '<!--', '--'
            ]):
                continue
                
            # Skip lines that are markdown
            if line.startswith('```') or line.startswith('`'):
                continue
                
            cleaned_lines.append(line)
        
        cleaned_sql = '\n'.join(cleaned_lines).strip()
        
        # Basic SQL validation - should start with valid SQL keywords
        if cleaned_sql and not any(cleaned_sql.upper().startswith(keyword) for keyword in [
            'SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP'
        ]):
            self.logger.warning(f"[SQL_VALIDATION] SQL doesn't start with valid keyword: {cleaned_sql[:50]}...")
            return ""
        
        # Remove trailing semicolon if present (DuckDB doesn't need it)
        if cleaned_sql.endswith(';'):
            cleaned_sql = cleaned_sql[:-1].strip()
        
        self.logger.info(f"[SQL_VALIDATION] Cleaned SQL: {cleaned_sql}")
        return cleaned_sql
    
    def _format_results(self, state: AgentState) -> AgentState:
        """Format the SQL results for user-friendly display."""
        self.logger.info(f"[SQL_AGENT_LG] Formatting results")
        
        results = state.get("sql_results")
        if not results or not results['success']:
            state["next_action"] = "end"
            return state
        
        formatting_prompt = f"""
        Format these SQL query results for the user query: "{state['original_query']}"
        
        Data: {results['data'][:5]}... (showing first 5 rows)
        Columns: {results['columns']}
        Total rows: {results['row_count']}
        
        Create a clear, well-structured response that:
        1. Explains what the data shows
        2. Highlights key insights
        3. Uses tables, lists, or structured format
        4. Is easy to read and understand
        5. Answers the user's specific question
        
        For schema comparisons, organize by:
        - File names (use basename, not full path)
        - Column structures
        - Data type differences
        - Key insights about compatibility
        
        Formatted response:
        """
        
        try:
            if self.llm and hasattr(self.llm, 'llm'):
                response = self.llm.llm.invoke(formatting_prompt)
                formatted_result = response.content if hasattr(response, 'content') else str(response)
                
                state["formatted_results"] = formatted_result
                state["messages"].append(AIMessage(content=f"Results formatted"))
                
                self.logger.info(f"[SQL_AGENT_LG] Results formatting complete")
            else:
                # Fallback formatting
                state["formatted_results"] = self._basic_format_results(results, state['original_query'])
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Formatting failed: {e}")
            state["formatted_results"] = self._basic_format_results(results, state['original_query'])
        
        state["next_action"] = "end"
        return state
    
    def _basic_format_results(self, results: Dict[str, Any], query: str) -> str:
        """Basic fallback formatting for results."""
        if not results['data']:
            return f"No results found for query: {query}"
        
        formatted = f"Results for '{query}':\n\n"
        
        # Create a simple table
        if results['columns']:
            # Header
            formatted += " | ".join(results['columns']) + "\n"
            formatted += "-" * (len(" | ".join(results['columns']))) + "\n"
            
            # Data rows
            for row in results['data'][:10]:  # Limit to first 10 rows
                formatted += " | ".join(str(cell) for cell in row) + "\n"
            
            if len(results['data']) > 10:
                formatted += f"\n... and {len(results['data']) - 10} more rows\n"
        
        return formatted
    
    def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors and decide on retry strategy."""
        self.logger.info(f"[SQL_AGENT_LG] Handling error, attempt {state['error_count']}")
        
        if state['error_count'] >= 3:
            state["next_action"] = "end"
            state["formatted_results"] = f"Unable to process query after multiple attempts: {state['original_query']}"
        else:
            state["next_action"] = "generate_sql"
            # Reset current SQL to force regeneration
            state["current_sql"] = None
        
        return state
    
    def _should_generate_sql(self, state: AgentState) -> str:
        """Decide if we should generate SQL."""
        return state.get("next_action", "end")
    
    def _should_execute_sql(self, state: AgentState) -> str:
        """Decide if we should execute SQL."""
        return state.get("next_action", "end")
    
    def _should_format_results(self, state: AgentState) -> str:
        """Decide if we should format results."""
        return state.get("next_action", "end")
    
    def _should_retry(self, state: AgentState) -> str:
        """Decide if we should retry or end."""
        return state.get("next_action", "end")
    
    def parse_query(self, query: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Parse query using the LangGraph agent."""
        try:
            if not self.graph:
                return {
                    "success": False,
                    "error": "LangGraph agent not initialized"
                }
            
            return {
                "success": True,
                "parsed_query": {
                    "intent": f"LangGraph SQL Agent query: {query}",
                    "operation_type": "advanced_sql_analysis",
                    "query": query,
                    "strategy": "sql_agent_langgraph",
                    "agent_mode": True
                }
            }
            
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Error parsing query: {e}")
            return {
                "success": False,
                "error": f"Failed to parse query: {str(e)}"
            }
    
    def execute_plan(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute the query plan using LangGraph agent."""
        try:
            if not self.graph:
                self.logger.warning("[SQL_AGENT_LG] Graph not available, using fallback")
                return self._execute_fallback(plan, schema_tools)
            
            query = plan.get("query", "")
            self.logger.info(f"[SQL_AGENT_LG] Executing plan for: {query}")
            
            # Initial state
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "original_query": query,
                "current_sql": None,
                "sql_results": None,
                "formatted_results": None,
                "error_count": 0,
                "next_action": "analyze_query"
            }
            
            # Run the agent
            final_state = self.graph.invoke(initial_state)
            
            result = final_state.get("formatted_results", "No results generated")
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Error executing plan: {e}")
            # Fallback to schema_tools
            try:
                return self._execute_fallback(plan, schema_tools)
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": f"LangGraph agent failed: {str(e)}, Fallback failed: {str(fallback_error)}"
                }
    
    def _execute_fallback(self, plan: Dict[str, Any], schema_tools) -> Dict[str, Any]:
        """Execute using traditional schema_tools as fallback."""
        self.logger.info("[SQL_AGENT_LG] Using fallback execution")
        
        try:
            query = plan.get("query", "").lower()
            
            if any(word in query for word in ["files", "list", "show"]):
                result = schema_tools.list_all_files()
            elif any(word in query for word in ["schema", "compare", "structure"]):
                result = schema_tools.detect_type_mismatches()
            elif any(word in query for word in ["common", "shared"]):
                result = schema_tools.find_common_columns()
            else:
                result = schema_tools.get_database_summary()
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Fallback execution failed: {str(e)}"
            }
    
    def synthesize_response(self, query: str, plan: Dict[str, Any], result: str) -> Dict[str, Any]:
        """Synthesize the final response."""
        try:
            # LangGraph agent already provides formatted response
            return {
                "success": True,
                "response": result
            }
                
        except Exception as e:
            self.logger.error(f"[SQL_AGENT_LG] Error synthesizing response: {e}")
            return {
                "success": False,
                "error": f"Failed to synthesize response: {str(e)}"
            }
    
    def get_help_text(self) -> str:
        """Get help text for LangGraph SQL agent strategy."""
        return """
TableTalk - LangGraph SQL Agent Mode

This mode uses an advanced LangGraph-based agent for intelligent SQL query processing and result formatting.
The agent can analyze complex queries, generate optimized SQL, and format results in user-friendly ways.

Example Queries:
  • "Compare schemas across all files"
  • "Find data type inconsistencies between files"
  • "Show me which files have similar column structures"
  • "What's the relationship between customer files?"
  • "Analyze data quality issues across the database"

Advanced Features:
  • Multi-step reasoning and query planning
  • Automatic error recovery and retry logic
  • Intelligent result formatting
  • Context-aware SQL generation
  • Structured output with insights

The agent can understand complex analytical requests and break them down into logical steps.
        """.strip()
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        agent_available = self.graph is not None and self.metadata_store is not None
        return {
            "name": "LangGraph SQL Agent Strategy",
            "type": "sql_agent_langgraph",
            "llm_available": self.llm is not None,
            "agent_available": agent_available,
            "capabilities": [
                "advanced_sql_generation",
                "multi_step_reasoning", 
                "intelligent_formatting",
                "error_recovery",
                "context_aware_analysis"
            ] if agent_available else ["basic_fallback"],
            "reliability": "excellent" if agent_available else "medium",
            "performance": "intelligent" if agent_available else "good"
        }
