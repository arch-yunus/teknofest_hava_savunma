import os
import sys
import time
import threading
import yaml
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.layout import Layout
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.align import Align
except ImportError:
    print("Hata: 'rich' kütüphanesi yüklenemedi. 'pip install rich' komutunu çalıştırdığınızdan emin olun.")
    sys.exit(1)

from radar import RadarSistemi, HavaDurumu
from interceptor import OnleyiciBatarya, Lazer_CIWS, MuhimmatYokHatasi
from telemetry import TelemetriSistemi
from tehdit_siniflandirici import TehditSiniflandirici, TehditOnceligi
from kalman_takip import KalmanTakipYoneticisi
from api import start_server, push_data_to_clients
import api
import utils

console = Console()

class GokkalkanRunner:
    def __init__(self):
        self.ayarlar = self.ayarları_yukle()
        self.telemetri = TelemetriSistemi(log_dosyasi="logs/gokkalkan_unified.log")
        self.siniflandirici = TehditSiniflandirici()
        self.kalman_yoneticisi = KalmanTakipYoneticisi(dt=1.0)
        self.radar = RadarSistemi(
            menzil_km=20, # Yarışma parkuru (15-20m)
            tespit_olasiligi=0.9
        )
        self.batarya = OnleyiciBatarya(muhimmat=100)
        self.ciws = Lazer_CIWS(menzil_km=2.0)
        
        self.auto_fire = False
        self.current_stage = 0
        self.running = True
        self.last_event = "Sistem Hazır. Bir aşama seçerek başlayın."

    def ayarları_yukle(self, yol: str = "config/ayarlar.yaml") -> Dict[str, Any]:
        if os.path.exists(yol):
            try:
                with open(yol, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except: pass
        return {}

    def get_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="radar_table", ratio=3),
            Layout(name="controls", ratio=1)
        )
        
        # Header
        layout["header"].update(Panel(Align.center("[bold cyan]🛡️ GÖKKALKAN UNIFIED RUNNER v4.1 - TEKNOFEST 2026[/]"), border_style="blue"))
        
        # Radar Table
        table = Table(title=f"CANLI RADAR - AŞAMA {self.current_stage}", expand=True)
        table.add_column("ID", style="cyan")
        table.add_column("Tip", style="magenta")
        table.add_column("Mesafe (m)", justify="right")
        table.add_column("İrtifa (m)", justify="right")
        table.add_column("Bilgi", style="dim")
        
        for h in self.radar.aktif_hedefler:
            dist_m = h.mesafe * 1000
            alt_m = h.z * 1000
            table.add_row(h.id, getattr(h, 'etiket', "Hedef"), f"{dist_m:.1f}", f"{alt_m:.1f}", "Dost" if getattr(h, 'is_dost', False) else "Tehdit")
        
        layout["radar_table"].update(Panel(table, border_style="green"))
        
        # Controls / Status
        status_text = (
            f"Mühimmat: [bold]{self.batarya.muhimmat}[/]\n"
            f"Oto-Atış: {'[bold green]AÇIK' if self.auto_fire else '[bold red]KAPALI'}[/]\n"
            f"Web UI: [underline]http://localhost:8000[/]\n\n"
            f"Son Olay:\n{self.last_event}"
        )
        layout["controls"].update(Panel(status_text, title="Durum", border_style="yellow"))
        
        # Footer
        layout["footer"].update(Panel(Align.center("[b]1-3:[/] Seç Aşama | [b]A:[/] Oto-Atış | [b]F:[/] Ateşle | [b]Q:[/] Çıkış"), border_style="blue"))
        
        return layout

    def main_loop(self):
        # API Server in background thread
        api_thread = threading.Thread(target=start_server, kwargs={"host": "0.0.0.0", "port": 8000}, daemon=True)
        api_thread.start()

        with Live(self.get_layout(), refresh_per_second=2, screen=True) as live:
            while self.running:
                # API Commands
                while api.frontend_commands:
                    cmd = api.frontend_commands.pop(0)
                    self.process_command(cmd.get("action"), cmd.get("target_id"))

                # Simulation Update
                try:
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
                                self.last_event = f"Oto-Ateş: {h.id}"
                            except: pass

                    # Push to Web
                    targets_data = [{"id": h.id, "x": h.x, "y": h.y, "z": h.z, "mesafe": h.mesafe, "is_dost": getattr(h, 'is_dost', False), "etiket": getattr(h, 'etiket', "Hedef")} for h in self.radar.aktif_hedefler]
                    out_data = {"targets": targets_data, "interceptors": [{"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id} for f in self.batarya.aktif_fuzeler], "lasers": self.ciws.aktif_atislar, "stage": self.current_stage}
                    push_data_to_clients(out_data)
                except Exception as e:
                    self.last_event = f"Hata: {str(e)}"

                live.update(self.get_layout())
                time.sleep(1)

    def process_command(self, action: str, target_id: str = None):
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
        self.last_event = f"Aşama {stage} Başlatıldı."
        self.telemetri.olay_kaydet("INFO", self.last_event)

    def manual_fire(self, target_id: str = None):
        target = next((h for h in self.radar.aktif_hedefler if h.id == target_id), None) if target_id else (min((h for h in self.radar.aktif_hedefler if not getattr(h, 'is_dost', False)), key=lambda x: x.mesafe, default=None))
        if target:
            try:
                self.batarya.angaje_ol(target)
                self.last_event = f"Manuel Ateş: {target.id}"
            except: self.last_event = "Mühimmat Bitti!"
        else: self.last_event = "Uygun Hedef Yok!"

if __name__ == "__main__":
    runner = GokkalkanRunner()
    
    # Run loop in background
    loop_thread = threading.Thread(target=runner.main_loop, daemon=True)
    loop_thread.start()
    
    # Use a simpler non-Live input handling logic to avoid terminal fighting
    try:
        while runner.running:
            # We don't use Prompt.ask here because it will fight with the Live display
            # Instead, we just wait for raw input if possible, but reading raw input on Windows is tricky without msvcrt
            # Let's use a simple input() and tell the user it will pause the display
            cmd = console.input("").upper()
            if cmd == "1": runner.set_stage(1)
            elif cmd == "2": runner.set_stage(2)
            elif cmd == "3": runner.set_stage(3)
            elif cmd == "A": runner.auto_fire = not runner.auto_fire
            elif cmd == "F": runner.manual_fire()
            elif cmd == "Q": runner.running = False; break
    except KeyboardInterrupt:
        runner.running = False
    
    console.print("[bold yellow]Kapatılıyor...[/]")
