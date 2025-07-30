"""TableTalk main entry point."""

import os
import sys
import yaml
import logging
import warnings
from pathlib import Path

# Suppress LangChain deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*deprecated.*", category=DeprecationWarning)

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Handle both direct execution and module execution
try:
    from .cli.chat_interface import ChatInterface
    from .utils.logger import setup_logger
except ImportError:
    # Fallback for direct execution
    from cli.chat_interface import ChatInterface
    from utils.logger import setup_logger


def load_config() -> dict:
    """Load configuration from config file.
    
    Returns:
        Configuration dictionary
    """
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Return default configuration
        return {
            'database': {'path': './database/metadata.duckdb'},
            'llm': {
                'model': 'phi3:mini',  # Works well for structured output
                'base_url': 'http://localhost:11434',
                'temperature': 0.1,
                'max_tokens': 1000
            },
            'scanner': {
                'max_file_size_mb': 100,
                'sample_size': 1000
            },
            'cli': {'prompt': 'TableTalk> '},
            'logging': {'level': 'INFO', 'file': './logs/tabletalk.log'}
        }


def check_ollama_connection(base_url: str) -> bool:
    """Check if Ollama is running and accessible with Phi-4 model.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        
        # Check if connection is successful
        if response.status_code != 200:
            return False
            
        # Check if Phi model is available
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        phi_available = any("phi" in name.lower() for name in model_names)
        phi4_fc_available = any("phi4-mini-fc" in name.lower() for name in model_names)
        
        if phi4_fc_available:
            print("✅ Phi-4 function calling model found!")
        elif phi_available:
            print("⚠️  Phi model found but no function calling support.")
            print("   Run ./setup_phi4_function_calling.sh for better performance")
        else:
            print("⚠️  Warning: No Phi model found. Basic mode only.")
            print("   Consider running: ollama pull phi3:mini")
        print()
            
        return True
    except Exception:
        return False


def run_tabletalk_commands(commands):
    """Run TableTalk commands programmatically and return results.
    
    Args:
        commands: List of commands to execute
        
    Returns:
        List of (command, response, success) tuples
    """
    try:
        # Create instance
        config = load_config()
        log_level = config.get('logging', {}).get('level', 'INFO')
        setup_logger(level=getattr(logging, log_level.upper()))
        
        chat = ChatInterface(config)
        results = []
        
        # Redirect stdout to capture output
        import io
        from contextlib import redirect_stdout
        
        for command in commands:
            try:
                if command.strip().lower() in ['quit', 'exit']:
                    break
                
                # Capture output
                output_buffer = io.StringIO()
                with redirect_stdout(output_buffer):
                    if command.startswith('/') or command.startswith('scan '):
                        # Handle as command
                        if command.startswith('scan '):
                            command = '/' + command
                        chat._handle_command(command)
                    else:
                        # Handle as query
                        chat._handle_query(command)
                
                response = output_buffer.getvalue().strip()
                results.append((command, response, True))
                
            except Exception as e:
                results.append((command, str(e), False))
        
        return results
        
    except Exception as e:
        return [("initialization", str(e), False)]


def main():
    """Main entry point for TableTalk."""
    print("🗣️  Starting TableTalk...")
    
    # Load configuration
    config = load_config()
    
    # Set up centralized logging (debug to files, warnings to console)
    log_level = config.get('logging', {}).get('level', 'INFO')
    setup_logger(level=getattr(logging, log_level.upper()))
    logger = logging.getLogger("tabletalk")
    
    # Check Ollama connection
    ollama_url = config['llm']['base_url']
    if not check_ollama_connection(ollama_url):
        print(f"⚠️  Warning: Cannot connect to Ollama at {ollama_url}")
        print("   Natural language queries will not be available.")
        print("   Start Ollama with: ollama serve")
        print()
        logger.warning(f"Ollama connection failed at {ollama_url}")
    else:
        logger.info(f"Ollama connection successful at {ollama_url}")
    
    try:
        # Initialize and start chat interface
        chat = ChatInterface(config)
        chat.start()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
