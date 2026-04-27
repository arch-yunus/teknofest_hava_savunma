# Add src to PATH for IDE and runtime resolution
import os
import sys
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

import time
import threading
import logging

from src.engine import ArgusEngine
from src.api import start_server

def main():
    # Setup Logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ArgusLauncher")
    
    logger.info("ARGUS | Millî Hava Savunma Simülasyonu Başlatılıyor...")

    # 1. Initialize Engine
    engine = ArgusEngine(fps=5) # High frequency for smooth UI
    
    # 2. Start API Server (Background)
    api_thread = threading.Thread(
        target=start_server, 
        kwargs={"host": "0.0.0.0", "port": 8000}, 
        daemon=True
    )
    api_thread.start()
    
    logger.info("Taktik Sunucu Aktif: http://localhost:8000")

    # 3. Start Engine Loop
    engine.start()
    
    logger.info("Sistem Hazır. Arayüzden kontrol edebilirsiniz.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Kapatılıyor...")
        engine.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
