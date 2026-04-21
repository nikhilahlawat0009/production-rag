#!/usr/bin/env python3
"""
My simple frontend server - serves the documentation and demo.

I built this quick HTTP server to showcase my work without needing
a full web framework. It serves the HTML, CSS, and JS files and
includes CORS headers so the frontend can call my FastAPI backend.
"""

import http.server
import socketserver
import os
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    Custom request handler that serves my frontend properly.

    Handles routing, MIME types, and CORS for the API calls.
    """
    def do_GET(self):
        # Serve index.html for root requests
        if self.path == '/' or self.path == '/index.html':
            self.path = '/index.html'

        # Set proper MIME types for my files
        if self.path.endswith('.css'):
            self.send_header('Content-type', 'text/css')
        elif self.path.endswith('.js'):
            self.send_header('Content-type', 'application/javascript')

        return super().do_GET()

    def end_headers(self):
        # Add CORS headers so my frontend can call the API
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def run_server(port=8080):
    """
    Start the server and serve my frontend.

    Changes to the frontend directory and starts serving.
    Includes helpful messages for users.
    """
    # Switch to the frontend directory
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)

    with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
        print(f"Frontend server running at http://localhost:{port}")
        print("Open your browser to view the documentation and demo")
        print("Make sure the FastAPI backend is running on port 8000 for the search demo")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
            httpd.shutdown()

if __name__ == "__main__":
    run_server()