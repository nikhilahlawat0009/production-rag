#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend for the production RAG platform.
Run this script to serve the frontend on port 8080.
"""

import http.server
import socketserver
import os
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html for root requests
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'

        # Set proper MIME types
        if self.path.endswith('.css'):
            self.send_header('Content-type', 'text/css')
        elif self.path.endswith('.js'):
            self.send_header('Content-type', 'application/javascript')

        return super().do_GET()

    def end_headers(self):
        # Add CORS headers for API calls
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server(port=8080):
    """Run the HTTP server on the specified port."""
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)

    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 Frontend server running at http://localhost:{port}")
        print("📖 Open your browser to view the documentation and demo")
        print("🔍 Make sure the FastAPI backend is running on port 8000 for the search demo")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()