"""
Python-JavaScript Bridge for Desktop App
Provides communication interface between Python backend and webview frontend
"""


class DesktopBridge:
    """
    Bridge class that exposes Python methods to JavaScript.
    Methods in this class can be called from JavaScript using window.pywebview.api
    """

    def __init__(self, port: int, api_url: str):
        self.port = port
        self.api_url = api_url

    def get_port(self) -> int:
        """Get the backend server port"""
        return self.port

    def get_api_url(self) -> str:
        """Get the full API URL"""
        return self.api_url

    def quit_app(self):
        """Quit the application"""
        import webview
        windows = webview.windows
        for window in windows:
            window.destroy()
