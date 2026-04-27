import random
import math
from typing import List, Dict, Any
from enum import Enum

class StrategicDirective(Enum):
    STATUS_QUO = "STABİL: STANDART PROSEDÜR"
    CONSERVE_AMMO = "YÜKSEK TASARRUF: SADECE KRİTİK HEDEFLER"
    MAX_INTERCEPTION = "AGRESİF SAVUNMA: TÜM TEHDİTLERE ANGAJMAN"
    RADAR_SILENCE = "RADAR SESSİZLİĞİ: ARM TEHDİDİ TESPİT EDİLDİ"
    SWARM_EMERGENCY = "SÜRÜ ALARMI: ALAN SAVUNMASI ÖNCELİKLİ"

class StrategicAnalyzer:
    """
    Gök-Vatan Stratejik Analiz Merkezi (V10.0)
    Savaş alanındaki genel durumu analiz eder ve üst düzey komuta direktifleri üretir.
    """
    def __init__(self):
        self.last_directive = StrategicDirective.STATUS_QUO
        self.threat_history = []
        self.network_status = {
            "Vatan-1": "CONNECTED",
            "Vatan-2": "CONNECTED",
            "C2_Global": "SYNCHRONIZED"
        }

    def analiz_et(self, hedefler: List[Dict[str, Any]], mühimmat: int, mission_id: str = "DEFAULT", stage: int = 0) -> Dict[str, Any]:
        """
        Hedef yoğunluğu, mühimmat durumu ve EH faaliyetlerine göre stratejik rapor sunar.
        """
        toplam_hedef = len(hedefler)
        kritik_hedefler = sum(1 for h in hedefler if h.get("oncelik") == "KRİTİK")
        jamming_mevcut = any(h.get("is_jammer") or h.get("is_ghost") for h in hedefler)
        arm_mevcut = any(h.get("is_arm") for h in hedefler)
        
        # Sürü Analizi (Swarm Centroid)
        swarm_targets = [h for h in hedefler if "SWRM" in str(h.get("id", ""))]
        centroid = {"x": 0, "y": 0, "z": 0}
        if swarm_targets:
            centroid["x"] = sum(h["x"] for h in swarm_targets) / len(swarm_targets)
            centroid["y"] = sum(h["y"] for h in swarm_targets) / len(swarm_targets)
            centroid["z"] = sum(h["z"] for h in swarm_targets) / len(swarm_targets)

        # Sektör Analizi (Teknofest 3-Kol Yapısı)
        # Sektör 1: 0-120 derece, Sektör 2: 120-240, Sektör 3: 240-360
        sectors = {1: 0, 2: 0, 3: 0}
        for h in hedefler:
            angle = (math.atan2(h["y"], h["x"]) * 180 / math.pi) % 360
            if 0 <= angle < 120: sectors[1] += 1
            elif 120 <= angle < 240: sectors[2] += 1
            else: sectors[3] += 1
        
        active_sector = max(sectors, key=sectors.get) if toplam_hedef > 0 else "YOK"

        directive = StrategicDirective.STATUS_QUO
        
        if arm_mevcut:
            directive = StrategicDirective.RADAR_SILENCE
        elif stage == 2 or toplam_hedef > 8:
            directive = StrategicDirective.SWARM_EMERGENCY
        elif mühimmat < 10 and kritik_hedefler > 0:
            directive = StrategicDirective.CONSERVE_AMMO
        elif kritik_hedefler > 3:
            directive = StrategicDirective.MAX_INTERCEPTION
            
        self.last_directive = directive
        
        # Simüle edilmiş ağ gecikmesi ve veri füzyon skoru
        fusion_score = random.uniform(92, 99.8)
        
        return {
            "directive": directive.value,
            "fusion_score": f"%{fusion_score:.1f}",
            "network": self.network_status,
            "recommendation": self._get_recommendation(directive, jamming_mevcut, stage),
            "swarm_centroid": centroid if swarm_targets else None,
            "hot_sector": active_sector,
            "sector_density": sectors
        }

    def _get_recommendation(self, directive: StrategicDirective, jamming: bool, stage: int) -> str:
        if stage == 1:
            return "AŞAMA-1: DURAN HEDEFLERE ANGAJE OLUN. MENZİL KONTROLÜ AKTİF."
        if stage == 3:
            return "AŞAMA-3: DOST UNSURLARI (IFF) KORUYUN. KATMANLI SAVUNMA AKTİF."
        if directive == StrategicDirective.RADAR_SILENCE:
            return "RADARI KAPATIN VE PASİF TAKİBE GEÇİN."
        if directive == StrategicDirective.SWARM_EMERGENCY:
            return f"SÜRÜYÜ DAĞITMAK İÇİN CIWS ÖNCELİKLENDİRİLDİ. SEKTÖR ODAKLI SAVUNMA."
        if jamming:
            return "BİLİŞSEL ECCM ALGORİTMALARI AKTİF EDİLDİ. GHOST FİLTRESİ %85."
        return "SİSTEM OPTİMAL ÇALIŞIYOR. MANUEL MÜDAHALE GEREKMİYOR."

if __name__ == "__main__":
    # Test
    sa = StrategicAnalyzer()
    print(sa.analiz_et([{"oncelik": "KRİTİK", "is_arm": True}], 50))
