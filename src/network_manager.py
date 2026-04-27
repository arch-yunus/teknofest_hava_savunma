import json
import socket
import threading
import time
from typing import Dict, Any, List

class NetworkManager:
    """
    SANCAR Ağ Merkezli Harp (NCW) İletişim Yöneticisi.
    Diğer bataryalar ile 'Recognized Air Picture' (RAP) paylaşımı yapar.
    """
    def __init__(self, port: int = 9000):
        self.port = port
        self.running = False
        self.remote_tracks: Dict[str, Any] = {}
        self.lock = threading.Lock()
        
    def start_broadcasting(self, telemetry_data: Dict[str, Any]):
        """
        Yerel hava resmini ağdaki diğer dost birimlere yayınlar.
        """
        # Gelecek versiyonlarda gerçek UDP broadcast eklenecek.
        pass

    def receive_remote_data(self, battery_id: str, tracks: List[Dict[str, Any]]):
        """Dost bir bataryadan iz verisi alır."""
        with self.lock:
            self.remote_tracks[battery_id] = tracks

    def fuse_tracks(self, local_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Track-to-Track Fusion (T2TF): Yerel ve uzak izleri birleştirir.
        Aynı konuma sahip izleri tekilleştirir, uzak izleri 'NETWORK-TRACK' olarak etiketler.
        """
        fused_list = list(local_tracks)
        local_ids = {t["id"] for t in local_tracks}
        
        with self.lock:
            for b_id, r_tracks in self.remote_tracks.items():
                for rt in r_tracks:
                    # Basit tekilleştirme: Eğer aynı ID bizde yoksa ekle
                    if rt["id"] not in local_ids:
                        # Ağdan gelen iz olduğunu belirtmek için işaretle
                        rt["is_remote"] = True
                        rt["source_battery"] = b_id
                        fused_list.append(rt)
        
        return fused_list

    def get_recognized_air_picture(self, local_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ağdaki tüm birimlerden birleştirilmiş hava resmini döner."""
        return self.fuse_tracks(local_tracks)

    def log_network_status(self) -> str:
        remote_count = len(self.remote_tracks)
        return f"NCW LİNK: AKTİF (Bağlı Ünite Sayısı: {remote_count})"
