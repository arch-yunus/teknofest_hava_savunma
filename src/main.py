import time
import sys
import yaml
import os
from typing import Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from radar import RadarSistemi, Hedef
from interceptor import OnleyiciBatarya, MuhimmatYokHatasi, Lazer_CIWS
from telemetry import TelemetriSistemi
from tehdit_siniflandirici import TehditSiniflandirici, TehditOnceligi
from kalman_takip import KalmanTakipYoneticisi
import utils
from api import start_server, push_data_to_clients
import threading

console = Console()

def ayarları_yukle(yol: str = "config/ayarlar.yaml") -> Dict[str, Any]:
    try:
        with open(yol, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return {}

def create_status_table(target_data: list, battery_ammo: int) -> Table:
    table = Table(
        title="[bold blue]GÖKKALKAN YZ v3.0 — CANLI TEMAS ÇİZELGESİ[/]",
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

    table.caption = f"[bold white]Mühimmat: {battery_ammo} | Aktif İzci: {target_data.__len__()}[/]"
    return table


def main():
    ayarlar = ayarları_yukle()
    telemetri = TelemetriSistemi(log_dosyasi="logs/gokkalkan_gorev.log")
    siniflandirici = TehditSiniflandirici()
    kalman_yoneticisi = KalmanTakipYoneticisi(dt=1.0)

    radar = RadarSistemi(
        menzil_km=ayarlar.get('radar', {}).get('menzil_km', 200),
        tespit_olasiligi=ayarlar.get('radar', {}).get('tespit_olasiligi', 0.4)
    )

    batarya = OnleyiciBatarya(
        muhimmat=ayarlar.get('batarya', {}).get('muhimmat', 50),
        hassasiyet_ayarlari=ayarlar.get('batarya', {}).get('vurus_hassasiyeti')
    )
    
    ciws = Lazer_CIWS(menzil_km=15.0, atis_hizi=10)

    # Başlangıç Ekranı
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]GÖKKALKAN YZ v3.0 — HAVA SAVUNMA KOMUTA MERKEZİ[/]\n"
        "[dim]Yeni Özellikler: Kalman Takip Filtresi · AI Tehdit Sınıflandırıcı[/]\n"
        "[dim]Mimar: Bahattin Yunus Çetin | Sektör: Karadeniz/Trabzon[/]",
        border_style="bold blue"
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Radar sistemleri senkronize ediliyor...", total=None)
        time.sleep(1)
        progress.add_task(description="Kalman takip filtreleri yükleniyor...", total=None)
        time.sleep(0.8)
        progress.add_task(description="Tehdit sınıflandırma motoru başlatılıyor...", total=None)
        time.sleep(0.8)
        progress.add_task(description="Silah sistemleri kalibre ediliyor...", total=None)
        time.sleep(0.5)
        progress.add_task(description="Gök vatan veritabanı bağlandı.", total=None)
        time.sleep(0.5)

    telemetri.olay_kaydet("INFO", "GÖKKALKAN v3.0 tam kapasite ile başlatıldı.")

    # V4.0 UI Upgrade: Start FastAPI server in a background thread
    api_thread = threading.Thread(target=start_server, kwargs={"host": "0.0.0.0", "port": 8000}, daemon=True)
    api_thread.start()
    console.print("[bold green]Taktik Web Radar Paneli başlatıldı: http://localhost:8000[/]")

    try:
        with Live(create_status_table([], batarya.muhimmat), refresh_per_second=1) as live:
            while True:
                radar.guncelle()
                radar.tara()
                # Füzeleri güncelle (dt = 1 saniye) ve Splash Damage kontrolü yap
                vurulan_hedefler_fuzeler = batarya.guncelle(1.0, radar.aktif_hedefler)
                
                # CIWS (Nokta Savunma) güncelle
                vurulan_hedefler_ciws = ciws.guncelle(1.0, radar.aktif_hedefler)
                
                tum_vurulanlar = set(vurulan_hedefler_fuzeler).union(set(vurulan_hedefler_ciws))
                
                # Vurulan hedefleri radar ve takipten çıkar (Alan hasarı dahil hepsi burada gelir)
                for vh in tum_vurulanlar:
                    if vh in radar.aktif_hedefler:
                        radar.aktif_hedefler.remove(vh)
                        kalman_yoneticisi.hedef_sil(vh.id)
                        
                        # Kinetik mi CIWS mi ayrımı yapalım
                        if vh in vurulan_hedefler_ciws:
                            telemetri.olay_kaydet("SUCCESS", f"CIWS LAZER İLE İMHA: {vh.id}")
                            live.console.print(f"[bold bright_cyan][⚡] CIWS LAZER KİLİDİ: {vh.id} İMHA EDİLDİ![/]")
                        else:
                            telemetri.olay_kaydet("SUCCESS", f"HEDEF İMHA EDİLDİ (Kinetik/Splash): {vh.id}")
                            live.console.print(f"[bold green][*] HEDEF İMHA EDİLDİ: {vh.id}[/]")

                current_targets = []
                for h in list(radar.aktif_hedefler):
                    # Kalman filtresi güncellemesi
                    izci = kalman_yoneticisi.hedef_guncelle(
                        h.id, h.x, h.y, h.z, h.vx, h.vy, h.vz
                    )
                    # Filtrelenmiş konum/hız ile hedefi güncelle (opsiyonel)
                    fx, fy, fz = izci.konum_tahmini()

                    tti = utils.carpisma_suresi_hesapla(h)
                    cpa = utils.en_yakin_nokta_hesapla(h)
                    hiz = h.toplam_hiz

                    # Tehdit değerlendirmesi
                    degerlendirme = siniflandirici.siniflandir(h, cpa, tti)

                    data = {
                        "id":      h.id,
                        "mesafe":  h.mesafe,
                        "irtifa":  fz,
                        "hiz":     hiz,
                        "tti":     tti,
                        "cpa":     cpa,
                        "tip":     degerlendirme.tehdit_tipi.name.replace("_", " "),
                        "oncelik": degerlendirme.oncelik.name,
                        "karar":   degerlendirme.onerilen_karar,
                        "skor":    degerlendirme.tehdit_skoru,
                        "x":       h.x,
                        "y":       h.y
                    }
                    current_targets.append(data)

                    # Otomatik Angajman Mantığı (kritik tehditler için)
                    kritik_cpa = ayarlar.get('tehdit_limitleri', {}).get('kritik_mesafe', 50.0)
                    if (
                        degerlendirme.oncelik == TehditOnceligi.KRİTİK
                        or cpa < kritik_cpa
                    ):
                        # Zaten bu hedefe giden füze var mı kontrolü eklenebilir, şimdilik basit
                        hedefe_fuze_var_mi = any(f.hedef.id == h.id for f in batarya.aktif_fuzeler)
                        if not hedefe_fuze_var_mi:
                            telemetri.olay_kaydet("WARNING", f"KRİTİK TEHDİT: {h.id}", data)
                            live.console.print(
                                f"[bold red]>>> TEHDİT KİLİDİ: {h.id} "
                                f"({degerlendirme.tehdit_tipi.name}) <<<[/]"
                            )
                            try:
                                batarya.angaje_ol(h)
                                live.console.print(f"[bold yellow][!] FÜZE FIRLATILDI -> Hedef: {h.id}[/]")
                            except MuhimmatYokHatasi as e:
                                live.console.print(f"[bold red][X] KRİTİK HATA: {e}[/]")

                live.update(create_status_table(current_targets, batarya.muhimmat))
                
                # Hazırlanan verileri WebSocket üzerinden Web UI'a gönder
                out_data = {
                    "targets": current_targets,
                    "interceptors": [
                        {"id": f.id, "x": f.x, "y": f.y, "z": f.z, "target_id": f.hedef.id}
                        for f in batarya.aktif_fuzeler
                    ],
                    "lasers": ciws.aktif_atislar  # Lazer atış listesi
                }
                push_data_to_clients(out_data)
                
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n[bold red]SİSTEM KAPATILDI.[/] [white]Gök vatan size emanet.[/]")
        sys.exit(0)

if __name__ == "__main__":
    main()
