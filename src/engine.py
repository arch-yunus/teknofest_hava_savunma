import time
import yaml
import os
import threading
import logging
from typing import Dict, Any, List

from src.radar import RadarSistemi, Hedef, HavaDurumu
from src.interceptor import OnleyiciBatarya, MuhimmatYokHatasi, Lazer_CIWS
from src.telemetry import TelemetriSistemi
from src.tehdit_siniflandirici import TehditSiniflandirici, TehditOnceligi
from src.kalman_takip import KalmanTakipYoneticisi
from src.strategic_analyzer import StrategicAnalyzer
import src.utils as utils
import src.api as api

class GokkalkanEngine:
    """GökKalkan Millî Hava Savunma Sistemi - Merkezi Simülasyon Motoru (v10.0)"""
    def __init__(self, config_path: str = "config/ayarlar.yaml"):
        self.ayarlar = self.load_config(config_path)
        self.telemetri = TelemetriSistemi(log_dosyasi="logs/gokkalkan_core.log")
        self.siniflandirici = TehditSiniflandirici()
        self.kalman_yoneticisi = KalmanTakipYoneticisi(dt=1.0)
        
        self.radar = RadarSistemi(
            menzil_km=self.ayarlar.get('radar', {}).get('menzil_km', 200),
            tespit_olasiligi=self.ayarlar.get('radar', {}).get('tespit_olasiligi', 0.4)
        )
        
        self.batarya = OnleyiciBatarya(
            muhimmat=self.ayarlar.get('batarya', {}).get('muhimmat', 50),
            hassasiyet_ayarlari=self.ayarlar.get('batarya', {}).get('vurus_hassasiyeti')
        )
        
        self.ciws = Lazer_CIWS(menzil_km=2.0, atis_hizi=10)
        self.stratejik_analizor = StrategicAnalyzer()
        
        self.auto_fire_enabled = True
        self.current_stage = 0
        self.emp_blast_active = False
        self.emp_timer = 0
        self.last_event = "Sistem Çekirdeği Başlatıldı."
        self.running = False
        self.loop_thread: threading.Thread | None = None
        
        self.current_telemetry: Dict[str, Any] = {}

    def load_config(self, yol: str) -> Dict[str, Any]:
        """Konfigürasyonu yükler ve temel şema doğrulaması yapar."""
        try:
            if os.path.exists(yol):
                with open(yol, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    # Basit Şema Doğrulaması (Production Readiness)
                    required = ['radar', 'batarya']
                    for r in required:
                        if r not in config:
                            self.telemetri.olay_kaydet("WARNING", f"Eksik Konfig: {r} bölümü bulunamadı. Varsayılanlar yüklenecek.")
                            config[r] = {}
                    return config
            else:
                self.telemetri.olay_kaydet("ERROR", f"Konfig dosyası bulunamadı: {yol}")
        except Exception as e:
            self.telemetri.olay_kaydet("CRITICAL", f"Konfig yükleme hatası: {str(e)}")
        return {}

    def start(self):
        """Start the simulation loop in a background thread."""
        if self.running: return
        self.running = True
        self.loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        if self.loop_thread:
            self.loop_thread.start()
        self.telemetri.olay_kaydet("INFO", "GokkalkanEngine simülasyon döngüsü başlatıldı.")

    def stop(self):
        """Stop the simulation loop."""
        self.running = False
        if self.loop_thread:
            self.loop_thread.join(timeout=2.0)
        self.telemetri.olay_kaydet("INFO", "GokkalkanEngine simülasyon döngüsü durduruldu.")

    def _run_loop(self):
        while self.running:
            start_time = time.time()
            self.tick()
            # Maintain 1Hz tick rate for the core engine
            elapsed = time.time() - start_time
            time.sleep(max(0.1, 1.0 - elapsed))

    def tick(self):
        """Perform one simulation step (dt=1.0s) with Robustness."""
        try:
            # 0. Handle External Commands from API
            while api.frontend_commands:
                cmd = api.frontend_commands.pop(0)
                try:
                    self.execute_command(cmd)
                except Exception as e:
                    self.telemetri.olay_kaydet("ERROR", f"Komut İşleme Hatası: {str(e)}")

            # 1. Update Radar and Physical State
            self.radar.guncelle()
            
            # ARM (Anti-Radyasyon) füzesi radarı vurdu mu?
            for h in list(self.radar.aktif_hedefler):
                h_mesafe = getattr(h, 'mesafe', 999.0)
                if getattr(h, 'is_arm', False) and h_mesafe < 0.5:
                    self.last_event = "KRİTİK: RADAR VURULDU (ARM)!"
                    self.telemetri.olay_kaydet("CRITICAL", self.last_event)
                    self.trigger_emp(duration=5)
                    self.radar.emisyon_aktif = False
                    self.radar.aktif_hedefler.remove(h)
                    break
            
            self.radar.tara()

            # 2. Update Weapons systems
            vurulan_hedefler_fuzeler = self.batarya.guncelle(1.0, self.radar.aktif_hedefler)
            vurulan_hedefler_ciws = self.ciws.guncelle(1.0, self.radar.aktif_hedefler)
            
            tum_vurulanlar = set(vurulan_hedefler_fuzeler).union(set(vurulan_hedefler_ciws))
            
            for vh in tum_vurulanlar:
                if vh in self.radar.aktif_hedefler:
                    self.radar.aktif_hedefler.remove(vh)
                    vh_id = getattr(vh, 'id', 'Unknown')
                    self.kalman_yoneticisi.hedef_sil(vh_id)
                    self.telemetri.olay_kaydet("SUCCESS", f"Hedef İmha Edildi: {vh_id}")

            # 3. Target Processing & AI Analysis
            all_target_info = []
            for h in list(self.radar.aktif_hedefler):
                self.kalman_yoneticisi.guncelle(h.id, h.x, h.y, h.z)
                tahmin = self.kalman_yoneticisi.tahmin_al(h.id)
                hiz_km_h = h.toplam_hiz
                tti = utils.hizli_carpisan_zamani(h.mesafe, hiz_km_h)
                cpa_km = utils.en_yakin_yaklasma_noktasi_hesapla((h.x, h.y, h.z), (h.vx, h.vy, h.vz))
                
                degerlendirme = self.siniflandirici.siniflandir(h, cpa_km, tti)
                karar = "İZLENİYOR"
                
                # Engagement Logic
                if self.auto_fire_enabled and degerlendirme.oncelik in [TehditOnceligi.KRİTİK, TehditOnceligi.YUKSEK]:
                    if self.batarya.muhimmat > 0 and h.mesafe > self.ciws.menzil_km:
                        mesafe_m = h.mesafe * 1000
                        menzil_uygun = True
                        if hasattr(h, 'etiket'):
                            if "F16" in h.etiket: menzil_uygun = 10 <= mesafe_m <= 15
                            elif "Helikopter" in h.etiket or "Balistik Fuze" in h.etiket: menzil_uygun = 5 <= mesafe_m <= 15
                            elif "IHA" in h.etiket: menzil_uygun = 0 <= mesafe_m <= 15
                        
                        if menzil_uygun and not any(f.hedef.id == h.id for f in self.batarya.aktif_fuzeler):
                            try:
                                self.batarya.angaje_ol(h)
                                karar = "ANGAJE"
                            except: pass
                
                data = {
                    "id": h.id, "mesafe": h.mesafe, "irtifa": tahmin[2],
                    "hiz": hiz_km_h, "tti": tti, "cpa": cpa_km,
                    "tip": "EH JAMMER" if h.is_jammer else ("GHOST" if h.is_ghost else degerlendirme.tehdit_tipi.name.replace("_", " ")),
                    "oncelik": degerlendirme.oncelik.name, "karar": karar, "skor": degerlendirme.tehdit_skoru,
                    "x": h.x, "y": h.y, "z": h.z, "is_dost": getattr(h, 'is_dost', False),
                    "etiket": getattr(h, 'etiket', "Hedef")
                }
                all_target_info.append(data)

            # 4. Strategic Analysis
            stratejik_rapor = self.stratejik_analizor.analiz_et(all_target_info, self.batarya.muhimmat)
            
            # 5. EMP Effect Update
            if self.emp_blast_active:
                self.emp_timer -= 1
                if self.emp_timer <= 0: self.emp_blast_active = False

            # 6. UI Data Sync
            self.current_telemetry = {
                "targets": all_target_info,
                "interceptors": [{"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id} for f in self.batarya.aktif_fuzeler],
                "lasers": self.ciws.aktif_atislar,
                "jamming": any(t.get("tip") == "GHOST" for t in all_target_info),
                "emp": self.emp_blast_active,
                "weather": self.radar.hava_durumu.name,
                "emission": self.radar.emisyon_aktif,
                "strategic": stratejik_rapor,
                "ammo": self.batarya.muhimmat,
                "auto_fire": self.auto_fire_enabled,
                "stage": self.current_stage
            }
            api.push_data_to_clients(self.current_telemetry)
        except Exception as e:
            self.telemetri.olay_kaydet("CRITICAL", f"Tick Hatası: {str(e)}")
            self.last_event = "SİSTEM HATASI"

    def execute_command(self, cmd_dict: Dict[str, Any]):
        action = cmd_dict.get("action")
        target_id = cmd_dict.get("target_id")
        
        if action == "force_swarm": 
            self.radar.tara_suru_saldirisi()
            self.telemetri.olay_kaydet("WARNING", "Manuel Komut: Sürü Saldırısı")
        elif action == "force_hypersonic": 
            self.radar.tara_hipersonik_tehdit()
            self.telemetri.olay_kaydet("CRITICAL", "Manuel Komut: Hipersonik Tehdit")
        elif action == "toggle_auto_fire": 
            self.auto_fire_enabled = not self.auto_fire_enabled
            self.telemetri.olay_kaydet("INFO", f"Otonom Mod: {self.auto_fire_enabled}")
        elif action == "trigger_emp": self.trigger_emp()
        elif action == "toggle_weather": 
            self.radar.hava_durumu = HavaDurumu.RAIN if self.radar.hava_durumu == HavaDurumu.CLEAR else HavaDurumu.CLEAR
        elif action == "toggle_radar_emission": self.radar.emisyon_aktif = not self.radar.emisyon_aktif
        elif action == "trigger_estop": self.radar.e_stop_tetikle(True)
        elif action == "release_estop": self.radar.e_stop_tetikle(False)
        elif action == "set_stage_1": self.set_stage(1)
        elif action == "set_stage_2": self.set_stage(2)
        elif action == "set_stage_3": self.set_stage(3)
        elif action == "manual_fire": self.manual_fire(target_id)
        elif action == "toggle_manual_mode": self.auto_fire_enabled = not self.auto_fire_enabled

    def set_stage(self, stage: int):
        self.current_stage = stage
        self.radar.aktif_hedefler.clear()
        if stage == 1: self.radar.hedef_uret_asama1(); self.auto_fire_enabled = False
        elif stage == 2: self.radar.hedef_uret_asama2(); self.auto_fire_enabled = True
        elif stage == 3: self.radar.hedef_uret_asama3(); self.auto_fire_enabled = True
        self.telemetri.olay_kaydet("INFO", f"Yarışma Aşaması {stage} Aktif.")

    def trigger_emp(self, duration: int = 3):
        self.radar.aktif_hedefler.clear()
        self.kalman_yoneticisi = KalmanTakipYoneticisi(dt=1.0)
        self.emp_blast_active = True
        self.emp_timer = duration
        self.telemetri.olay_kaydet("CRITICAL", "EMP Patlaması Tetiklendi.")

    def manual_fire(self, target_id: str | None = None):
        target = None
        if target_id:
            target = next((h for h in self.radar.aktif_hedefler if h.id == target_id), None)
        else:
            threats = [h for h in self.radar.aktif_hedefler if not getattr(h, 'is_dost', False)]
            if threats:
                target = min(threats, key=lambda x: x.mesafe)
        
        if target:
            try:
                self.batarya.angaje_ol(target)
                self.telemetri.olay_kaydet("ACTION", f"Manuel Ateş: {target.id}")
            except Exception as e:
                self.telemetri.olay_kaydet("ERROR", f"Ateşleme Hatası: {e}")
