import random
import math
from typing import List, Dict, Optional, Any
from enum import Enum

class HavaDurumu(Enum):
    CLEAR = 0
    RAIN = 1

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
        
        # Aşama-9 ARM ve Chaff
        self.is_arm = False  # Anti-Radyasyon Füzesi
        self.has_fired_arm = False
        self.chaff_deployed = False

        # Aşama-10 Hipersonik (Mach 5+)
        self.is_hypersonic = False
        self.heat_signature = 1.0 # Hipersonik hedeflerde sürtünme kaynaklı yüksek ısı

        # TEKNOFEST 2026 Özel İsterler
        self.is_dost = False # Dost/Düşman ayrımı (Aşama-3)
        self.etiket = "Bilinmeyen" # F16, Helikopter, Mini IHA, Balistik Fuze
        self.dondu = False # E-Stop için hareket durdurma bayrağı

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
        if self.dondu: return # E-Stop aktifse hareket yok
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        if self.z < 0: self.z = 0

    def boids_guncelle(self, suru: List['Hedef'], dt: float):
        """Boids (Flocking) Algoritması: Ayrılma, Hizalanma, Birleşme kuralları."""
        # Yalnızca hedefin is_suru özelliği varsa aktif olacak (basitlik için sürü flag'i eklenebilir veya ID'den kontrol edilebilir)
        if not self.id.startswith("SWRM-"): return
        
        algilama_yaricapi = 2.0 # km
        ayrilma_mesafesi = 0.5 # km
        
        cohesion_x = cohesion_y = cohesion_z = 0.0
        align_vx = align_vy = align_vz = 0.0
        sep_x = sep_y = sep_z = 0.0
        komsular = 0
        
        for diger in suru:
            if diger.id == self.id or not diger.id.startswith("SWRM-"): continue
            
            dx = diger.x - self.x
            dy = diger.y - self.y
            dz = diger.z - self.z
            mesafe = math.sqrt(dx**2 + dy**2 + dz**2)
            
            if 0 < mesafe < algilama_yaricapi:
                komsular += 1
                
                # Cohesion (Birleşme)
                cohesion_x += diger.x
                cohesion_y += diger.y
                cohesion_z += diger.z
                
                # Alignment (Hizalanma)
                align_vx += diger.vx
                align_vy += diger.vy
                align_vz += diger.vz
                
                # Separation (Ayrılma)
                if mesafe < ayrilma_mesafesi:
                    sep_x -= (dx / mesafe)
                    sep_y -= (dy / mesafe)
                    sep_z -= (dz / mesafe)
                    
        if komsular > 0:
            # Ortalamaları al
            cohesion_x /= komsular
            cohesion_y /= komsular
            cohesion_z /= komsular
            
            # Merkeze doğru vektör
            cx = cohesion_x - self.x
            cy = cohesion_y - self.y
            cz = cohesion_z - self.z
            
            align_vx /= komsular
            align_vy /= komsular
            align_vz /= komsular
            
            # Ağırlıklar
            w_c = 0.01  # Cohesion weight
            w_a = 0.05  # Alignment weight
            w_s = 0.1   # Separation weight
            
            self.vx += (cx * w_c) + ((align_vx - self.vx) * w_a) + (sep_x * w_s)
            self.vy += (cy * w_c) + ((align_vy - self.vy) * w_a) + (sep_y * w_s)
            self.vz += (cz * w_c) + ((align_vz - self.vz) * w_a) + (sep_z * w_s)
            
            # Hız limitleme (Sürünün aşırı hızlanmasını önle)
            max_hiz_kmps = 600 / 3600.0 # max 600 km/h
            hiz_mag = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
            if hiz_mag > max_hiz_kmps:
                self.vx = (self.vx / hiz_mag) * max_hiz_kmps
                self.vy = (self.vy / hiz_mag) * max_hiz_kmps
                self.vz = (self.vz / hiz_mag) * max_hiz_kmps

    def get_instant_rcs(self) -> float:
        """Swerling modellerine göre anlık RCS dalgalanması hesaplar."""
        # Radar gürültüsü ve Swerling modellerini içeren basit bir RCS dalgalanma simülasyonu
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
        
        # Aşama 8 & 9 - Çevre Faktörleri ve Taktik Emisyon
        self.hava_durumu = HavaDurumu.CLEAR
        self.emisyon_aktif = True  # Radar yayını yapıyor mu?
        
        # Aşama 10.2 - Clutter ve CFAR Parametreleri
        self.false_alarm_rate = 1e-4 # P_fa (Yanlış alarm olasılığı)
        self.cfar_win_size = 10     # Eğitim hücreleri sayısı
        self.cfar_guard_size = 2    # Koruma hücreleri sayısı
        self.clutter_floor_db = -20 # Yer/Deniz clutter taban seviyesi

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

        # Weather Attenuation (Yağmur/Bulut Zayıflatması)
        attenuation_db_per_km = 0.0
        if self.hava_durumu == HavaDurumu.RAIN:
            # X-Band (9.5GHz) radar için ağır yağmur zayıflatması ~ 0.2 dB/km (tek yön)
            attenuation_db_per_km = 0.4 # Gidiş-Dönüş (Two-way)
            
        total_atten_db = attenuation_db_per_km * (hedef.mesafe)
        
        # Clutter Effect (Alçak irtifada yer yansıması gürültüyü artırır)
        clutter_db = 0.0
        if hedef.z < 1.0: # 1km altı "Low-Level" clutter bölgesi
            clutter_db = (1.0 - hedef.z) * 15.0 # İrtifa azaldıkça clutter artar (max 15dB)

        L_total = L * (10**((total_atten_db + clutter_db) / 10.0)) 

        # SNR = (Pt * G^2 * lam^2 * sigma) / ((4pi)^3 * R^4 * k * T * B * L)
        pay = self.P_t * (G**2) * (lam**2) * rcs
        payda = ((4 * math.pi)**3) * (R**4) * k_bolt * T * B * L_total
        
        snr_linear = pay / payda
        return 10 * math.log10(max(snr_linear, 1e-15))

    def _ca_cfar_test(self, point_snr: float) -> bool:
        """
        Cell-Averaging Constant False Alarm Rate (CA-CFAR) algoritması.
        Gürültü tabanına göre dinamik eşikleme yapar.
        """
        # Eğitim hücreleri simülasyonu (Gerçek radarda dizi (array) üzerinden yapılır)
        # Burada basitleştirilmiş bir model kullanıyoruz.
        noise_samples = [random.gauss(0, 2) for _ in range(self.cfar_win_size)]
        noise_avg = sum([10**(n/10.0) for n in noise_samples]) / self.cfar_win_size
        noise_avg_db = 10 * math.log10(max(noise_avg, 1e-10))
        
        # Alfa eşik katsayısı (P_fa'ya bağlı)
        alpha = self.cfar_win_size * (self.false_alarm_rate**(-1.0/self.cfar_win_size) - 1)
        
        threshold = noise_avg_db + (10 * math.log10(max(alpha, 1.0)))
        return point_snr > threshold
        
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

    def hedef_uret_asama1(self) -> None:
        """TEKNOFEST Aşama-1: Fiziksel Parkur (5m, 10m, 15m) sabit hedefler."""
        self.aktif_hedefler.clear()
        
        hedefler = [
            ("Balistik Fuze", 0.005), # 5m
            ("Helikopter", 0.010),    # 10m
            ("Savas Ucagi (F16)", 0.015), # 15m
            ("Mini/Micro IHA", 0.010)  # 10m (farklı vektör)
        ]
        
        for i, (label, dist) in enumerate(hedefler):
            angle = (i * math.pi / 2) + random.uniform(-0.1, 0.1)
            x = dist * math.cos(angle)
            y = dist * math.sin(angle)
            z = random.uniform(0.001, 0.002) # 1-2 metre yükseklik
            
            # Aşama 1 hedefleri özeldir
            h = Hedef(f"STG1-{i}", x, y, z, 0, 0, 0, rcs=0.5)
            h.etiket = label
            self.aktif_hedefler.append(h)

    def hedef_uret_asama2(self) -> List[Hedef]:
        """TEKNOFEST Aşama-2: Sürü Saldırı (3 koldan, toplam 15 hedef, parkur içi: 0-15m)."""
        self.aktif_hedefler.clear()
        suru = []
        
        # 3 farklı koldan (yön) hedeflerin yaklaşması
        kollar = [0, 2*math.pi/3, 4*math.pi/3]
        labels = ["Balistik Fuze", "Mini/Micro IHA", "Savas Ucagi (F16)"]
        
        for k_idx, angle in enumerate(kollar):
            for i in range(5):  # Her koldan 5 hedef, toplam 15
                dist = 0.015 + (i * 0.002) # 15m'den başlayarak dizili
                x = dist * math.cos(angle + random.uniform(-0.1, 0.1))
                y = dist * math.sin(angle + random.uniform(-0.1, 0.1))
                z = 0.001 + (random.random() * 0.001)
                
                hiz_mps = 0.8 / 1000 # 0.8 m/s -> km/s
                vx = -x / dist * hiz_mps
                vy = -y / dist * hiz_mps
                
                h = Hedef(f"SWRM-{k_idx}-{i}", x, y, z, vx, vy, 0, rcs=0.1)
                h.etiket = labels[k_idx]
                self.aktif_hedefler.append(h)
                suru.append(h)
        return suru

    def hedef_uret_asama3(self) -> None:
        """TEKNOFEST Aşama-3: Katmanlı (1 Düşman, 2 Dost maket). Farklı hız ve irtifalarda hareket ederler."""
        self.aktif_hedefler.clear()
        
        # 1 Düşman Hedef (Rastgele tip: F16, Helikopter, IHA)
        type_choice = random.choice([
            ("Savas Ucagi (F16)", 0.015, 0.005, 1000),      # Yüksek irtifa, hızlı
            ("Helikopter", 0.010, 0.002, 300),              # Orta irtifa, yavaş
            ("Mini/Micro IHA", 0.005, 0.001, 150)           # Alçak irtifa, çok yavaş
        ])
        
        # Düşman
        ang1 = random.uniform(0, 2*math.pi)
        dist_enemy = type_choice[1]
        z_enemy = type_choice[2] # km
        speed_enemy_kmh = type_choice[3]
        
        x1, y1 = dist_enemy * math.cos(ang1), dist_enemy * math.sin(ang1)
        # Merkeze (0,0,0) doğru hız vektörü
        hiz_mps1 = speed_enemy_kmh / 3.6
        vx1 = -x1 / dist_enemy * hiz_mps1 if dist_enemy > 0 else 0
        vy1 = -y1 / dist_enemy * hiz_mps1 if dist_enemy > 0 else 0
        
        h_dusman = Hedef("STG3-ENEMY", x1, y1, z_enemy, vx1, vy1, 0, rcs=0.5)
        h_dusman.etiket = type_choice[0]
        h_dusman.is_dost = False
        self.aktif_hedefler.append(h_dusman)
        
        # 2 Dost Unsur
        for i in range(2):
            ang = ang1 + (i+1) * (math.pi/2)
            dist = random.choice([0.008, 0.012, 0.015])
            z_dost = random.uniform(0.002, 0.006)
            speed_dost_kmh = random.uniform(400, 900)
            
            x, y = dist * math.cos(ang), dist * math.sin(ang)
            hiz_mps_dost = speed_dost_kmh / 3.6
            
            # Dost hedefleri merkeze değilde radar etrafında devriye attıralım (Tanjant Hız)
            tanjant_vx = -y / dist * hiz_mps_dost if dist > 0 else 0
            tanjant_vy = x / dist * hiz_mps_dost if dist > 0 else 0
            
            h_dost = Hedef(f"STG3-FRIEND-{i}", x, y, z_dost, tanjant_vx, tanjant_vy, 0, rcs=0.5)
            h_dost.etiket = random.choice(["F16 (Dost)", "IHA (Dost)"])
            h_dost.is_dost = True
            self.aktif_hedefler.append(h_dost)

    def e_stop_tetikle(self, aktif: bool):
        """Tüm hedefleri dondurur veya çözer."""
        for h in self.aktif_hedefler:
            h.dondu = aktif

    def tara(self) -> List[Hedef]:
        """Radar taraması yapar ve tespit edilen hedefleri döndürür."""
        if not self.emisyon_aktif:
            return [] # Radar sussturulduğunda tamamen kör oluruz

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
                # Yeni: CFAR Eşikleme
                if self._ca_cfar_test(snr):
                    # Tespit olasılığı ve CFAR başarımı
                    if random.random() < self.tespit_olasiligi:
                        tespit_edilenler.append(hedef)
        
        # Aşama 10.2: Yanlış Alarm (False Alarm) Üretimi
        # Nadiren gürültü eşiği geçer ve hayali bir hedef (Clutter Spike) oluşur
        if random.random() < 0.05: # Her taramada %5 ihtimalle false alarm
            fa_x = random.uniform(-self.menzil_km, self.menzil_km)
            fa_y = random.uniform(-self.menzil_km, self.menzil_km)
            fa_z = random.uniform(0, 2.0) # Genelde alçak irtifada (yer clutter)
            fa_target = Hedef(
                f"CLUTTER-{random.randint(10,99)}", fa_x, fa_y, fa_z, 
                random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), 0,
                rcs=0.01, is_ghost=True
            )
            fa_target.etiket = "CLUTTER"
            tespit_edilenler.append(fa_target)
            
        return tespit_edilenler

    def tara_suru_saldirisi(self) -> List[Hedef]:
        """Aynı vektörden gelen 5 ile 12 arasında İHA (Swarm) üretir."""
        if not self.emisyon_aktif: 
            return [] # Radar kapalıyken sürü tespit edilemez/üretim event'i tetiklenmez
            
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
        formasyon_araligi_km = 0.5 
        hiz_norm = math.sqrt(ana_vx**2 + ana_vy**2)
        arka_x = -ana_vx / hiz_norm
        arka_y = -ana_vy / hiz_norm
        yan_x = -arka_y
        yan_y = arka_x
        
        for i in range(adet):
            if i == 0:
                offset_arka = 0
                offset_yan = 0
            else:
                kademesi = (i + 1) // 2
                yon = 1 if i % 2 == 1 else -1
                offset_arka = kademesi * formasyon_araligi_km
                offset_yan = yon * kademesi * formasyon_araligi_km
            
            x = merkez_x + (arka_x * offset_arka) + (yan_x * offset_yan)
            y = merkez_y + (arka_y * offset_arka) + (yan_y * offset_yan)
            z = merkez_z + (random.uniform(-0.1, 0.1))
            
            vx = ana_vx
            vy = ana_vy
            vz = 0.0
            
            iha = Hedef(
                hedef_id=f"SWRM-{random.randint(1000, 9999)}",
                x=x, y=y, z=z, vx=vx, vy=vy, vz=vz, rcs=0.01
            )
            self.aktif_hedefler.append(iha)
            suru.append(iha)
        return suru

    def tara_hipersonik_tehdit(self) -> List[Hedef]:
        """
        TEKNOFEST 2026 / Phase 10: Mach 5+ Hipersonik Tehdit Üretimi.
        Çok yüksek hız, düşük manevra, yüksek ısı izi.
        """
        if not self.emisyon_aktif: return []
        
        # Hipersonik hedefler uzaklardan belirlenir (HGV / HCM)
        aci = random.uniform(0, 2 * math.pi)
        uzaklik = self.menzil_km * 0.95
        x = uzaklik * math.cos(aci)
        y = uzaklik * math.sin(aci)
        z = random.uniform(20.0, 30.0) # Yüksek irtifa (Atmospheric entry)
        
        # Mach 5 - Mach 8 arası hız (1700 m/s - 2700 m/s)
        hiz_mps = random.uniform(1700, 2700)
        
        vx = -(x / uzaklik) * hiz_mps
        vy = -(y / uzaklik) * hiz_mps
        vz = -(z / uzaklik) * hiz_mps * 0.2 # Sığ alçalış
        
        h = Hedef(f"H-SONIC-{random.randint(100, 999)}", x, y, z, vx, vy, vz, rcs=0.2)
        h.is_hypersonic = True
        h.heat_signature = 5.0 + (hiz_mps / 500.0) # Hızla artan termal iz
        h.etiket = "Hipersonik HCM"
        
        self.aktif_hedefler.append(h)
        return [h]

    def guncelle(self):
        """Tüm hedeflerin konumlarını günceller."""
        suru_hedefleri = [h for h in self.aktif_hedefler if h.id.startswith("SWRM-")]
        
        for h in self.aktif_hedefler:
            h.boids_guncelle(suru_hedefleri, 1.0) # Boids alg. (SWRM etiketiyse çalışır)
            
            # ARM Davranışı (Anti-Radyasyon)
            if h.is_arm and getattr(h, 'is_ghost', False) == False:
                if not self.emisyon_aktif:
                    # Radar kapalıysa hedefini kaybeder ve rastgele sapar
                    h.vx += random.uniform(-0.1, 0.1)
                    h.vy += random.uniform(-0.1, 0.1)
                elif h.mesafe < 0.5:
                    # Radar vuruldu! (Main loop'ta yakalanacak)
                    pass
            
            # Jammer uçakları radar açıksa ARM ateşleyebilir
            if h.is_jammer and getattr(h, 'is_ghost', False) == False and not h.has_fired_arm and self.emisyon_aktif:
                if h.mesafe < 120 and random.random() < 0.05: # %5 ihtimalle ARM ateşler
                    h.has_fired_arm = True
                    # Hipersonik ARM füzesi merkeze doğru (Mach 4+)
                    hiz_mps = 1500 / 3.6 
                    vx = -(h.x / h.mesafe) * hiz_mps
                    vy = -(h.y / h.mesafe) * hiz_mps
                    arm = Hedef(
                        hedef_id=f"ARM-{random.randint(100,999)}",
                        x=h.x, y=h.y, z=h.z,
                        vx=vx, vy=vy, vz=0,
                        rcs=0.1
                    )
                    arm.is_arm = True
                    self.aktif_hedefler.append(arm)
            
            h.ilerle(1.0)
            if h.mesafe > self.menzil_km * 1.5: # Menzili çok aşanı sil
                if h in self.aktif_hedefler:
                    self.aktif_hedefler.remove(h)
