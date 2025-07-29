"""Command-line chat interface for TableTalk."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from metadata.metadata_store import MetadataStore
from metadata.schema_extractor import SchemaExtractor
from tools.schema_tools import SchemaTools
from agent.llm_agent import LLMAgent


class ChatInterface:
    """Interactive command-line interface for TableTalk."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the chat interface.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
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
            self.logger.error(f"Failed to initialize LLM agent: {str(e)}")
            self.agent = None
        
        # CLI settings
        self.prompt = config['cli']['prompt']
        self.running = False
    
    def start(self) -> None:
        """Start the interactive chat interface."""
        self.running = True
        
        # Welcome message
        self._print_welcome()
        
        # Check if agent is available
        if not self.agent:
            print("⚠️  LLM agent not available. You can still use /scan commands.")
            print("Make sure Ollama is running: ollama serve")
            print()
        
        # Main chat loop
        while self.running:
            try:
                user_input = input(self.prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    # Handle natural language query
                    self._handle_query(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                self.logger.error(f"Error in chat loop: {str(e)}")
                print(f"❌ An error occurred: {str(e)}")
    
    def _print_welcome(self) -> None:
        """Print welcome message and instructions."""
        print("🗣️  Welcome to TableTalk!")
        print("A conversational assistant for exploring data schemas.\n")
        
        # Show database status
        stats = self.metadata_store.get_database_stats()
        if stats['total_files'] > 0:
            print(f"📊 Database: {stats['total_files']} files, {stats['total_columns']} columns")
        else:
            print("📊 Database: Empty (use /scan to add files)")
        
        print("\nCommands:")
        print("  /scan <directory>  - Scan files for schema information")
        print("  /help             - Show help message")
        print("  /exit or /quit    - Exit TableTalk")
        print("\nOr ask questions in natural language!")
        print("Example: 'Show me the schema of orders.csv'\n")
    
    def _handle_command(self, command: str) -> None:
        """Handle slash commands.
        
        Args:
            command: Command string starting with /
        """
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd in ['/exit', '/quit']:
            self.running = False
            print("👋 Goodbye!")
            
        elif cmd == '/help':
            self._show_help()
            
        elif cmd == '/scan':
            if len(parts) < 2:
                print("❌ Usage: /scan <directory>")
                return
            
            directory = parts[1]
            self._scan_directory(directory)
            
        elif cmd == '/clear':
            if self.agent:
                self.agent.clear_memory()
                print("🧹 Conversation memory cleared")
            else:
                print("❌ Agent not available")
                
        elif cmd == '/status':
            self._show_status()
            
        else:
            print(f"❌ Unknown command: {cmd}")
            print("Use /help to see available commands")
    
    def _handle_query(self, query: str) -> None:
        """Handle natural language queries.
        
        Args:
            query: User's natural language query
        """
        if not self.agent:
            print("❌ LLM agent not available. Make sure Ollama is running.")
            print("You can still use /scan commands to explore files.")
            return
        
        print("🤔 Processing...")
        try:
            response = self.agent.query(query)
            print(f"🤖 {response}")
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
            
            # Try to provide a direct tool response as fallback
            try:
                if "schema" in query.lower() and any(word in query.lower() for word in ["orders.csv", "customers.csv", "reviews.csv"]):
                    # Extract file name and try direct tool call
                    for filename in ["orders.csv", "customers.csv", "reviews.csv"]:
                        if filename in query.lower():
                            direct_response = self.schema_tools.get_file_schema(filename)
                            print(f"🔧 Direct tool response:\n{direct_response}")
                            return
                elif "files" in query.lower():
                    direct_response = self.schema_tools.list_all_files()
                    print(f"🔧 Direct tool response:\n{direct_response}")
                    return
            except Exception as fallback_e:
                print(f"⚠️  Fallback also failed: {str(fallback_e)}")
                
            print("💡 Try using specific commands like /status or rephrase your question.")
    
    def _scan_directory(self, directory_path: str) -> None:
        """Scan a directory for files and extract schemas.
        
        Args:
            directory_path: Path to directory to scan
        """
        try:
            directory = Path(directory_path)
            
            if not directory.exists():
                print(f"❌ Directory not found: {directory_path}")
                return
            
            if not directory.is_dir():
                print(f"❌ Path is not a directory: {directory_path}")
                return
            
            print(f"🔍 Scanning directory: {directory_path}")
            
            # Extract schemas from all files
            results = self.schema_extractor.extract_from_directory(str(directory))
            
            if not results:
                print("❌ No supported files found in directory")
                print("Supported formats: CSV, Parquet")
                return
            
            # Store results in database
            total_columns = 0
            for file_name, schema_data in results.items():
                self.metadata_store.store_schema_info(schema_data)
                total_columns += len(schema_data)
                print(f"  ✓ {file_name}: {len(schema_data)} columns")
            
            print(f"\n✅ Scan complete: {len(results)} files, {total_columns} columns processed")
            
        except Exception as e:
            self.logger.error(f"Error scanning directory: {str(e)}")
            print(f"❌ Error scanning directory: {str(e)}")
    
    def _show_help(self) -> None:
        """Show help information."""
        if self.agent:
            help_text = self.agent.context_manager.get_help_text()
            print(help_text)
        else:
            print("""
TableTalk Commands:

Commands:
  /scan <directory>     - Scan files in directory for schema information
  /help                 - Show this help message
  /status              - Show system status
  /clear               - Clear conversation memory
  /exit or /quit       - Exit TableTalk

Note: LLM agent is not available. Start Ollama to enable natural language queries.
            """.strip())
    
    def _show_status(self) -> None:
        """Show system status information."""
        print("📊 TableTalk Status:")
        
        # Database status
        stats = self.metadata_store.get_database_stats()
        print(f"  Database: {stats['total_files']} files, {stats['total_columns']} columns")
        
        if stats['last_scan_time']:
            print(f"  Last scan: {stats['last_scan_time']}")
        
        # Agent status
        if self.agent:
            if self.agent.test_connection():
                print(f"  LLM Agent: ✅ Connected ({self.agent.model_name})")
            else:
                print(f"  LLM Agent: ❌ Connection failed")
        else:
            print(f"  LLM Agent: ❌ Not initialized")
        
        # Show available files
        files = self.metadata_store.list_all_files()
        if files:
            print(f"  Available files:")
            for file_info in files[:5]:  # Show first 5
                print(f"    - {file_info['file_name']} ({file_info['column_count']} columns)")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more")
        else:
            print("  No files scanned yet")
