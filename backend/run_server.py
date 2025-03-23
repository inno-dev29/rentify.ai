#!/usr/bin/env python3
"""
Helper script to run the Django development server on an available port.
This script finds an available port and starts the Django development server.
"""

import os
import sys
import socket
import subprocess
from contextlib import closing

def find_available_port(start_port=8000, max_attempts=100):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            if result != 0:  # Port is available
                return port
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def run_django_server():
    """Run the Django development server on an available port."""
    try:
        # Find an available port
        port = find_available_port()
        print(f"Found available port: {port}")
        
        # Get the directory of this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the command
        cmd = [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}"]
        
        # Print the command for the user
        print(f"Running: {' '.join(cmd)}")
        print(f"Server will be available at http://127.0.0.1:{port}/")
        print("Press Ctrl+C to stop the server.")
        
        # Run the command
        subprocess.run(cmd, cwd=base_dir)
        
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(run_django_server()) 