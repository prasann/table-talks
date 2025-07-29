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
                'model': 'phi3:mini',
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
    """Check if Ollama is running and accessible.
    
    Args:
        base_url: Ollama server URL
        
    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


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
