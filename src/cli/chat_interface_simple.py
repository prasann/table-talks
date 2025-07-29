"""Simple chat interface for TableTalk."""

import os
import sys
from pathlib import Path

from metadata.metadata_store import MetadataStore
from metadata.schema_extractor import SchemaExtractor
from tools.schema_tools import SchemaTools
from agent.llm_agent import LLMAgent


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
        self.schema_tools = SchemaTools(self.metadata_store)
        
        # Initialize LLM agent
        try:
            self.agent = LLMAgent(
                model_name=config['llm']['model'],
                base_url=config['llm']['base_url'],
                temperature=config['llm']['temperature'],
                max_tokens=config['llm']['max_tokens'],
                schema_tools=self.schema_tools
            )
        except Exception as e:
            print(f"LLM agent not available: {e}")
            self.agent = None
        
        self.running = False

    def start(self):
        """Start the interactive CLI."""
        print("TableTalk - Chat with your data schemas")
        print("Commands: /scan <dir>, /help, /exit")
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
        elif cmd == '/scan':
            if len(parts) < 2:
                print("Usage: /scan <directory>")
                return
            self._scan_directory(parts[1])
        else:
            print(f"Unknown command: {cmd}")
            print("Use /help for available commands")

    def _handle_query(self, query):
        """Handle natural language queries."""
        if not self.agent:
            print("LLM agent not available. Use /scan commands.")
            return
        
        # Try direct pattern matching first
        direct = self._try_direct(query)
        if direct:
            print(direct)
            return
            
        try:
            response = self.agent.query(query)
            print(response)
        except Exception as e:
            print(f"Error: {e}")

    def _try_direct(self, query):
        """Try direct response for common queries."""
        q = query.lower()
        
        # Schema queries
        if "schema" in q or "structure" in q:
            files = self.metadata_store.list_all_files()
            for file_info in files:
                if file_info['file_name'].lower() in q:
                    return self.schema_tools.get_file_schema(file_info['file_name'])
        
        # File listing
        if "files" in q and ("what" in q or "list" in q):
            return self.schema_tools.list_all_files()
        
        # Common columns
        if "common" in q and "column" in q:
            return self.schema_tools.find_common_columns()
        
        # Type mismatches
        if "mismatch" in q or "inconsisten" in q:
            return self.schema_tools.detect_type_mismatches()
        
        return None

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
                        print(f"✓ {file_path.name}: {len(schema_info['columns'])} columns")
                        file_count += 1
                except Exception as e:
                    print(f"✗ {file_path.name}: {e}")
        
        print(f"Scan complete: {file_count} files processed")

    def _show_help(self):
        """Show help message."""
        print("Commands:")
        print("  /scan <directory>  - Scan files for schema information")
        print("  /help             - Show this help")
        print("  /exit             - Exit TableTalk")
        print()
        print("Natural language queries:")
        print("  'What files do we have?'")
        print("  'Show schema of orders.csv'")
        print("  'Find common columns'")
