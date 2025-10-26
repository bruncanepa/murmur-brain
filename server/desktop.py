"""
Desktop Application Entry Point
Creates a native desktop window with embedded webview to run Murmur Brain
"""
import os
import sys
import threading
import time
import socket
from pathlib import Path
import webview
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from bridge import DesktopBridge
from core.config import get_settings


def find_free_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find free port in range {start_port}-{start_port + max_attempts}")


def start_backend_server(port: int):
    """Start the FastAPI backend server in a separate thread."""
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False  # Reduce console noise
    )
    server = uvicorn.Server(config)
    server.run()


def wait_for_server(port: int, timeout: int = 10):
    """Wait for the backend server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def check_ollama_on_startup():
    """Check Ollama availability on startup (non-blocking)."""
    try:
        from modules.ollama.ollama_service import OllamaService
        from core.ollama_client import get_ollama_client

        service = OllamaService(get_ollama_client())
        status = service.get_status()

        if not status['ready']:
            print(f"\n⚠️  {status['message']}")
            print(f"   Action required: {status['action']}")
            print("   The app will still work for browsing documents.")
            print("   You'll be prompted to install Ollama when you open the app.\n")
        else:
            print(f"✅ {status['message']}\n")
    except Exception as e:
        print(f"⚠️  Could not check Ollama status: {e}")
        print("   The app will still work for browsing documents.\n")


def main():
    """Main entry point for desktop application."""
    settings = get_settings()

    # Find an available port
    port = find_free_port(8000)
    api_url = f"http://127.0.0.1:{port}"

    print(f"Starting {settings.app_name} v{settings.app_version}...")
    print(f"Backend server will run on: {api_url}")

    # Start backend server in a separate thread
    backend_thread = threading.Thread(
        target=start_backend_server,
        args=(port,),
        daemon=True
    )
    backend_thread.start()

    # Wait for server to be ready
    print("Waiting for backend server to start...")
    if not wait_for_server(port, timeout=10):
        print("ERROR: Backend server failed to start!")
        sys.exit(1)

    print("Backend server is ready!")

    # Check Ollama status on startup (non-blocking)
    check_ollama_on_startup()

    # Create JavaScript bridge
    bridge = DesktopBridge(port=port, api_url=api_url)

    # Inject port into JavaScript context after page loads
    def on_loaded():
        """Inject backend port into window object after page loads."""
        js_code = f"""
            window.BACKEND_PORT = {port};
            console.log('=== Desktop Bridge Port Injection ===');
            console.log('BACKEND_PORT set to:', {port});
            console.log('====================================');
        """
        print(f"Injecting port {port} into JavaScript context...")
        window.evaluate_js(js_code)

    # Create desktop window with webview
    print("Creating desktop window...")
    window = webview.create_window(
        title=f"{settings.app_name}",
        url=api_url,
        width=1200,
        height=800,
        resizable=True,
        fullscreen=False,
        min_size=(800, 600),
        js_api=bridge  # Expose bridge methods to JavaScript
    )

    # Set up event handler for when page is loaded
    window.events.loaded += on_loaded

    # Start the webview (this blocks until window is closed)
    print(f"Launching {settings.app_name}...")
    print(f"DevTools enabled - Right-click and select 'Inspect' to open developer tools")
    webview.start(debug=True)  # Debug mode enables DevTools

    print(f"{settings.app_name} closed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
