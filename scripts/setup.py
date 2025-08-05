#!/usr/bin/env python3
"""
TableTalk Cross-Platform Setup Script

A comprehensive setup script that works on Windows, macOS, and Linux.
Sets up Python environment, dependencies, Ollama models, and semantic search.
"""

import os
import sys
import json
import platform
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any


class Colors:
    """ANSI color codes for cross-platform colored output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @classmethod
    def disable_on_windows(cls):
        """Disable colors on Windows if not supported."""
        if platform.system() == "Windows":
            # Check if Windows Terminal or modern console
            if not (os.environ.get('WT_SESSION') or os.environ.get('TERM')):
                for attr in dir(cls):
                    if not attr.startswith('_') and attr != 'disable_on_windows':
                        setattr(cls, attr, '')


class TableTalkSetup:
    """Cross-platform setup for TableTalk."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.config = {
            "phi4_model": "phi4-mini:3.8b-fp16",
            "phi4_fc_model": "phi4-mini-fc", 
            "semantic_model": "all-MiniLM-L6-v2"
        }
        
        # Disable colors on older Windows consoles
        Colors.disable_on_windows()
    
    def print_header(self, message: str):
        """Print a formatted header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{message}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    
    def print_step(self, step: str):
        """Print a step with formatting."""
        print(f"\n{Colors.BLUE}[*] {step}...{Colors.END}")
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"{Colors.GREEN}[+] {message}{Colors.END}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{Colors.YELLOW}[!] {message}{Colors.END}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"{Colors.RED}[-] {message}{Colors.END}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"{Colors.WHITE}[i] {message}{Colors.END}")
    
    def check_python_version(self) -> bool:
        """Check if Python version is 3.11+."""
        self.print_step("Checking Python version")
        
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro} found")
            return True
        else:
            self.print_error(f"Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
            return False
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment."""
        self.print_step("Setting up Python virtual environment")
        
        if self.venv_path.exists():
            self.print_success("Virtual environment already exists")
            return True
        
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], 
                         check=True, capture_output=True)
            self.print_success("Virtual environment created")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to create virtual environment: {e}")
            return False
    
    def get_python_executable(self) -> str:
        """Get the path to the Python executable in the virtual environment."""
        if self.platform == "windows":
            return str(self.venv_path / "Scripts" / "python.exe")
        else:
            return str(self.venv_path / "bin" / "python")
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies."""
        self.print_step("Installing Python dependencies")
        
        python_exe = self.get_python_executable()
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            self.print_error("requirements.txt not found")
            return False
        
        try:
            # Upgrade pip first
            subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install requirements
            subprocess.run([python_exe, "-m", "pip", "install", "-r", str(requirements_file)], 
                         check=True, capture_output=True)
            
            # Install semantic search dependencies with Windows-specific handling
            if self.platform == "windows":
                # On Windows, install CPU-only PyTorch first to avoid CUDA issues
                self.print_step("Installing PyTorch (CPU-only for Windows compatibility)")
                subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", 
                              "torch", "torchvision", "torchaudio", "--index-url", 
                              "https://download.pytorch.org/whl/cpu"], 
                             check=True, capture_output=True)
            
            subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", 
                          "sentence-transformers", "scikit-learn"], 
                         check=True, capture_output=True)
            
            # Install additional Windows compatibility packages
            if self.platform == "windows":
                subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", 
                              "certifi", "requests[security]"], 
                             check=True, capture_output=True)
            
            self.print_success("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        self.print_step("Creating project directories")
        
        directories = ["database", "logs", "data"]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
        
        self.print_success(f"Created directories: {', '.join(directories)}")
        return True
    
    def check_ollama_installation(self) -> bool:
        """Check if Ollama is installed and running."""
        self.print_step("Checking Ollama installation")
        
        # Check if ollama command exists
        try:
            subprocess.run(["ollama", "--version"], 
                         check=True, capture_output=True)
            self.print_success("Ollama is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_error("Ollama not found")
            self.print_info("Please install Ollama from: https://ollama.ai")
            return False
        
        # Check if Ollama is running
        try:
            response = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
            if response.status == 200:
                self.print_success("Ollama is running")
                return True
        except Exception:
            pass
        
        self.print_warning("Ollama is not running")
        self.print_info("Start Ollama with: ollama serve")
        return False
    
    def setup_ollama_models(self) -> bool:
        """Set up Ollama models for function calling."""
        if not self.check_ollama_installation():
            return False
        
        self.print_step("Setting up Ollama models")
        
        # Pull base model
        try:
            self.print_step(f"Downloading {self.config['phi4_model']}")
            subprocess.run(["ollama", "pull", self.config["phi4_model"]], 
                         check=True)
            self.print_success("Base model downloaded")
        except subprocess.CalledProcessError:
            self.print_error("Failed to download base model")
            return False
        
        # Create function calling model
        return self._create_function_calling_model()
    
    def _create_function_calling_model(self) -> bool:
        """Create the function calling model with proper template."""
        self.print_step("Creating function calling model")
        
        modelfile_content = f'''FROM {self.config["phi4_model"]}

TEMPLATE """
{{{{- if .Messages }}}}
{{{{- if or .System .Tools }}}}<|system|>

