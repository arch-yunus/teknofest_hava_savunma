import time
from typing import Dict, Any
from radar import Hedef

class SavunmaHatasi(Exception):
    """GökKalkan savunma sistemi için genel hata sınıfı."""
    pass

class MuhimmatYokHatasi(SavunmaHatasi):
    """Mühimmat tükendiğinde fırlatılan hata."""
    pass

class OnleyiciBatarya:
    def __init__(self, muhimmat: int = 10, hassasiyet_ayarlari: Dict[str, float] = None):
        self.muhimmat = muhimmat
        # Varsayılan hassasiyet ayarları
        self.hassasiyet = hassasiyet_ayarlari or {
            "yakin": 0.95,
            "orta": 0.80,
            "uzak": 0.50
        }

    def angaje_ol(self, hedef: Hedef) -> bool:
        """
        Proportional Navigation (PN) algoritması simülasyonu ile angaje olur.
        """
        if self.muhimmat <= 0:
            raise MuhimmatYokHatasi("KRİTİK: Mühimmat kalmadı!")
        
        self.muhimmat -= 1
        
        # PN Parametreleri
        N = 3.0 # Navigasyon sabiti (Navigational Constant)
        V_m = 0.9 # Savunma füzesi hızı (km/s) ~ Mach 2.6
        
        # Hedef kinematik verileri
        R_v = [hedef.x, hedef.y, hedef.z] # Konum vektörü
        V_v = [hedef.vx, hedef.vy, hedef.vz] # Hız vektörü
        
        # Basitleştirilmiş Angajman Geometrisi Analizi
        # Gerçek bir füzeli önleme denkleminde LOS hızı ve kapanma hızı (Closing Velocity) kullanılır.
        # Burada 'vurus_ihtimali'ni bu geometrik zorluğa göre hesaplıyoruz.
        
        mesafe = hedef.mesafe
        kapanma_hizi = - (hedef.x*hedef.vx + hedef.y*hedef.vy + hedef.z*hedef.vz) / max(mesafe, 0.001)
        
        # Hedef çok hızlıysa veya manevra yapıyorsa (ivme varsa) vuruş ihtimali düşer
        # Basitlik için hız bileşeni
        zorluk_faktoru = (hedef.toplam_hiz / 5000.0) + (mesafe / 150.0)
        
        # Navigasyon sabiti N'in başarısı (N optimumda başarı artar)
        hedef_hizi_kmps = hedef.toplam_hiz / 3600.0
        if hedef_hizi_kmps < 0.001:
            basari_payi = 1.0 # Duran hedefi vurmak daha kolaydır
        else:
            basari_payi = (N / 4.0) * (V_m / hedef_hizi_kmps)
        
        import random
        vurus_olasiligi = min(0.98, max(0.1, basari_payi - zorluk_faktoru))
        
        return random.random() < vurus_olasiligi
