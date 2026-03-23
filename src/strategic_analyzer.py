import random
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

    def analiz_et(self, hedefler: List[Dict[str, Any]], mühimmat: int) -> Dict[str, Any]:
        """
        Hedef yoğunluğu, mühimmat durumu ve EH faaliyetlerine göre stratejik rapor sunar.
        """
        toplam_hedef = len(hedefler)
        kritik_hedefler = sum(1 for h in hedefler if h.get("oncelik") == "KRİTİK")
        jamming_mevcut = any(h.get("is_jammer") or h.get("is_ghost") for h in hedefler)
        arm_mevcut = any(h.get("is_arm") for h in hedefler)
        
        directive = StrategicDirective.STATUS_QUO
        
        if arm_mevcut:
            directive = StrategicDirective.RADAR_SILENCE
        elif toplam_hedef > 10:
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
            "recommendation": self._get_recommendation(directive, jamming_mevcut)
        }

    def _get_recommendation(self, directive: StrategicDirective, jamming: bool) -> str:
        if directive == StrategicDirective.RADAR_SILENCE:
            return "RADARI KAPATIN VE PASİF TAKİBE GEÇİN."
        if directive == StrategicDirective.SWARM_EMERGENCY:
            return "SÜRÜYÜ DAĞITMAK İÇİN CIWS VE SPLASH DAMAGE ÖNCELİKLENDİRİLDİ."
        if jamming:
            return "BİLİŞSEL ECCM ALGORİTMALARI AKTİF EDİLDİ. GHOST FİLTRESİ %85."
        return "SİSTEM OPTİMAL ÇALIŞIYOR. MANUEL MÜDAHALE GEREKMİYOR."

if __name__ == "__main__":
    # Test
    sa = StrategicAnalyzer()
    print(sa.analiz_et([{"oncelik": "KRİTİK", "is_arm": True}], 50))
