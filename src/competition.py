"""
competition.py - Teknofest 2026 Çelikkubbe Yarışma Puanlama ve Görev Yönetimi
Şartname puanlama tablosuna göre skorlama yapar.
"""
import random
from typing import List, Optional

# ---------- Puanlama Sabitleri (Şartnameye göre) ----------
PUAN_ASAMA1_DOĞRU_HEDEF   =  10  # Doğru hedefi doğru sırayla vurma
PUAN_ASAMA1_YANLIS_SIRA   =  -5  # Yanlış sırayla vurma cezası
PUAN_ASAMA2_SURU_ENGEL    =  20  # Sürü hedefini başarıyla durdurma
PUAN_ASAMA3_DUSUK_ALT     =  30  # Alçak irtifa düşman (Mini IHA) imhası
PUAN_ASAMA3_ORTA_ALT      =  40  # Orta irtifa (Helikopter) imhası
PUAN_ASAMA3_YUKSEK_ALT    =  50  # Yüksek irtifada (F16/Balistik) imha
PUAN_DOST_VURMA_CEZASI    = -20  # Dost hedef imha cezası
PUAN_MENZIL_DISI           =  -3  # Menzil dışı ateş cezası


class Stage1Mission:
    """Aşama 1 için rastgele bir 'zarf sırası' oluşturur ve takibini yapar."""

    def __init__(self, target_ids: List[str]):
        # PDF: "Zarf içinde 4 hedefin sırası verilecek"
        self.sequence: List[str] = list(target_ids)
        random.shuffle(self.sequence)
        self.current_index: int = 0
        self.completed: bool = False

    @property
    def next_target(self) -> Optional[str]:
        if self.current_index < len(self.sequence):
            return self.sequence[self.current_index]
        return None

    def advance(self):
        self.current_index += 1
        if self.current_index >= len(self.sequence):
            self.completed = True

    def get_objectives(self) -> List[dict]:
        """UI'a göndermek için sıralı görev listesi."""
        objs = []
        for i, tid in enumerate(self.sequence):
            status = "completed" if i < self.current_index else \
                     "active" if i == self.current_index else "pending"
            objs.append({"order": i + 1, "target_id": tid, "status": status})
        return objs


class ScoringManager:
    """Tüm yarışma boyunca puanı, isabetleri ve ıskalamaları takip eder."""

    def __init__(self):
        self.total_score: int = 0
        self.hits: int = 0
        self.misses: int = 0
        self.penalties: int = 0
        self.friendly_fire: int = 0
        self.events: List[dict] = []  # Son olaylar (UI'da gösterilir)

    def add_score(self, amount: int, reason: str):
        self.total_score += amount
        if amount > 0:
            self.hits += 1
        elif amount < 0:
            self.penalties += 1
        self.events.insert(0, {"delta": amount, "reason": reason})
        if len(self.events) > 10:
            self.events.pop()

    def register_friendly_fire(self):
        self.friendly_fire += 1
        self.add_score(PUAN_DOST_VURMA_CEZASI, "DOST İMHA! Ceza")

    def register_wrong_order(self):
        self.add_score(PUAN_ASAMA1_YANLIS_SIRA, "Yanlış Sıra! Ceza")

    def register_out_of_range(self):
        self.add_score(PUAN_MENZIL_DISI, "Menzil Dışı Atış")

    def hit_stage1(self):
        self.add_score(PUAN_ASAMA1_DOĞRU_HEDEF, "Aşama-1 İsabet")

    def hit_stage2(self):
        self.add_score(PUAN_ASAMA2_SURU_ENGEL, "Aşama-2 Sürü Engel")

    def hit_stage3(self, etiket: str):
        if "IHA" in etiket or "Kamikazes" in etiket:
            self.add_score(PUAN_ASAMA3_DUSUK_ALT, "Aşama-3 Mini İHA")
        elif "Helikopter" in etiket:
            self.add_score(PUAN_ASAMA3_ORTA_ALT, "Aşama-3 Helikopter")
        else:
            self.add_score(PUAN_ASAMA3_YUKSEK_ALT, f"Aşama-3 {etiket}")

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "hits": self.hits,
            "misses": self.misses,
            "penalties": self.penalties,
            "friendly_fire": self.friendly_fire,
            "events": self.events[:5],  # Son 5 olay
        }
