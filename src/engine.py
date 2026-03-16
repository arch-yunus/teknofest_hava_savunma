import time
import threading
import logging
from typing import Dict, Any, List
import api
from src.radar import RadarSistemi, HavaDurumu
from src.interceptor import OnleyiciBatarya, Lazer_CIWS
from src.tehdit_siniflandirici import TehditSiniflandirici, TehditOnceligi
from src.kalman_takip import KalmanTakipYoneticisi
import src.utils as utils

class GokkalkanEngine:
    """GökKalkan Millî Hava Savunma Sistemi - Merkezi Simülasyon Motoru"""
    def __init__(self, fps: int = 2):
        self.fps = fps
        self.dt = 1.0 / fps
        self.running = False
        
        # Core Components
        self.radar = RadarSistemi(menzil_km=20, tespit_olasiligi=0.95)
        self.batarya = OnleyiciBatarya(muhimmat=100)
        self.ciws = Lazer_CIWS(menzil_km=2.5, atis_hizi=15)
        self.siniflandirici = TehditSiniflandirici()
        self.kalman = KalmanTakipYoneticisi(dt=self.dt)
        
        # State
        self.auto_fire = False
        self.current_stage = 0
        self.emp_blast_active = False
        self.emp_timer: float = 0.0
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("GokkalkanEngine")

    def start(self):
        self.running = True
        self.logger.info("GökKalkan Simülasyon Motoru Başlatıldı.")
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
        self.logger.info("GökKalkan Simülasyon Motoru Durduruldu.")

    def _run_loop(self):
        while self.running:
            try:
                start_time = time.time()
                
                # 1. Handle External Commands
                self._handle_commands()
                
                # 2. Physics & Simulation Update
                self.radar.guncelle()
                
                # 3. Defensive Actions (Interceptor & CIWS)
                vurulanlar = self.batarya.guncelle(self.dt, self.radar.aktif_hedefler)
                vurulanlar_ciws = self.ciws.guncelle(self.dt, self.radar.aktif_hedefler)
                
                # Cleanup Destroyed Targets
                all_destroyed = set(vurulanlar + vurulanlar_ciws)
                for tgt in all_destroyed:
                    if tgt in self.radar.aktif_hedefler:
                        self.radar.aktif_hedefler.remove(tgt)
                        self.kalman.hedef_sil(tgt.id)
                        self.logger.info(f"HEDEF İMHA: {tgt.id}")

                # 4. Threat Analysis & Auto-Fire Logic
                current_targets_data = self._process_threats()
                
                # 5. Push Data to UI
                self._sync_ui(current_targets_data)
                
                # EMP Effect Management
                if self.emp_blast_active:
                    self.emp_timer -= self.dt
                    if self.emp_timer <= 0:
                        self.emp_blast_active = False

                # Maintain FPS
                elapsed = time.time() - start_time
                sleep_time = max(0.0, self.dt - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Simülasyon Çevrimi Hatası: {e}")
                time.sleep(1)

    def _handle_commands(self):
        while api.frontend_commands:
            cmd_data = api.frontend_commands.pop(0)
            action = cmd_data.get("action")
            
            if action == "set_stage_1": self.set_stage(1)
            elif action == "set_stage_2": self.set_stage(2)
            elif action == "set_stage_3": self.set_stage(3)
            elif action == "toggle_auto_fire": 
                self.auto_fire = not self.auto_fire
                self.logger.info(f"Otonom Mod: {self.auto_fire}")
            elif action == "manual_fire":
                target_id = cmd_data.get("target_id")
                self.manual_fire(target_id)
            elif action == "trigger_emp":
                self.radar.aktif_hedefler.clear()
                self.emp_blast_active = True
                self.emp_timer = 2.0
            elif action == "trigger_estop": self.radar.e_stop_tetikle(True)
            elif action == "release_estop": self.radar.e_stop_tetikle(False)

    def set_stage(self, stage: int):
        self.current_stage = stage
        self.radar.aktif_hedefler.clear()
        if stage == 1: self.radar.hedef_uret_asama1(); self.auto_fire = False
        elif stage == 2: self.radar.hedef_uret_asama2(); self.auto_fire = True
        elif stage == 3: self.radar.hedef_uret_asama3(); self.auto_fire = True
        self.logger.info(f"Yarışma Aşaması {stage} Aktif Edildi.")

    def manual_fire(self, target_id: str | None = None):
        target = None
        if target_id:
            target = next((h for h in self.radar.aktif_hedefler if h.id == target_id), None)
        else:
            # Fire at closest threat
            threats = [h for h in self.radar.aktif_hedefler if not getattr(h, 'is_dost', False)]
            if threats:
                # Type hint for IDE: threats is list of objects with mesafe and id
                target = min(threats, key=lambda x: getattr(x, 'mesafe', 999.0))
        
        if target:
            try:
                target_id_val = getattr(target, 'id', 'Unknown')
                self.batarya.angaje_ol(target)
                self.logger.info(f"Manuel Ateş: {target_id_val}")
            except Exception as e:
                self.logger.warning(f"Ateşleme Hatası: {e}")

    def _process_threats(self) -> List[Dict]:
        processed = []
        for h in list(self.radar.aktif_hedefler):
            self.kalman.guncelle(h.id, h.x, h.y, h.z)
            tahmin = self.kalman.tahmin_al(h.id)
            
            hiz_kmh = h.toplam_hiz
            tti = utils.hizli_carpisan_zamani(h.mesafe, hiz_kmh)
            cpa = utils.en_yakin_yaklasma_noktasi_hesapla((h.x, h.y, h.z), (h.vx, h.vy, h.vz))
            
            eval = self.siniflandirici.siniflandir(h, cpa, tti)
            
            # Auto-Fire Logic
            if self.auto_fire and eval.oncelik in [TehditOnceligi.KRİTİK, TehditOnceligi.YUKSEK]:
                # Check for existing lock
                if not any(f.hedef.id == h.id for f in self.batarya.aktif_fuzeler):
                    # Check range (Teknofest 2026 Parkur: 0-15m)
                    if h.mesafe < 0.015: 
                        try: self.batarya.angaje_ol(h)
                        except: pass

            data = {
                "id": h.id,
                "x": h.x, "y": h.y, "z": h.z,
                "mesafe": h.mesafe,
                "irtifa": h.z,
                "hiz": hiz_kmh,
                "tti": tti,
                "cpa": cpa,
                "tip": eval.tehdit_tipi.name,
                "oncelik": eval.oncelik.name,
                "is_dost": getattr(h, 'is_dost', False),
                "etiket": getattr(h, 'etiket', "HEDEF"),
                "karar": "ANGAJE" if any(f.hedef.id == h.id for f in self.batarya.aktif_fuzeler) else "TAKİP"
            }
            processed.append(data)
        return processed

    def _sync_ui(self, targets: List[Dict]):
        out_data = {
            "targets": targets,
            "interceptors": [
                {"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id}
                for f in self.batarya.aktif_fuzeler
            ],
            "lasers": self.ciws.aktif_atislar,
            "emp": self.emp_blast_active,
            "stage": self.current_stage,
            "auto_fire": self.auto_fire,
            "ammo": self.batarya.muhimmat
        }
        api.push_data_to_clients(out_data)
