#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend application.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support."""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    """Start the frontend server."""
    port = 3000
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    print("🚀 Starting Intelligent Query Retrieval System Frontend")
    print("=" * 60)
    print(f"📍 Server running at: http://localhost:{port}")
    print(f"📁 Serving from: {frontend_dir}")
    print("🔄 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
            print(f"✅ Frontend server started successfully!")
            print(f"🌐 Open http://localhost:{port} in your browser")
            
            # Try to open browser automatically
            try:
                webbrowser.open(f'http://localhost:{port}')
                print("🔗 Browser opened automatically")
            except:
                print("⚠️  Could not open browser automatically")
            
            print("\n📋 Make sure your backend is running on http://localhost:8000")
            print("   To start backend: cd ../backend && python start.py")
            print()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use")
            print("   Try stopping other servers or use a different port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
