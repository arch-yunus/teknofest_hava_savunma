import time
import sys
import os
import threading
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.engine import GokkalkanEngine
import src.api as api

console = Console()

def create_status_table(target_data: list, battery_ammo: int) -> Table:
    table = Table(
        title="[bold blue]GÖKKALKAN YZ v10.0 — CANLI TAKTİK TABLO[/]",
        border_style="blue"
    )

    table.add_column("ID",         style="cyan",      no_wrap=True)
    table.add_column("Mesafe(km)", justify="right",   style="magenta")
    table.add_column("İrtifa(km)", justify="right",   style="green")
    table.add_column("Hız(km/h)",  justify="right",   style="yellow")
    table.add_column("TTI(sn)",    justify="right",   style="red")
    table.add_column("CPA(km)",    justify="right",   style="bold red")
    table.add_column("Tip",        justify="center",  style="white")
    table.add_column("Öncelik",    justify="center")
    table.add_column("Karar",      style="bold")

    ONCELIK_RENK = {
        "KRİTİK":  "[bold red]",
        "YUKSEK":  "[bold yellow]",
        "ORTA":    "[yellow]",
        "DUSUK":   "[dim]",
    }

    for t in target_data:
        oncelik_str = t.get("oncelik", "?")
        renk = ONCELIK_RENK.get(oncelik_str, "")

        table.add_row(
            t['id'],
            f"{t['mesafe']:.2f}",
            f"{t['irtifa']:.2f}",
            f"{t['hiz']:.1f}",
            f"{t['tti']:.1f}" if t['tti'] else "---",
            f"{t['cpa']:.2f}",
            t.get("tip", "?"),
            f"{renk}{oncelik_str}[/]" if renk else oncelik_str,
            t.get("karar", "?"),
        )

    table.caption = f"[bold white]Mühimmat: {battery_ammo} | Aktif İz: {len(target_data)}[/]"
    return table

def main():
    # 1. Initialize Engine and API
    engine = GokkalkanEngine()
    
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]GÖKKALKAN YZ v10.0 — HAVA SAVUNMA KOMUTA MERKEZİ[/]\n"
        "[dim]Merkezi Simülasyon Motoru (Core Engine) Aktif[/]\n"
        "[dim]Mimar: Bahattin Yunus Çetin | Sektör: Gök Vatan[/]",
        border_style="bold blue"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Çekirdek motor yükleniyor...", total=None)
        time.sleep(0.5)
        progress.add_task(description="API servisleri başlatılıyor...", total=None)
        api_thread = threading.Thread(target=api.start_server, kwargs={"host": "0.0.0.0", "port": 8000}, daemon=True)
        api_thread.start()
        time.sleep(0.5)

    console.print("[bold green]Taktik Web Radar Paneli: http://localhost:8000[/]")

    # 2. Main Execution Loop
    try:
        with Live(create_status_table([], engine.batarya.muhimmat), refresh_per_second=2) as live:
            while True:
                # Update Engine (Simulation + API Commands + UI Sync)
                engine.tick()
                
                # Update CLI Dashboard
                telemetry = engine.current_telemetry
                live.update(create_status_table(telemetry.get("targets", []), telemetry.get("ammo", 0)))
                
                # Handle occasional console messages from command events
                if engine.last_event != "Sistem Çekirdeği Başlatıldı.":
                    # Simple hack to avoid repeating the same last_event indefinitely
                    # We could use a queue for events if more complex messaging is needed
                    pass
                
                time.sleep(0.5) # Dashboard refresh rate independent of engine tick if desired

    except KeyboardInterrupt:
        console.print("\n[bold red]SİSTEM KAPATILDI.[/] [white]Gök vatan size emanet.[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
                
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[bold red]SİSTEM KAPATILDI.[/] [white]Gök vatan size emanet.[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
