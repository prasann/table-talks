"""Simple chat interface for TableTalk."""

import os
import sys
from pathlib import Path

# Ensure src is in Python path for consistent imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Always use absolute imports from src
from metadata.metadata_store import MetadataStore
from metadata.schema_extractor import SchemaExtractor

# Import schema agent
try:
    from agent.schema_agent import SchemaAgent
    SCHEMA_AGENT_AVAILABLE = True
except ImportError:
    SCHEMA_AGENT_AVAILABLE = False

# Import old components only if library agent is not available
OLD_AGENT_AVAILABLE = False
try:
    from tools.schema_tools import SchemaTools
    from agent.schema_agent import SchemaAgent
    OLD_AGENT_AVAILABLE = True
except ImportError:
    pass


class ChatInterface:
    """Simple command-line interface for TableTalk."""
    
    def __init__(self, config):
        """Initialize the chat interface."""
        self.config = config
        
        # Initialize components
        self.metadata_store = MetadataStore(config['database']['path'])
        self.schema_extractor = SchemaExtractor(
            max_file_size_mb=config['scanner']['max_file_size_mb'],
            sample_size=config['scanner']['sample_size']
        )
        
        # Only initialize schema_tools if old agent is available
        self.schema_tools = None
        if OLD_AGENT_AVAILABLE:
            self.schema_tools = SchemaTools(self.metadata_store)
        
        # Choose agent type based on configuration and availability
        use_modern_agent = config.get('agent', {}).get('use_modern_agent', True)
        
        # Force modern agent if old agent is not available
        if not OLD_AGENT_AVAILABLE:
            use_modern_agent = True
            
        agent_type = "Modern" if use_modern_agent and SCHEMA_AGENT_AVAILABLE else "Original"
        
        # Initialize Schema agent
        try:
            if use_modern_agent and SCHEMA_AGENT_AVAILABLE:
                print("🔬 Using modern schema agent (SQLAlchemy + Great Expectations)")
                self.agent = SchemaAgent(
                    database_path=config['database']['path'],
                    model_name=config['llm']['model'],
                    base_url=config['llm']['base_url']
                )
            elif OLD_AGENT_AVAILABLE and self.schema_tools:
                if use_modern_agent and not SCHEMA_AGENT_AVAILABLE:
                    print("⚠️ Modern schema agent not available, falling back to original agent")
                print("🔧 Using original agent (custom tools)")
                self.agent = SchemaAgent(
                    schema_tools=self.schema_tools,
                    model_name=config['llm']['model'],
                    base_url=config['llm']['base_url']
                )
            else:
                raise RuntimeError("No compatible agent available. Please install required dependencies.")
            
            # Get status to display the right message
            status = self.agent.get_status()
            agent_name = status.get('agent_type', 'Unknown')
            print(f"🤖 Agent: {agent_name}")
            
            if status.get('function_calling'):
                print("🚀 Advanced mode: Native function calling enabled!")
            elif status.get('llm_available'):
                print("🤖 Intelligent mode: LLM query parsing enabled!")
            else:
                print("📝 Basic mode: Pattern matching only")
                
        except Exception as e:
            print(f"⚠️  LLM agent not available: {e}")
            self.agent = None
        
        self.running = False

    def start(self):
        """Start the interactive CLI."""
        print("🗣️  TableTalk - Conversational data exploration")
        print("📁 Commands: /scan <dir>, /help, /status, /refresh, /exit")
        if self.agent and self.agent.check_llm_availability():
            print("✨ Intelligent mode: Ask complex questions and get smart insights!")
        else:
            print("📊 Basic mode: Ask simple questions about your data")
        print()
        
        self.running = True
        while self.running:
            try:
                user_input = input("TableTalk> ").strip()
                if not user_input:
                    continue
                    
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    self._handle_query(user_input)
                    
            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
            except EOFError:
                print("\\nGoodbye!")
                break

    def _handle_command(self, command):
        """Handle CLI commands."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd in ['/exit', '/quit']:
            print("Goodbye!")
            self.running = False
        elif cmd == '/help':
            self._show_help()
        elif cmd == '/status':
            self._show_status()
        elif cmd == '/refresh':
            self._refresh_agent()
        elif cmd == '/scan':
            if len(parts) < 2:
                print("Usage: /scan <directory>")
                return
            self._scan_directory(parts[1])
        elif cmd == '/strategy':
            # Remove strategy switching - SchemaAgent auto-detects
            self._show_agent_info()
        elif cmd == '/refresh':
            self._refresh_agent()
        else:
            print(f"Unknown command: {cmd}")
            print("Use /help for available commands")

    def _handle_query(self, query):
        """Handle natural language queries."""
        if not self.agent:
            print("Agent not available. Please try /scan to analyze files first.")
            return
        
        try:
            response = self.agent.query(query)
            print(response)
        except Exception as e:
            print(f"Error processing query: {e}")

    def _scan_directory(self, directory):
        """Scan directory for files and load data into DuckDB."""
        directory_path = Path(directory).resolve()
        
        if not directory_path.exists():
            print(f"Directory not found: {directory}")
            return
        
        print(f"Scanning: {directory_path}")
        
        file_count = 0
        data_loaded_count = 0
        
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.parquet']:
                try:
                    # 1. Extract schema metadata (existing functionality)
                    schema_info = self.schema_extractor.extract_from_file(str(file_path))
                    if schema_info:
                        self.metadata_store.store_schema_info(schema_info)
                        print(f"✓ Schema: {file_path.name}: {len(schema_info)} columns")
                        file_count += 1
                    
                    # 2. Load actual data into DuckDB tables (NEW!)
                    table_name = file_path.stem.lower()  # Use filename as table name
                    
                    # Connect to the same DuckDB database
                    import duckdb
                    with duckdb.connect(self.metadata_store.db_path) as conn:
                        if file_path.suffix.lower() == '.csv':
                            # Load CSV file
                            conn.execute(f"""
                                CREATE OR REPLACE TABLE {table_name} AS 
                                SELECT * FROM read_csv_auto('{file_path}')
                            """)
                        elif file_path.suffix.lower() == '.parquet':
                            # Load Parquet file
                            conn.execute(f"""
                                CREATE OR REPLACE TABLE {table_name} AS 
                                SELECT * FROM read_parquet('{file_path}')
                            """)
                        
                        # Get row count
                        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        print(f"✓ Data: {table_name}: {row_count:,} rows loaded")
                        data_loaded_count += 1
                    
                except Exception as e:
                    print(f"✗ {file_path.name}: {e}")
        
        print(f"Scan complete: {file_count} schemas extracted, {data_loaded_count} data tables loaded")
        
        # Refresh the agent's analyzer to pick up new tables
        if self.agent and hasattr(self.agent, 'analyzer') and hasattr(self.agent.analyzer, 'refresh'):
            print("🔄 Refreshing analyzer to detect new tables...")
            self.agent.analyzer.refresh()
        
        # Show available tables
        if data_loaded_count > 0:
            print("\n📋 Available data tables:")
            import duckdb
            with duckdb.connect(self.metadata_store.db_path) as conn:
                tables = conn.execute("SHOW TABLES").fetchall()
                for table in tables:
                    table_name = table[0]
                    if table_name != 'schema_info':  # Skip metadata table
                        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        col_count = len(conn.execute(f"DESCRIBE {table_name}").fetchall())
                        print(f"  - {table_name}: {row_count:,} rows, {col_count} columns")

    def _show_status(self):
        """Show current status."""
        if self.agent:
            status = self.agent.get_status()
            print("📊 System Status:")
            print(f"   Agent: {status.get('agent_type', 'Unknown')} ({status.get('mode', 'Unknown')})")
            print(f"   LLM Available: {'✅' if status['llm_available'] else '❌'}")
            print(f"   Function Calling: {'✅' if status.get('function_calling') else '❌'}")
            if status['llm_available'] or status.get('function_calling'):
                print(f"   Model: {status['model_name']}")
                print(f"   URL: {status['base_url']}")
        
        files = self.metadata_store.list_all_files()
        print(f"   Files Scanned: {len(files)}")
    
    def _show_agent_info(self):
        """Show current agent information."""
        if not self.agent:
            print("Agent not available")
            return
            
        status = self.agent.get_status()
        print("🤖 SchemaAgent Status:")
        print(f"   Mode: {status.get('mode', 'Unknown')}")
        print(f"   Model: {status['model_name']}")
        print(f"   LLM Available: {'✅' if status['llm_available'] else '❌'}")
        print(f"   Function Calling: {'✅' if status.get('function_calling') else '❌'}")
    
    def _refresh_agent(self):
        """Refresh the agent to detect new tables."""
        if self.agent and hasattr(self.agent, 'analyzer') and hasattr(self.agent.analyzer, 'refresh'):
            print("🔄 Refreshing agent analyzer...")
            self.agent.analyzer.refresh()
            
            # Test if refresh worked
            if hasattr(self.agent.analyzer, 'list_files'):
                result = self.agent.analyzer.list_files()
                if "Available Tables" in result:
                    print("✅ Agent refreshed successfully")
                    # Show a preview of available tables
                    lines = result.split('\n')[:10]  # First 10 lines
                    for line in lines:
                        if line.strip():
                            print(f"   {line}")
                else:
                    print("⚠️ Agent refresh may not have worked properly")
            else:
                print("✅ Agent refreshed")
        else:
            print("❌ Agent refresh not supported")
    
    def _show_strategies(self):
        """Show available strategies (deprecated - keeping for compatibility)."""
        self._show_agent_info()
    
    def _switch_strategy(self, strategy_type):
        """Switch strategy (deprecated - SchemaAgent auto-detects)."""
        print("⚠️  Strategy switching is no longer needed - SchemaAgent auto-detects capabilities!")
        self._show_agent_info()

    def _show_help(self):
        """Show help message."""
        print("""
TableTalk Commands:
  /scan <directory>  - Scan files for schema information
  /status            - Show system status
  /refresh           - Refresh agent to detect new tables
  /strategy          - Show agent information
  /help              - Show this help
  /exit              - Exit TableTalk

Start by scanning a directory: /scan data/

Query Examples:
  "Show me the customers table"
  "What columns are in orders?"
  "How many rows are in each file?"
  "Show me tables with email addresses"
        """.strip())
