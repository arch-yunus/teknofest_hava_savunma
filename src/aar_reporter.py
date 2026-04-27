import os
import csv
from datetime import datetime

class AARReporter:
    """
    After Action Review (AAR) HTML Raporlayıcı.
    CSV formatındaki logları görsel bir HTML raporuna dönüştürür.
    """
    def __init__(self, events_file: str, telemetry_file: str):
        self.events_file = events_file
        self.telemetry_file = telemetry_file
        self.report_dir = "reports/aar"
        os.makedirs(self.report_dir, exist_ok=True)

    def generate_html(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.report_dir, f"report_{timestamp}.html")
        
        # Olayları oku
        events = []
        if os.path.exists(self.events_file):
            with open(self.events_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                events = list(reader)
        
        # İstatistikleri hesapla
        hits = len([e for e in events if e['event_type'] == 'HIT'])
        misses = len([e for e in events if e['event_type'] == 'MISS'])
        total_fired = hits + misses
        accuracy = (hits / total_fired * 100) if total_fired > 0 else 0
        
        html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>ARGUS AAR Raporu - {timestamp}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .header {{ border-left: 5px solid #38bdf8; padding-left: 15px; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #1e293b; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #334155; }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #38bdf8; }}
        .stat-label {{ color: #94a3b8; text-transform: uppercase; font-size: 0.8em; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #334155; color: #38bdf8; }}
        .event-HIT {{ color: #4ade80; font-weight: bold; }}
        .event-MISS {{ color: #f87171; }}
        .event-FIRE {{ color: #fbbf24; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ARGUS After Action Review</h1>
        <p>Operasyon Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
        <p>Birim: VATAN-1 Ana Kontrol Merkezi</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_fired}</div>
            <div class="stat-label">Toplam Atış</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{hits}</div>
            <div class="stat-label">Başarılı Önleme</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{accuracy:.1f}%</div>
            <div class="stat-label">İsabet Oranı</div>
        </div>
    </div>

    <h2>Operasyonel Olay Kaydı</h2>
    <table>
        <thead>
            <tr>
                <th>Sim Süresi (sn)</th>
                <th>Olay Tipi</th>
                <th>Hedef ID</th>
                <th>Detaylar</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for e in events:
            html_content += f"""
            <tr>
                <td>{e['sim_time']}</td>
                <td class="event-{e['event_type']}">{e['event_type']}</td>
                <td>{e['target_id']}</td>
                <td>{e['details']}</td>
            </tr>
            """
            
        html_content += """
        </tbody>
    </table>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return output_path
