import random
import math
from typing import List, Dict, Optional, Any

class Hedef:
    """Hava sahasındaki bir hedefi (İHA, Füze, Uçak) temsil eder."""
    def __init__(self, hedef_id: str, x: float, y: float, z: float, vx: float, vy: float, vz: float, rcs: float = 1.0, is_jammer: bool = False, is_ghost: bool = False):
        self.id = hedef_id
        self.x = x  # Doğu-Batı (km)
        self.y = y  # Kuzey-Güney (km)
        self.z = z  # İrtifa (km)
        self.vx = vx # Hız X (km/s)
        self.vy = vy # Hız Y (km/s)
        self.vz = vz # Hız Z (km/s)
        self.rcs_base = rcs # Temel RCS (m^2)
        self.swerling_type = random.choice([1, 3]) # Rastgele Swerling tipi ataması

        # Aşama-5 EH Özellikleri
        self.is_jammer = is_jammer
        self.is_ghost = is_ghost

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
        # Radar gürültüsü ve Swerling modeli ...lerine göre anlık RCS dalgalanması hesaplar."""
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
        
    def hedef_uret(self, max_hedef: int = 5) -> None:
        """Rastgele yeni hedefler (Uçak, Füze, İHA ve EH Jammers) üretir."""
        if len(self.aktif_hedefler) >= max_hedef:
            return

        # Aşama-5 EH Uçağı ihtimali (%15)
        is_jammer = random.random() < 0.15

        aci = random.uniform(0, 2 * math.pi)
        mesafe = random.uniform(self.menzil_km * 0.8, self.menzil_km)
        
        x = mesafe * math.cos(aci)
        y = mesafe * math.sin(aci)
        z = random.uniform(0.1, 15.0) # İrtifa (100m - 15km)
        
        # Hedef merkeze (0,0,0) doğru yönelecek şekilde hız vektörü oluştur
        hedef_hiz_kmh = random.uniform(300, 2500) # 300 km/h - Mach 2+
        if is_jammer:
            hedef_hiz_kmh = random.uniform(700, 900) # EH Uçakları genelde sub-sonic
            
        hiz_mps = hedef_hiz_kmh / 3.6
        
        hiz_x = -x / mesafe * hiz_mps
        hiz_y = -y / mesafe * hiz_mps
        hiz_z = -z / mesafe * hiz_mps * random.uniform(0.1, 0.5) # Hafif alçalma
        
        rcs = random.uniform(0.01, 5.0) # Stealth İHA'dan büyük Kargo uçağına
        if is_jammer:
            rcs = random.uniform(1.0, 3.0)
            
        yeni_hedef = Hedef(
            hedef_id=f"TGT-{random.randint(1000, 9999)}",
            x=x, y=y, z=z,
            vx=hiz_x, vy=hiz_y, vz=hiz_z,
            rcs=rcs,
            is_jammer=is_jammer
        )
        self.aktif_hedefler.append(yeni_hedef)

    def tara(self) -> List[Hedef]:
        """Radar taraması yapar ve tespit edilen hedefleri döndürür."""
        tespit_edilenler = []
        jami_etkisinde_mi = False
        
        # Jammer kontrolü (100km altındaysa radar menzilinde Ghost üretir)
        # Aktif hedefler listesi üzerinde dönerken değişiklik yapmamak için kopyasını al
        veri_havuzu = list(self.aktif_hedefler) 

        # Ghostları temizle (önceki turdan kalanlar veya rastgele kaybolanlar)
        silinecek_ghostlar = [g for g in veri_havuzu if getattr(g, 'is_ghost', False) and random.random() < 0.5]
        for g in silinecek_ghostlar:
            if g in self.aktif_hedefler: # Ensure it's still in the main list
                self.aktif_hedefler.remove(g)
        
        for h in veri_havuzu:
            if h.is_jammer and h.mesafe < 100.0:
                jami_etkisinde_mi = True
                # Jammer, çevresinde rastgele hayalet (Ghost) kopyalar oluşturur
                if random.random() < 0.3: # Her taramada %30 ihtimalle ghost oluştur
                    ghost_x = h.x + random.uniform(-10, 10)
                    ghost_y = h.y + random.uniform(-10, 10)
                    ghost_z = h.z + random.uniform(-2, 2)
                    ghost = Hedef(
                        hedef_id=f"GHOST-{random.randint(100, 999)}",
                        x=ghost_x, y=ghost_y, z=ghost_z,
                        vx=h.vx + random.uniform(-0.05, 0.05), # km/s cinsinden küçük hız farkları
                        vy=h.vy + random.uniform(-0.05, 0.05),
                        vz=0,
                        rcs=h.rcs_base, # Ghost'un RCS'i jammer'ınkiyle aynı olabilir
                        is_ghost=True
                    )
                    # Sadece kısa süreliğine veri havuzuna aktarılır (kalıcı olmaz)
                    # radar.py'deki aktif listeye atmak yerine sadece bu cycle'da taramaya dahil edelim
                    self.aktif_hedefler.append(ghost) # Add to active targets for this scan cycle

        # Tüm aktif hedefleri (gerçek ve ghost) tara
        for hedef in self.aktif_hedefler:
            if hedef.mesafe <= self.menzil_km:
                snr = self._snr_hesapla(hedef)
                if snr >= self.snr_min_db:
                    # Tespit olasılığına göre filtrele
                    if random.random() < self.tespit_olasiligi:
                        tespit_edilenler.append(hedef)
        return tespit_edilenler

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
            
            # V-Formasyonu Oluşturma Geometrisi
            # Lider ortada (0,0), diğerleri (-1, -1), (1, -1), vb. formasyonda
            formasyon_araligi_km = 0.5 # İHA'lar arası mesafe (km)
            
            # Formasyon vektörleri (Lider uçuş yönünde, arkadakiler açılı geride)
            # İlerleyiş vektörünün tersini bul:
            hiz_norm = math.sqrt(ana_vx**2 + ana_vy**2)
            arka_x = -ana_vx / hiz_norm
            arka_y = -ana_vy / hiz_norm
            
            # Dik vektör (kanatlar için)
            yan_x = -arka_y
            yan_y = arka_x
            
            for i in range(adet):
                # V-Formasyon Pozisyonu (0: Lider, 1: Sağ 1, 2: Sol 1, 3: Sağ 2, 4: Sol 2...)
                if i == 0:
                    offset_arka = 0
                    offset_yan = 0
                else:
                    kademesi = (i + 1) // 2
                    yon = 1 if i % 2 == 1 else -1
                    
                    # Geride ve Yanda
                    offset_arka = kademesi * formasyon_araligi_km
                    offset_yan = yon * kademesi * formasyon_araligi_km
                
                # Gerçek uzay pozisyonu
                x = merkez_x + (arka_x * offset_arka) + (yan_x * offset_yan)
                y = merkez_y + (arka_y * offset_arka) + (yan_y * offset_yan)
                z = merkez_z + (random.uniform(-0.1, 0.1)) # İrtifa nispeten aynı
                
                # Koordineli hız (Lider ile birebir aynı hız vektörü, jitter yok)
                vx = ana_vx
                vy = ana_vy
                vz = 0.0 # V-formasyonunda sabit irtifa uçağı
                
                iha = Hedef(
                    hedef_id=f"SWRM-{random.randint(1000, 9999)}",
                    x=x, y=y, z=z, vx=vx, vy=vy, vz=vz, rcs=0.01
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
