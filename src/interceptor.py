import time
import math
from typing import Dict, Any, List, Optional
from radar import Hedef

class SavunmaHatasi(Exception):
    """GökKalkan savunma sistemi için genel hata sınıfı."""
    pass

class MuhimmatYokHatasi(SavunmaHatasi):
    """Mühimmat tükendiğinde fırlatılan hata."""
    pass

class OnleyiciFuze:
    """Gerçek zamanlı uçan füzeyi temsil eder."""
    def __init__(self, id: str, hedef: Hedef, baslangic_x: float = 0, baslangic_y: float = 0, baslangic_z: float = 0):
        self.id = id
        self.hedef = hedef
        self.x = baslangic_x
        self.y = baslangic_y
        self.z = baslangic_z
        self.hiz_km_s = 0.9 # Savunma füzesi hızı ~ Mach 2.6
        self.vurus_mesafesi = 0.5 # Hedefi yok sayma yarıçapı (km)
        self.aktif = True
        self.vurdu = False

    def guncelle(self, dt: float):
        if not self.aktif or self.hedef is None:
            return

        # Hedefe olan vektör
        dx = self.hedef.x - self.x
        dy = self.hedef.y - self.y
        dz = self.hedef.z - self.z
        mesafe = math.sqrt(dx**2 + dy**2 + dz**2)

        if mesafe <= self.vurus_mesafesi:
            self.vurdu = True
            self.aktif = False
            return

        # Proportional Navigation (Basitleştirilmiş Gözlem Hattı Takibi)
        # Sadece doğrusal yönelimle (Pure Pursuit) hızı vektörlendiriyoruz:
        nx = dx / mesafe
        ny = dy / mesafe
        nz = dz / mesafe

        self.x += nx * self.hiz_km_s * dt
        self.y += ny * self.hiz_km_s * dt
        self.z += nz * self.hiz_km_s * dt


class OnleyiciBatarya:
    def __init__(self, muhimmat: int = 10, hassasiyet_ayarlari: Dict[str, float] = None):
        self.muhimmat = muhimmat
        self.aktif_fuzeler: List[OnleyiciFuze] = []
        self.fuze_sayaci = 0

    def angaje_ol(self, hedef: Hedef) -> bool:
        """Kinetik bir önleyici füze fırlatır."""
        if self.muhimmat <= 0:
            raise MuhimmatYokHatasi("KRİTİK: Mühimmat kalmadı!")
        
        self.muhimmat -= 1
        self.fuze_sayaci += 1
        yeni_fuze = OnleyiciFuze(f"INT-{self.fuze_sayaci}", hedef)
        self.aktif_fuzeler.append(yeni_fuze)
        
        # Anında vuruş sonucu dönmüyoruz, füze uçarken takip edilecek
        return True 
    
    def guncelle(self, dt: float) -> List[Hedef]:
        """Tüm füzeleri günceller ve vurulan hedefleri döndürür."""
        vurulan_hedefler = []
        silinecek_fuzeler = []
        
        for fuze in self.aktif_fuzeler:
            fuze.guncelle(dt)
            if fuze.vurdu:
                vurulan_hedefler.append(fuze.hedef)
                silinecek_fuzeler.append(fuze)
        
        for f in silinecek_fuzeler:
            self.aktif_fuzeler.remove(f)
            
        return vurulan_hedefler
