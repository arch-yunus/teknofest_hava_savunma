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
        self.hiz_km_s = 1.4 # Savunma füzesi hızı ~ Mach 4.1 (YÜKSEK PERFORMANS)
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
    def __init__(self, muhimmat: int = 10, hassasiyet_ayarlari: Dict[str, float] = None, patlama_yaricapi_km: float = 1.0):
        self.muhimmat = muhimmat
        self.aktif_fuzeler: List[OnleyiciFuze] = []
        self.fuze_sayaci = 0
        self.patlama_yaricapi_km = patlama_yaricapi_km # Alan hasarı yarıçapı

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
    
    def guncelle(self, dt: float, aktif_hedefler: List[Hedef] = None) -> List[Hedef]:
        """Tüm füzeleri günceller ve (Alan Hasarı dahil) vurulan hedefleri döndürür."""
        if aktif_hedefler is None:
            aktif_hedefler = []
            
        vurulan_hedefler = set() # Aynı hedefi iki kere vurmamak için Set
        silinecek_fuzeler = []
        
        for fuze in self.aktif_fuzeler:
            if not fuze.aktif or not fuze.hedef:
                silinecek_fuzeler.append(fuze)
                continue

            # --- TAKTİKSEL ANALİZ (ECM/ECCM) ---
            # Hedef Chaff/Flare bıraktıysa füze kilidi %60 ihtimalle bozulur
            if getattr(fuze.hedef, 'chaff_deployed', False):
                import random
                if random.random() < 0.6:
                    fuze.hedef = None
                    fuze.aktif = False
                    continue

            # Hedef manevra yapıyorsa (High-G Turn), vuruş ihtimali düşer
            is_maneuvering = getattr(fuze.hedef, 'is_maneuvering', False)
            
            fuze.guncelle(dt)
            
            if fuze.vurdu:
                # Hedef manevra yapıyorsa vuruş şansı %70'e düşer (Kinetik limitler)
                import random
                p_k = 0.7 if is_maneuvering else 0.95
                
                if random.random() < p_k:
                    vurulan_hedefler.add(fuze.hedef)
                    # --- BLAST SPLASH DAMAGE (Parça Tesirli Savaş Başlığı) ---
                    px, py, pz = fuze.x, fuze.y, fuze.z
                    for diger_hedef in aktif_hedefler:
                        if diger_hedef == fuze.hedef: continue
                        mesaf_karesi = (diger_hedef.x - px)**2 + (diger_hedef.y - py)**2 + (diger_hedef.z - pz)**2
                        if mesaf_karesi <= (self.patlama_yaricapi_km ** 2):
                            vurulan_hedefler.add(diger_hedef)
                
                silinecek_fuzeler.append(fuze)
            elif not fuze.aktif:
                silinecek_fuzeler.append(fuze)
        
        for f in set(silinecek_fuzeler):
            if f in self.aktif_fuzeler:
                self.aktif_fuzeler.remove(f)
            
        return list(vurulan_hedefler)

class Lazer_CIWS:
    """Yakın Alan Savunma Sistemi (Close-In Weapon System) 
    15km altındaki kritik hedefleri doğrudan enerji silahı ile anında vurur.
    """
    def __init__(self, menzil_km: float = 15.0, atis_hizi: int = 5):
        self.menzil_km = menzil_km
        self.atis_hizi = atis_hizi # Saniyedeki maksimum hedef vurma sayısı
        self.aktif_atislar = [] # Son saniyedeki CIWS atışlarının listesi [hedefler]
        
    def guncelle(self, dt: float, aktif_hedefler: List[Hedef]) -> List[Hedef]:
        """İç çembere girenleri anında lazerle avlar."""
        vurulanlar = set()
        self.aktif_atislar.clear()
        
        ates_sayisi = 0
        
        for hedef in aktif_hedefler:
            if ates_sayisi >= self.atis_hizi:
                break
                
            if hedef.mesafe <= self.menzil_km:
                vurulanlar.add(hedef)
                self.aktif_atislar.append({
                    "id": hedef.id, 
                    "x": hedef.x, 
                    "y": hedef.y, 
                    "z": hedef.z
                })
                ates_sayisi += 1
                
        return list(vurulanlar)
