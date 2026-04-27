import time
import sys
import os
import threading
from rich.console import Console
from rich.table import Table
from rich.live import Live

from src.engine import ArgusEngine
import src.api as api

console = Console()

class ArgusRunner:
    """ARGUS CLI Simulation Runner - Unified Engine Client"""
    def __init__(self):
        self.engine = ArgusEngine()
        self.console = console

    def create_table(self, targets: list, ammo: int) -> Table:
        table = Table(title="[bold magenta]ARGUS CLI RUNNER — TAKTİK VERİ[/]")
        table.add_column("ID", style="cyan")
        table.add_column("Mesafe", justify="right")
        table.add_column("Hız", justify="right")
        table.add_column("Tip", justify="center")
        table.add_column("Durum", style="bold")

        for t in targets:
            table.add_row(
                t['id'],
                f"{t['mesafe']:.2f}km",
                f"{t['hiz']:.0f}km/h",
                t['tip'],
                t['karar']
            )
        table.caption = f"Mühimmat: {ammo}"
        return table

    def run(self):
        # Start API for monitoring even in CLI mode (using different port to avoid conflict if main.py is also running)
        api_thread = threading.Thread(target=api.start_server, kwargs={"port": 8001}, daemon=True)
        api_thread.start()
        
        self.console.print("[bold green]Runner Başlatıldı. API Port: 8001[/]")
        self.console.print("[dim]Bu istemci merkezi ArgusEngine çekirdeğini kullanmaktadır.[/]")
        
        try:
            with Live(self.create_table([], 0), refresh_per_second=2) as live:
                while True:
                    # Simulation Step
                    self.engine.tick()
                    
                    # Dashboard Update
                    telemetry = self.engine.current_telemetry
                    live.update(self.create_table(telemetry.get("targets", []), telemetry.get("ammo", 0)))
                    
                    time.sleep(0.5)
        except KeyboardInterrupt:
            self.console.print("\n[bold red]Runner Durduruldu.[/]")

if __name__ == "__main__":
    runner = ArgusRunner()
    runner.run()

if __name__ == "__main__":
    runner = ArgusRunner()
    runner.run()
