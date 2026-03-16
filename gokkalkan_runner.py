import os
import sys
import time
import threading
import yaml
import logging
from typing import Dict, Any

# Add src to PATH for IDE and runtime resolution
import os
import sys
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(ROOT_DIR, 'src'))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from rich.live import Live
except ImportError:
    print("Hata: 'rich' kütüphanesi eksik. 'pip install rich' çalıştırın.")
    sys.exit(1)

from src.radar import RadarSistemi
from src.interceptor import OnleyiciBatarya, Lazer_CIWS
from src.telemetry import TelemetriSistemi
import src.api as api
from src.api import start_server, push_data_to_clients

console = Console()

class GokkalkanRunner:
    def __init__(self):
        self.ayarlar = self.ayarları_yukle()
        self.telemetri = TelemetriSistemi(log_dosyasi="logs/gokkalkan_unified.log")
        self.radar = RadarSistemi(menzil_km=20, tespit_olasiligi=0.9)
        self.batarya = OnleyiciBatarya(muhimmat=100)
        self.ciws = Lazer_CIWS(menzil_km=2.0)
        
        self.auto_fire = False
        self.current_stage = 0
        self.running = True
        self.last_event = "Sistem Hazır. Başlamak için terminale '1', '2' veya '3' yazıp Enter'a basın."

    def ayarları_yukle(self, yol: str = "config/ayarlar.yaml") -> Dict[str, Any]:
        if os.path.exists(yol):
            try:
                with open(yol, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except: pass
        return {}

    def generate_dashboard(self) -> Panel:
        table = Table(title=f"HAVA SAVUNMA RADARI - AŞAMA {self.current_stage}", expand=True)
        table.add_column("ID", style="cyan")
        table.add_column("Tip", style="magenta")
        table.add_column("Mesafe(m)", justify="right")
        table.add_column("İrtifa(m)", justify="right")
        table.add_column("Bilgi", style="dim")
        
        for h in self.radar.aktif_hedefler:
            dist_m = h.mesafe * 1000
            alt_m = h.z * 1000
            table.add_row(h.id, getattr(h, 'etiket', "Hedef"), f"{dist_m:.1f}", f"{alt_m:.1f}", "Dost" if getattr(h, 'is_dost', False) else "Tehdit")
        
        status = (
            f"[bold]Mühimmat:[/] {self.batarya.muhimmat} | "
            f"[bold]Oto-Atış:[/] {'[green]AKTİF' if self.auto_fire else '[red]PASİF'}\n"
            f"[bold]Web UI:[/] [blue]http://localhost:8000[/]\n"
            f"[bold]Son Olay:[/] {self.last_event}"
        )
        
        main_content = Table.grid(expand=True)
        main_content.add_row(table)
        main_content.add_row(Panel(status, border_style="yellow"))
        main_content.add_row(Align.center("[b]1-3:[/] Seç Aşama | [b]A:[/] Oto-Atış | [b]F:[/] Ateşle | [b]Q:[/] Çıkış"))
        
        return Panel(main_content, title="[bold cyan]🛡️ GÖKKALKAN KONTROL MERKEZİ[/]", border_style="blue")

    def run(self):
        # Start API in background thread
        threading.Thread(target=start_server, kwargs={"host": "0.0.0.0", "port": 8000}, daemon=True).start()
        
        # Start input listener thread
        threading.Thread(target=self.input_handler, daemon=True).start()

        # Simple non-screen Live display for maximum compatibility
        with Live(self.generate_dashboard(), refresh_per_second=2) as live:
            while self.running:
                try:
                    # Update simulation
                    self.radar.guncelle()
                    self.radar.tara()
                    
                    vurulanlar = self.batarya.guncelle(1.0, self.radar.aktif_hedefler)
                    vurulanlar_ciws = self.ciws.guncelle(1.0, self.radar.aktif_hedefler)
                    
                    for v in set(vurulanlar + vurulanlar_ciws):
                        if v in self.radar.aktif_hedefler:
                            self.radar.aktif_hedefler.remove(v)
                            self.last_event = f"HEDEF VURULDU: {v.id}"
                            self.telemetri.olay_kaydet("SUCCESS", self.last_event)

                    if self.auto_fire:
                        for h in self.radar.aktif_hedefler:
                            if getattr(h, 'is_dost', False): continue
                            if any(f.hedef.id == h.id for f in self.batarya.aktif_fuzeler): continue
                            try:
                                self.batarya.angaje_ol(h)
                                self.last_event = f"Otomatik Ateşlendi: {h.id}"
                            except: pass

                    # API Sync
                    targets_data = [{"id": h.id, "x": h.x, "y": h.y, "z": h.z, "mesafe": h.mesafe, "is_dost": getattr(h, 'is_dost', False), "etiket": getattr(h, 'etiket', "Hedef")} for h in self.radar.aktif_hedefler]
                    out_data = {"targets": targets_data, "interceptors": [{"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id} for f in self.batarya.aktif_fuzeler], "lasers": self.ciws.aktif_atislar, "stage": self.current_stage}
                    push_data_to_clients(out_data)
                    
                    # Remote commands from Web UI
                    while api.frontend_commands:
                        cmd = api.frontend_commands.pop(0)
                        self.process_command(cmd.get("action"))

                except Exception as e:
                    self.last_event = f"Simülasyon Hatası: {str(e)}"
                
                live.update(self.generate_dashboard())
                time.sleep(1)

    def input_handler(self):
        while self.running:
            try:
                cmd = input().upper().strip()
                if cmd == '1': self.set_stage(1)
                elif cmd == '2': self.set_stage(2)
                elif cmd == '3': self.set_stage(3)
                elif cmd == 'A': self.auto_fire = not self.auto_fire; self.last_event = f"Oto-Atış: {self.auto_fire}"
                elif cmd == 'F': self.manual_fire()
                elif cmd == 'Q': self.running = False; os._exit(0)
            except EOFError: break
            except: pass

    def set_stage(self, stage: int):
        self.current_stage = stage
        if stage == 1: self.radar.hedef_uret_asama1(); self.auto_fire = False
        elif stage == 2: self.radar.hedef_uret_asama2(); self.auto_fire = True
        elif stage == 3: self.radar.hedef_uret_asama3(); self.auto_fire = True
        self.last_event = f"Aşama {stage} Aktif."

    def manual_fire(self):
        # Type safe search for targets
        threats = [h for h in self.radar.aktif_hedefler if not getattr(h, 'is_dost', False)]
        target = min(threats, key=lambda x: getattr(x, 'mesafe', 999.0), default=None)
        if target:
            target_id_val = getattr(target, 'id', 'Unknown')
            try:
                self.batarya.angaje_ol(target)
                self.last_event = f"Manuel Ateş: {target_id_val}"
            except: self.last_event = "Mühimmat Bitti!"
        else: self.last_event = "Uygun Tehdit Yok."

    def process_command(self, action: str):
        if "set_stage" in action: self.set_stage(int(action[-1]))
        elif action == "toggle_auto_fire": self.auto_fire = not self.auto_fire

if __name__ == "__main__":
    try:
        runner = GokkalkanRunner()
        runner.run()
    except KeyboardInterrupt:
        os._exit(0)
    except Exception as e:
        print(f"\n[FİTAL HATA]: {str(e)}")
        input("Kapatmak için Enter'a basın...")