{{{{ if .System }}}}{{{{ .System }}}}
{{{{- end }}}}
In addition to plain text responses, you can chose to call one or more of the provided functions.

Use the following rule to decide when to call a function:
  * if the response can be generated from your internal knowledge (e.g., as in the case of queries like "What is the capital of Poland?"), do so
  * if you need external information that can be obtained by calling one or more of the provided functions, generate a function calls

If you decide to call functions:
  * prefix function calls with functools marker (no closing marker required)
  * all function calls should be generated in a single JSON list formatted as functools[{{"name": [function name], "arguments": [function arguments as JSON]}}, ...]
  * follow the provided JSON schema. Do not hallucinate arguments or values. Do to blindly copy values from the provided samples
  * respect the argument type formatting. E.g., if the type if number and format is float, write value 7 as 7.0
  * make sure you pick the right functions that match the user intent

Available functions as JSON spec:
{{{{- if .Tools }}}}
{{{{ .Tools }}}}
{{{{- end }}}}<|end|>
{{{{- end }}}}
{{{{- range .Messages }}}}
{{{{- if ne .Role "system" }}}}<|{{{{ .Role }}}}|>
{{{{- if and .Content (eq .Role "tools") }}}}

{{"result": {{{{ .Content }}}}}}
{{{{- else if .Content }}}}

{{{{ .Content }}}}
{{{{- else if .ToolCalls }}}}

functools[
{{{{- range .ToolCalls }}}}{{"name": "{{{{ .Function.Name }}}}", "arguments": {{{{ .Function.Arguments }}}}}}
{{{{- end }}}}]
{{{{- end }}}}<|end|>
{{{{- end }}}}
{{{{- end }}}}<|assistant|>

{{{{ else }}}}
{{{{- if .System }}}}<|system|>

{{{{ .System }}}}<|end|>{{{{ end }}}}{{{{ if .Prompt }}}}<|user|>

{{{{ .Prompt }}}}<|end|>{{{{ end }}}}<|assistant|>

