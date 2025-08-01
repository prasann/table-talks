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
from agent.schema_agent import SchemaAgent


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
        
        # Initialize Schema agent (simplified - function calling only)
        try:
            self.agent = SchemaAgent(
                metadata_store=self.metadata_store,
                model_name=config['llm']['model'],
                base_url=config['llm']['base_url']
            )
            
            # Get status to display the right message
            status = self.agent.get_status()
            if status.get('function_calling'):
                print(f"🚀 Function calling mode enabled with {status['tools_available']} tools!")
                print(f"📊 Available tools: {', '.join(status['tool_names'][:4])}...")
            else:
                print("❌ Function calling not supported - please use phi4-mini-fc model")
                
        except Exception as e:
            print(f"⚠️  LLM agent not available: {e}")
            self.agent = None
        
        self.running = False

    def start(self):
        """Start the interactive CLI."""
        print("🗣️  TableTalk - Conversational data exploration")
        print("📁 Commands: /scan <dir>, /help, /status, /exit")
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
        elif cmd == '/scan':
            if len(parts) < 2:
                print("Usage: /scan <directory>")
                return
            self._scan_directory(parts[1])
        elif cmd == '/strategy':
            # Remove strategy switching - SchemaAgent auto-detects
            self._show_agent_info()
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
        """Scan directory for files."""
        directory_path = Path(directory).resolve()
        
        if not directory_path.exists():
            print(f"Directory not found: {directory}")
            return
        
        print(f"Scanning: {directory_path}")
        
        file_count = 0
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.parquet']:
                try:
                    schema_info = self.schema_extractor.extract_from_file(str(file_path))
                    if schema_info:
                        self.metadata_store.store_schema_info(schema_info)
                        print(f"✓ {file_path.name}: {len(schema_info)} columns")
                        file_count += 1
                except Exception as e:
                    print(f"✗ {file_path.name}: {e}")
        
        print(f"Scan complete: {file_count} files processed")

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
        print(f"   Capabilities: {', '.join(status.get('capabilities', []))}")
    
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
