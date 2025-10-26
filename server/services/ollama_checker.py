"""
Ollama Detection and Installation Guide Service
Checks if Ollama is installed and running, provides installation guidance
"""
import subprocess
import platform
import requests
from typing import Dict


class OllamaChecker:
    """Service to check Ollama availability and guide installation"""

    OLLAMA_BASE_URL = "http://localhost:11434"

    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """Get current platform information"""
        system = platform.system()
        return {
            "system": system,
            "machine": platform.machine(),
            "platform": platform.platform()
        }

    @staticmethod
    def is_ollama_running() -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{OllamaChecker.OLLAMA_BASE_URL}/api/tags", timeout=2)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    @staticmethod
    def is_ollama_installed() -> bool:
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
    def get_installation_instructions() -> Dict[str, any]:
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

    @classmethod
    def get_status(cls) -> Dict[str, any]:
        """Get comprehensive Ollama status"""
        running = cls.is_ollama_running()
        installed = cls.is_ollama_installed()
        platform_info = cls.get_platform_info()

        status = {
            "running": running,
            "installed": installed,
            "platform": platform_info,
            "ready": running
        }

        # Add installation instructions if not installed or not running
        if not running:
            status["installation_instructions"] = cls.get_installation_instructions()

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


# Singleton instance
_ollama_checker = None


def get_ollama_checker() -> OllamaChecker:
    """Get singleton OllamaChecker instance"""
    global _ollama_checker
    if _ollama_checker is None:
        _ollama_checker = OllamaChecker()
    return _ollama_checker
