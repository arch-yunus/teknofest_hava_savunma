import os
import sys
import threading
import time
import webview

from src.engine import ArgusEngine
import src.api as api

class ArgusDesktop:
    """ARGUS Desktop Application - Unified Engine Client"""
    def __init__(self):
        # Initialize the core engine
        self.engine = ArgusEngine()
        self.running = True

    def simulation_loop(self):
        # Start API for the Webview internal dashboard
        threading.Thread(target=api.start_server, kwargs={"host": "127.0.0.1", "port": 8000}, daemon=True).start()
        
        # Initial simulation setup
        self.engine.set_stage(2) # Default to Stage 2 for desktop demo
        
        while self.running:
            try:
                # Perform a simulation tick
                self.engine.tick()
                
            except Exception as e:
                print(f"Desktop Simulation Error: {e}")
            
            time.sleep(0.5)

if __name__ == "__main__":
    # Ensure src is in path (though usually it should be if run from root)
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    if ROOT_DIR not in sys.path:
        sys.path.append(os.path.join(ROOT_DIR, 'src'))

    app = ArgusDesktop()
    
    # Run the core simulation engine in a background thread
    sim_thread = threading.Thread(target=app.simulation_loop, daemon=True)
    sim_thread.start()
    
    print("ARGUS Masaüstü Komuta Merkezi başlatılıyor...")
    
    # 0. API Servisi için bekleme (Resilience)
    max_retries = 10
    while max_retries > 0:
        try:
            import socket
            with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                break
        except:
            max_retries -= 1
            time.sleep(0.5)

    # 1. Webview penceresini oluştur
    window = webview.create_window(
        "ARGUS AI - Komuta Kontrol Merkezi (v10.0)",
        "http://localhost:8000",
        width=1280,
        height=800,
        resizable=True
    )
    
    # 2. GUI döngüsünü başlat
    webview.start(debug=False)
    app.running = False
