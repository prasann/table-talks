"""TableTalk main entry point."""

import os
import sys
import yaml
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.chat_interface import ChatInterface


def setup_logging(config: dict) -> None:
    """Set up logging configuration.
    
    Args:
        config: Configuration dictionary
    """
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('file', './logs/tabletalk.log')
    
    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


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
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Check Ollama connection
    ollama_url = config['llm']['base_url']
    if not check_ollama_connection(ollama_url):
        print(f"⚠️  Warning: Cannot connect to Ollama at {ollama_url}")
        print("   Natural language queries will not be available.")
        print("   Start Ollama with: ollama serve")
        print()
    
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
