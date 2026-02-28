import random
import math
from typing import List, Dict, Optional, Any

class Hedef:
    """Hava sahasındaki bir hedefi (İHA, Füze, Uçak) temsil eder."""
    def __init__(self, hedef_id: str, x: float, y: float, z: float, vx: float, vy: float, vz: float, rcs: float = 1.0):
        self.id = hedef_id
        self.x = x  # Doğu-Batı (km)
        self.y = y  # Kuzey-Güney (km)
        self.z = z  # İrtifa (km)
        self.vx = vx # Hız X (km/s)
        self.vy = vy # Hız Y (km/s)
        self.vz = vz # Hız Z (km/s)
        self.rcs_base = rcs # Temel RCS (m^2)
        self.swerling_type = random.choice([1, 3]) # Rastgele Swerling tipi ataması

    @property
    def mesafe(self) -> float:
        """Merkeze (Radara) olan öklid mesafesi."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @property
    def toplam_hiz(self) -> float:
        """Hedefin vektörel toplam hızı (km/saat)."""
        hiz_kmps = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
        return hiz_kmps * 3600.0

    def ilerle(self, dt: float = 1.0):
        """Hedefi hız vektörü yönünde dt süresi kadar hareket ettirir."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        if self.z < 0: self.z = 0

    def get_instant_rcs(self) -> float:
        """Swerling modellerine göre anlık RCS dalgalanması hesaplar."""
        if self.swerling_type == 1:
            # Swerling 1: Rayleigh dağılımı (Exponential in Power)
            return -self.rcs_base * math.log(max(random.random(), 1e-6))
        else:
            # Swerling 3: Chi-square 4-DOF
            return self.rcs_base * random.gammavariate(2, 0.5)

class RadarSistemi:
    def __init__(self, menzil_km: float = 150.0, tespit_olasiligi: float = 0.4):
        self.menzil_km = menzil_km
        self.tespit_olasiligi = tespit_olasiligi
        self.aktif_hedefler: List[Hedef] = []

        # İleri Fiziksel Radar Parametreleri (X-Band)
        self.P_t = 50000.0  # Verici Gücü (Watt)
        self.G_db = 45.0    # Anten Kazancı (dB)
        self.f_hz = 9.5e9   # 9.5 GHz X-Band
        self.snr_min_db = 13.0 # Minimum Tespit Eşiği (dB)
        self.L_db = 5.0     # Sistem Kayıpları (dB)

    def _snr_hesapla(self, hedef: Hedef) -> float:
        """Radar Menzil Denklemi ile anlık SNR hesaplar."""
        R = max(hedef.mesafe * 1000.0, 1.0) # Metre cinsinden mesafe
        rcs = hedef.get_instant_rcs()
        c = 3e8
        lam = c / self.f_hz
        G = 10**(self.G_db / 10.0)
        L = 10**(self.L_db / 10.0)
        k_bolt = 1.38e-23
        T = 290.0 # Gürültü sıcaklığı (K)
        B = 1e6   # Bant genişliği (Hz)

        # SNR = (Pt * G^2 * lam^2 * sigma) / ((4pi)^3 * R^4 * k * T * B * L)
        pay = self.P_t * (G**2) * (lam**2) * rcs
        payda = ((4 * math.pi)**3) * (R**4) * k_bolt * T * B * L
        
        snr_linear = pay / payda
        return 10 * math.log10(max(snr_linear, 1e-15))
        
    def tara(self) -> Optional[Hedef]:
        """Radar taraması yapar ve yeni bir hedef tespit edilirse döndürür."""
        if random.random() < self.tespit_olasiligi:
            # Rastgele bir hedef oluştur (Sektör içinde)
            aci = random.uniform(0, 2 * math.pi)
            uzaklik = random.uniform(self.menzil_km * 0.5, self.menzil_km)
            
            x = uzaklik * math.cos(aci)
            y = uzaklik * math.sin(aci)
            z = random.uniform(1.0, 15.0) # 1km - 15km irtifa
            
            # Merkeze doğru yönelmiş hızlar (Basit simülasyon)
            hiz_mag = random.uniform(0.1, 0.6) # km/s
            vx = -x / uzaklik * hiz_mag
            vy = -y / uzaklik * hiz_mag
            vz = random.uniform(-0.01, 0.01)
            
            yeni_hedef = Hedef(
                hedef_id=f"HDF-{random.randint(100, 999)}",
                x=x, y=y, z=z,
                vx=vx, vy=vy, vz=vz,
                rcs=random.choice([0.01, 0.1, 1.0, 5.0, 10.0]) # İHA, Füze, Uçak RCS'leri
            )
            
            # SNR Filtresi Uygula
            if self._snr_hesapla(yeni_hedef) >= self.snr_min_db:
                self.aktif_hedefler.append(yeni_hedef)
                return yeni_hedef
        return None

    def tara_suru_saldirisi(self) -> List[Hedef]:
        """Aynı vektörden gelen 5 ile 12 arasında İHA (Swarm) üretir."""
        if random.random() < (self.tespit_olasiligi * 0.1): # Sürü saldırısı nadirdir
            suru = []
            adet = random.randint(5, 12)
            
            # Ana sürü merkezi
            aci = random.uniform(0, 2 * math.pi)
            uzaklik = random.uniform(self.menzil_km * 0.7, self.menzil_km)
            merkez_x = uzaklik * math.cos(aci)
            merkez_y = uzaklik * math.sin(aci)
            merkez_z = random.uniform(0.5, 3.0) # Sürü alçaktan gelir
            
            # Sürü hızı (hepsi aynı yöne, merkeze doğru)
            hiz_mag = random.uniform(0.15, 0.3)
            ana_vx = -merkez_x / uzaklik * hiz_mag
            ana_vy = -merkez_y / uzaklik * hiz_mag
            
            for i in range(adet):
                # Merkezin etrafında hafif dağılım (Jitter)
                x = merkez_x + random.uniform(-2.0, 2.0)
                y = merkez_y + random.uniform(-2.0, 2.0)
                z = merkez_z + random.uniform(-0.2, 0.2)
                
                # Hızlarda mikro sapmalar
                vx = ana_vx + random.uniform(-0.02, 0.02)
                vy = ana_vy + random.uniform(-0.02, 0.02)
                vz = random.uniform(-0.005, 0.005)
                
                iha = Hedef(
                    hedef_id=f"SWRM-{random.randint(1000, 9999)}",
                    x=x, y=y, z=z, vx=vx, vy=vy, vz=vz
                )
                self.aktif_hedefler.append(iha)
                suru.append(iha)
            return suru
        return []

    def guncelle(self):
        """Tüm hedeflerin konumlarını günceller."""
        for h in self.aktif_hedefler:
            h.ilerle()
            if h.mesafe > self.menzil_km * 1.2: # Menzili çok aşanı sil
                self.aktif_hedefler.remove(h)
