import webview
import threading
import time
import sys
import os

# Import main backend
import main
from api import start_server

def start_backend():
    """Starts the FastAPI web server from main.py and the simulation loop"""
    main.main()

if __name__ == '__main__':
    # Add project root to sys path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run the SANCAR Backend (Simulation + FastAPI) in a separate daemon thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for FastAPI server to initialize
    time.sleep(2)
    
    # Create Native Desktop Window pointing to the local dashboard
    print("Masaüstü uygulamasi baslatiliyor...")
    webview.create_window(
        "SANCAR AI Komuta Kontrol Merkezi - Teknofest 2026", 
        "http://localhost:8000",
        width=1280,
        height=720,
        fullscreen=False, # Can be toggled with F11 natively
        frameless=False,
        min_size=(1024, 600)
    )
    
    # Start the desktop app UI loop
    webview.start()
