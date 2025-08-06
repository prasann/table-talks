"""Simple chat interface for TableTalk."""

import logging
import os
import sys
from pathlib import Path

# Internal imports
from ..metadata.metadata_store import MetadataStore
from ..metadata.schema_extractor import SchemaExtractor
from ..agent.schema_agent import SchemaAgent
from ..utils.session_logger import QuerySessionLogger
from .rich_formatter import CLIFormatter


class ChatInterface:
    """Simple command-line interface for TableTalk."""
    
    def __init__(self, config):
        """Initialize the chat interface."""
        self.config = config
        self.formatter = CLIFormatter()  # Rich formatter for all CLI output
        
        # Initialize session logger (clean, structured logging)
        verbose_logging = config.get('logging', {}).get('verbose', False)
        self.session_logger = QuerySessionLogger(
            log_file=config.get('logging', {}).get('file', 'logs/tabletalk.log'),
            verbose=verbose_logging
        )
        
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
                base_url=config['llm']['base_url'],
                timeout=config['llm'].get('timeout', 120)  # Use config timeout or default to 120
            )
            
            # Get status to display the right message
            status = self.agent.get_status()
            if status.get('function_calling'):
                self.formatter.print_status({
                    'mode': 'Function Calling',
                    'tools_count': status['tools_available'],
                    'tools_list': status['tool_names'],
                    'llm_available': True,
                    'function_calling': True,
                    'model_name': status.get('model_name', '')
                })
            else:
                self.formatter.print_error("Function calling not supported - please use phi4-mini-fc model")
                
        except Exception as e:
            self.formatter.print_warning(f"LLM agent not available: {e}")
            self.agent = None
        
        self.running = False

    def start(self):
        """Start the interactive CLI."""
        self.formatter.print_welcome()
        
        if self.agent and self.agent.check_llm_availability():
            self.formatter.print_mode_info(intelligent_mode=True)
        else:
            self.formatter.print_mode_info(intelligent_mode=False)
        
        self.formatter.print_rule()
        
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
                self.formatter.print_goodbye()
                self.session_logger.log_session_end()
                break
            except EOFError:
                self.formatter.print_goodbye()
                self.session_logger.log_session_end()
                break

    def _handle_command(self, command):
        """Handle CLI commands."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd in ['/exit', '/quit']:
            self.formatter.print_goodbye()
            self.session_logger.log_session_end()
            self.running = False
        elif cmd == '/help':
            self._show_help()
        elif cmd == '/status':
            self._show_status()
        elif cmd == '/scan':
            if len(parts) < 2:
                self.formatter.print_error("Usage: /scan <directory>")
                return
            self._scan_directory(parts[1])
        elif cmd == '/strategy':
            # Remove strategy switching - SchemaAgent auto-detects
            self._show_agent_info()
        else:
            self.formatter.print_error(f"Unknown command: {cmd}")
            self.formatter.print_info("Use /help for available commands")

    def _handle_query(self, query):
        """Handle natural language queries."""
        if not self.agent:
            self.formatter.print_warning("Agent not available. Please try /scan to analyze files first.")
            return
        
        # Log query start with session logger
        self.session_logger.log_query_start(query)
        
        try:
            # Show loading indicator while processing query
            with self.formatter.create_loading_indicator("[AI] Analyzing your query"):
                response = self.agent.query(query)
            
            # Get the actual tools used from the agent
            tools_used = self.agent.get_last_tools_used() if hasattr(self.agent, 'get_last_tools_used') else []
            
            # Log successful completion with actual tools used
            self.session_logger.log_query_success(response, tools_used=tools_used)
            
            self.formatter.print_agent_response(response)
        except Exception as e:
            # Log query error
            self.session_logger.log_query_error(str(e))
            self.formatter.print_error("Error processing query", str(e))

    def _scan_directory(self, directory):
        """Scan directory for files."""
        directory_path = Path(directory).resolve()
        
        if not directory_path.exists():
            self.formatter.print_error(f"Directory not found: {directory}")
            return
        
        self.formatter.print_scan_start(str(directory_path))
        
        file_count = 0
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.csv', '.parquet']:
                try:
                    schema_info = self.schema_extractor.extract_from_file(str(file_path))
                    if schema_info:
                        self.metadata_store.store_schema_info(schema_info)
                        self.formatter.print_scan_progress(file_path.name, len(schema_info))
                        file_count += 1
                except Exception as e:
                    self.formatter.print_scan_error(file_path.name, str(e))
        
        # Log scan operation with session logger
        self.session_logger.log_scan_operation(str(directory_path), file_count)
        self.formatter.print_scan_complete(file_count)

    def _show_status(self):
        """Show current status."""
        status_data = {}
        
        if self.agent:
            status = self.agent.get_status()
            status_data.update({
                'mode': f"{status.get('agent_type', 'Unknown')} ({status.get('mode', 'Unknown')})",
                'llm_available': status['llm_available'],
                'function_calling': status.get('function_calling', False),
                'model_name': status['model_name']
            })
        
        files = self.metadata_store.list_all_files()
        status_data['files_scanned'] = len(files)
        
        self.formatter.print_status(status_data)
    
    def _show_agent_info(self):
        """Show current agent information."""
        if not self.agent:
            self.formatter.print_warning("Agent not available")
            return
            
        status = self.agent.get_status()
        agent_data = {
            'mode': status.get('mode', 'Unknown'),
            'model_name': status['model_name'],
            'llm_available': status['llm_available'],
            'function_calling': status.get('function_calling', False)
        }
        
        if 'capabilities' in status:
            agent_data['capabilities'] = ', '.join(status['capabilities'])
        
        self.formatter.print_status(agent_data)
    
    def _show_strategies(self):
        """Show available strategies (deprecated - keeping for compatibility)."""
        self._show_agent_info()
    
    def _switch_strategy(self, strategy_type):
        """Switch strategy (deprecated - SchemaAgent auto-detects)."""
        self.formatter.print_warning("Strategy switching is no longer needed - SchemaAgent auto-detects capabilities!")
        self._show_agent_info()

    def _show_help(self):
        """Show help message."""
        self.formatter.print_command_help()
