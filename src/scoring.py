from typing import List, Dict, Any
from src.models import Hedef

class TeknofestScorer:
    """Teknofest 2026 Çelikkubbe Yarışması Puanlama Motoru."""
    
    def __init__(self):
        self.total_score = 0
        self.hits = 0
        self.misses = 0
        self.friendly_fire_incidents = 0
        self.ammo_used = 0
        self.stage_scores = {1: 0, 2: 0, 3: 0}

    def reset(self):
        self.total_score = 0
        self.hits = 0
        self.misses = 0
        self.friendly_fire_incidents = 0
        self.ammo_used = 0
        self.stage_scores = {1: 0, 2: 0, 3: 0}

    def record_hit(self, target: Hedef, stage: int):
        """İmha puanı (Hit-to-Kill)."""
        points = 0
        if stage == 1:
            # Aşama 1: Sabit hedefler (5m, 10m, 15m)
            points = 50
        elif stage == 2:
            # Aşama 2: Sürü (0-15m)
            points = 20 # Çok sayıda hedef olduğu için adet puanı düşük
        elif stage == 3:
            # Aşama 3: Katmanlı (Dost/Düşman ayrımı kritik)
            points = 100
        
        self.hits += 1
        self.stage_scores[stage] += points
        self.total_score += points

    def record_friendly_fire(self):
        """Dost ateşi cezası (-500 puan)."""
        self.friendly_fire_incidents += 1
        penalty = 500
        self.total_score -= penalty
        # Minimun score 0 limit? Genelde Teknofest'te puan eksiye düşmez ama kurallar değişebilir.
        self.total_score = max(0, self.total_score)

    def record_miss(self):
        """Iskalama cezası (-10 puan)."""
        self.misses += 1
        self.total_score = max(0, self.total_score - 10)

    def get_report(self) -> Dict[str, Any]:
        """Final raporu ve istatistikleri döndürür."""
        return {
            "total_score": self.total_score,
            "hits": self.hits,
            "misses": self.misses,
            "friendly_fire_count": self.friendly_fire_incidents,
            "stage_breakdown": self.stage_scores,
            "efficiency": (self.hits / (self.hits + self.misses)) if (self.hits + self.misses) > 0 else 0
        }
