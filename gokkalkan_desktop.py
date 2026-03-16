import os
# Add src to PATH for IDE and runtime resolution
import sys
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

import webview
import threading
import time
import yaml # Keep yaml as it was in original, not explicitly removed by instruction

from src.radar import RadarSistemi
from src.interceptor import OnleyiciBatarya, Lazer_CIWS
from src.telemetry import TelemetriSistemi
import api
from api import start_server, push_data_to_clients

class GokkalkanDesktop:
    def __init__(self):
        self.telemetri = TelemetriSistemi(log_dosyasi="logs/gokkalkan_desktop.log")
        self.radar = RadarSistemi(menzil_km=20, tespit_olasiligi=0.9)
        self.batarya = OnleyiciBatarya(muhimmat=100)
        self.ciws = Lazer_CIWS(menzil_km=2.0)
        
        self.auto_fire = True # Default to auto for desktop demo
        self.current_stage = 2
        self.running = True
        self.last_event = "Masaüstü Uygulaması Başlatıldı."

    def simulation_loop(self):
        # Start API
        threading.Thread(target=start_server, kwargs={"host": "127.0.0.1", "port": 8000}, daemon=True).start()
        
        # Set initial stage
        self.radar.hedef_uret_asama2()
        
        while self.running:
            try:
                self.radar.guncelle()
                self.radar.tara()
                
                vurulanlar = self.batarya.guncelle(1.0, self.radar.aktif_hedefler)
                vurulanlar_ciws = self.ciws.guncelle(1.0, self.radar.aktif_hedefler)
                
                for v in set(vurulanlar + vurulanlar_ciws):
                    if v in self.radar.aktif_hedefler:
                        self.radar.aktif_hedefler.remove(v)
                        self.telemetri.olay_kaydet("SUCCESS", f"HEDEF İMHA: {v.id}")

                if self.auto_fire:
                    for h in self.radar.aktif_hedefler:
                        if getattr(h, 'is_dost', False): continue
                        if any(f.hedef.id == h.id for f in self.batarya.aktif_fuzeler): continue
                        try:
                            self.batarya.angaje_ol(h)
                        except: pass

                # Sync with UI
                targets_data = [{"id": h.id, "x": h.x, "y": h.y, "z": h.z, "mesafe": h.mesafe, "is_dost": getattr(h, 'is_dost', False), "etiket": getattr(h, 'etiket', "Hedef")} for h in self.radar.aktif_hedefler]
                out_data = {"targets": targets_data, "interceptors": [{"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id} for f in self.batarya.aktif_fuzeler], "lasers": self.ciws.aktif_atislar, "stage": self.current_stage}
                push_data_to_clients(out_data)

                # Process Remote Commands
                while api.frontend_commands:
                    cmd = api.frontend_commands.pop(0)
                    self.process_command(cmd.get("action"), cmd.get("target_id"))

            except Exception as e:
                print(f"Hata: {e}")
            
            time.sleep(1)

    def process_command(self, action: str, target_id: str | None = None):
        if action == "set_stage_1": self.set_stage(1)
        elif action == "set_stage_2": self.set_stage(2)
        elif action == "set_stage_3": self.set_stage(3)
        elif action == "toggle_auto_fire": self.auto_fire = not self.auto_fire
        elif action == "manual_fire": self.manual_fire(target_id)

    def set_stage(self, stage: int):
        self.current_stage = stage
        if stage == 1: self.radar.hedef_uret_asama1(); self.auto_fire = False
        elif stage == 2: self.radar.hedef_uret_asama2(); self.auto_fire = True
        elif stage == 3: self.radar.hedef_uret_asama3(); self.auto_fire = True
        self.telemetri.olay_kaydet("INFO", f"Aşama {stage} Başlatıldı.")

    def manual_fire(self, target_id: str | None = None):
        target = next((h for h in self.radar.aktif_hedefler if h.id == target_id), None) if target_id else (min((h for h in self.radar.aktif_hedefler if not getattr(h, 'is_dost', False)), key=lambda x: getattr(x, 'mesafe', 999.0), default=None))
        if target:
            try:
                self.batarya.angaje_ol(target)
            except: pass

if __name__ == "__main__":
    app = GokkalkanDesktop()
    
    # Run simulation in thread
    sim_thread = threading.Thread(target=app.simulation_loop, daemon=True)
    sim_thread.start()
    
    # Create webview window
    print("Masaüstü penceresi oluşturuluyor...")
    window = webview.create_window(
        "GÖKKALKAN AI - Komuta Kontrol Merkezi",
        "http://localhost:8000",
        width=1280,
        height=800,
        resizable=True
    )
    
    # Start webview loop (Blocking)
    webview.start(debug=True)
    app.running = False
