import os
import csv
from datetime import datetime
from typing import Any, Dict, List

class AARLogger:
    """
    After Action Review (AAR) Logger.
    Simülasyon olaylarını analiz edilebilir CSV formatında kaydeder.
    """
    def __init__(self, log_dir: str = "logs/aar"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Dosya yolları
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.events_file = os.path.join(self.log_dir, f"events_{timestamp}.csv")
        self.telemetry_file = os.path.join(self.log_dir, f"telemetry_{timestamp}.csv")
        
        # CSV Başlıkları
        self._init_csv(self.events_file, ["timestamp", "sim_time", "event_type", "target_id", "details"])
        self._init_csv(self.telemetry_file, ["timestamp", "sim_time", "active_targets", "interceptors", "system_load"])

    def _init_csv(self, file_path: str, headers: List[str]):
        if not os.path.exists(file_path):
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def log_event(self, sim_time: float, event_type: str, target_id: str, details: str = ""):
        """Önemli bir simülasyon olayını kaydeder (FIRE, HIT, MISS, DETECT)."""
        row = [
            datetime.now().isoformat(),
            round(sim_time, 3),
            event_type,
            target_id,
            details
        ]
        with open(self.events_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def log_telemetry(self, sim_time: float, target_count: int, interceptor_count: int, load: float = 0.0):
        """Sistem durumunu periyodik olarak kaydeder."""
        row = [
            datetime.now().isoformat(),
            round(sim_time, 3),
            target_count,
            interceptor_count,
            round(load, 2)
        ]
        with open(self.telemetry_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def close(self):
        """Logger kaynaklarını temizler (gerekiyorsa)."""
        pass
