"""
Ollama service.

Provides Ollama status checking and model management.
"""
import subprocess
import platform
import requests
from typing import List, Dict
from core.ollama_client import OllamaClient
from .ollama_scraper import get_scraper


class OllamaService:
    """Service for Ollama operations."""

    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        self.scraper = get_scraper()

    @staticmethod
    def _is_ollama_installed() -> bool:
        """Check if Ollama is installed (binary exists)"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def _get_installation_instructions() -> Dict:
        """Get platform-specific installation instructions"""
        system = platform.system()

        instructions = {
            "Darwin": {  # macOS
                "platform": "macOS",
                "method": "Homebrew or Direct Download",
                "steps": [
                    "Option 1 - Using Homebrew:",
                    "1. Open Terminal",
                    "2. Run: brew install ollama",
                    "3. Run: ollama serve",
                    "",
                    "Option 2 - Direct Download:",
                    "1. Visit https://ollama.com/download/mac",
                    "2. Download and install Ollama.app",
                    "3. Launch Ollama from Applications"
                ],
                "download_url": "https://ollama.com/download/mac",
                "command": "brew install ollama && ollama serve"
            },
            "Linux": {
                "platform": "Linux",
                "method": "Install Script",
                "steps": [
                    "1. Open Terminal",
                    "2. Run: curl -fsSL https://ollama.com/install.sh | sh",
                    "3. Start service: ollama serve",
                    "",
                    "Or use package manager:",
                    "- Ubuntu/Debian: Check Ollama website for .deb package",
                    "- Fedora/RHEL: Check Ollama website for .rpm package"
                ],
                "download_url": "https://ollama.com/download/linux",
                "command": "curl -fsSL https://ollama.com/install.sh | sh"
            },
            "Windows": {
                "platform": "Windows",
                "method": "Direct Download",
                "steps": [
                    "1. Visit https://ollama.com/download/windows",
                    "2. Download OllamaSetup.exe",
                    "3. Run the installer",
                    "4. Ollama will start automatically",
                    "",
                    "Alternative - Using winget:",
                    "1. Open PowerShell or Command Prompt",
                    "2. Run: winget install Ollama.Ollama"
                ],
                "download_url": "https://ollama.com/download/windows",
                "command": "winget install Ollama.Ollama"
            }
        }

        return instructions.get(system, {
            "platform": "Unknown",
            "method": "Manual Download",
            "steps": [
                "1. Visit https://ollama.com/download",
                "2. Select your operating system",
                "3. Follow the installation instructions"
            ],
            "download_url": "https://ollama.com/download"
        })

    def get_status(self) -> Dict:
        """
        Get comprehensive Ollama installation and running status.

        Returns:
            Dict with detailed status information including installation instructions
        """
        # Check if running
        running = False
        try:
            is_running = self.ollama.check_model_available()
            running = is_running
        except Exception:
            running = False

        # Check if installed
        installed = self._is_ollama_installed()

        # Get platform info
        platform_info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "platform": platform.platform()
        }

        status = {
            "running": running,
            "installed": installed,
            "platform": platform_info,
            "ready": running
        }

        # Add installation instructions if not installed or not running
        if not running:
            status["installation_instructions"] = self._get_installation_instructions()

            if installed and not running:
                status["message"] = "Ollama is installed but not running. Please start the Ollama service."
                status["action"] = "start_service"
            elif not installed:
                status["message"] = "Ollama is not installed. Please install it to use Local Brain."
                status["action"] = "install_required"
        else:
            status["message"] = "Ollama is running and ready!"
            status["action"] = "ready"

        return status

    def search_models(self, query: str = "", category: str = None) -> List[Dict]:
        """
        Search Ollama library for models.

        Args:
            query: Search query
            category: Category filter

        Returns:
            List of model dictionaries
        """
        return self.scraper.search_models(query, category)

    def get_categories(self) -> List[str]:
        """
        Get list of model categories.

        Returns:
            List of category names
        """
        return self.scraper.get_categories()

    def get_chat_models(self) -> List[str]:
        """
        Get available chat models from Ollama.

        Returns:
            List of model names
        """
        return self.ollama.list_chat_models()