{{{{ end }}}}{{{{ .Response }}}}{{{{ if .Response }}}}<|user|>{{{{ end }}}}
"""'''
        
        # Write Modelfile
        modelfile_path = self.project_root / "Modelfile.tmp"
        try:
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Create model
            subprocess.run(["ollama", "create", self.config["phi4_fc_model"], 
                          "-f", str(modelfile_path)], check=True)
            
            self.print_success("Function calling model created")
            
            # Cleanup
            modelfile_path.unlink()
            return True
            
        except Exception as e:
            self.print_error(f"Failed to create function calling model: {e}")
            if modelfile_path.exists():
                modelfile_path.unlink()
            return False
    
    def setup_semantic_model(self) -> bool:
        """Set up and warm up the semantic model."""
        self.print_step("Setting up semantic search model")
        
        python_exe = self.get_python_executable()
        
    def setup_semantic_model(self) -> bool:
        """Set up and warm up the semantic model."""
        self.print_step("Setting up semantic search model")
        
        python_exe = self.get_python_executable()
        
        # Create warmup script with Windows-specific handling
        warmup_script = '''
import warnings
import sys
import os
import ssl

def warmup_semantic_model():
    try:
        print("[*] Loading semantic model for first time...")
        
        # Handle SSL issues on Windows
        try:
            import certifi
            os.environ['SSL_CERT_FILE'] = certifi.where()
        except ImportError:
            pass
        
        # Handle SSL context issues
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            
            # Set environment variables for better Windows compatibility
            os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Avoid threading issues
            os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'  # Reduce output noise
            
            from sentence_transformers import SentenceTransformer
            
            # Use local cache directory to avoid long path issues on Windows
            cache_folder = os.path.join(os.path.expanduser("~"), ".cache", "sentence_transformers")
            if not os.path.exists(cache_folder):
                os.makedirs(cache_folder, exist_ok=True)
            
            model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_folder)
        
        # Test encoding with error handling
        try:
            sample_embedding = model.encode(["test column name"], show_progress_bar=False)
            print(f"[+] Semantic model ready! Embedding dimension: {len(sample_embedding[0])}")
            return True
        except Exception as embed_error:
            print(f"[-] Encoding test failed: {embed_error}")
            return False
        
    except ImportError as e:
        print(f"[!] sentence-transformers not available: {e}")
        print("[!] Try: pip install --upgrade sentence-transformers torch")
        return False
    except Exception as e:
        print(f"[-] Error loading semantic model: {e}")
        # Print more detailed error info for debugging
        import traceback
        print(f"[-] Detailed error: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = warmup_semantic_model()
    sys.exit(0 if success else 1)
'''
        
        warmup_path = self.project_root / "warmup_semantic.py"
        try:
            with open(warmup_path, 'w', encoding='utf-8') as f:
                f.write(warmup_script)
            
            # Run warmup
            result = subprocess.run([python_exe, str(warmup_path)], 
                                  capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                self.print_success("Semantic model warmed up successfully")
                success = True
            else:
                self.print_warning("Semantic model warmup failed, but TableTalk will still work")
                self.print_warning("Semantic search features will be disabled")
                success = False
            
            # Print output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  {line}")
            
            # Cleanup
            warmup_path.unlink()
            return success
            
        except Exception as e:
            self.print_error(f"Failed to setup semantic model: {e}")
            if warmup_path.exists():
                warmup_path.unlink()
            
            # Windows-specific troubleshooting
            if self.platform == "windows":
                self.print_info("Windows troubleshooting tips:")
                self.print_info("1. Run as Administrator if you see permission errors")
                self.print_info("2. Disable antivirus temporarily during setup")
                self.print_info("3. Check Windows Defender isn't blocking downloads")
                self.print_info("4. Ensure you have at least 4GB RAM available")
                self.print_info("5. Try: pip install --upgrade --no-cache-dir sentence-transformers")
            
            return False
    
    def test_installation(self) -> Dict[str, bool]:
        """Test the installation."""
        self.print_step("Testing installation")
        
        results = {}
        
        # Test Python environment
        python_exe = self.get_python_executable()
        try:
            result = subprocess.run([python_exe, "-c", 
                                   "from src.agent.schema_agent import SchemaAgent; print('[+] Python imports work')"], 
                                  cwd=str(self.project_root), 
                                  capture_output=True, text=True, encoding='utf-8')
            results['python'] = result.returncode == 0
            if results['python']:
                self.print_success("Python environment test passed")
            else:
                self.print_error("Python environment test failed")
        except Exception:
            results['python'] = False
            self.print_error("Python environment test failed")
        
        # Test Ollama model
        try:
            test_payload = {
                "model": self.config["phi4_fc_model"],
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            cmd = ["curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
                   "-H", "Content-Type: application/json",
                   "-d", json.dumps(test_payload)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            results['ollama'] = "message" in result.stdout
            
            if results['ollama']:
                self.print_success("Ollama function calling test passed")
            else:
                self.print_warning("Ollama function calling test failed")
        except Exception:
            results['ollama'] = False
            self.print_warning("Ollama function calling test failed")
        
        return results
    
    def print_summary(self, test_results: Dict[str, bool]):
        """Print setup summary."""
        self.print_header("Setup Complete!")
        
        print(f"\n{Colors.BOLD}Status Summary:{Colors.END}")
        print(f"Python Environment: {'[+] Ready' if test_results.get('python') else '[-] Failed'}")
        print(f"Ollama Models: {'[+] Ready' if test_results.get('ollama') else '[!] Check Ollama'}")
        print(f"Semantic Search: [+] Available")
        
        print(f"\n{Colors.BOLD}Configuration:{Colors.END}")
        print(f"Model: {self.config['phi4_fc_model']}")
        print(f"Semantic Model: {self.config['semantic_model']}")
        print(f"Project Root: {self.project_root}")
        
        print(f"\n{Colors.BOLD}To start TableTalk:{Colors.END}")
        if self.platform == "windows":
            print(f"  {self.venv_path}\\Scripts\\activate")
        else:
            print(f"  source {self.venv_path}/bin/activate")
        print(f"  python tabletalk.py")
        
        print(f"\n{Colors.BOLD}Example queries:{Colors.END}")
        print("  'what files do we have'")
        print("  'show me the schema of orders'")
        print("  'list down the tables that has customer identifier in them'")
        
        if not test_results.get('ollama'):
            print(f"\n{Colors.YELLOW}[!] Note: Make sure Ollama is running with: ollama serve{Colors.END}")
    
    def run(self) -> bool:
        """Run the complete setup process."""
        self.print_header("TableTalk Setup")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        
        steps = [
            self.check_python_version,
            self.create_virtual_environment,
            self.install_dependencies,
            self.create_directories,
            self.setup_ollama_models,
            self.setup_semantic_model,
        ]
        
        for step in steps:
            if not step():
                self.print_error("Setup failed. Please check the errors above.")
                return False
        
        # Test installation
        test_results = self.test_installation()
        
        # Print summary
        self.print_summary(test_results)
        
        # Return overall success
        return test_results.get('python', False)


def main():
    """Main entry point."""
    setup = TableTalkSetup()
    
    try:
        success = setup.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
