import random
import math
from typing import List, Any
from enum import Enum

class HavaDurumu(Enum):
    """Hava durumu durumlarını temsil eder."""
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

        # EH Özellikleri
        self.is_jammer = is_jammer
        self.is_ghost = is_ghost
        
        # ARM ve Chaff
        self.is_arm = False  # Anti-Radyasyon Füzesi
        self.has_fired_arm = False
        self.chaff_deployed = False

        # Hipersonik (Mach 5+)
        self.is_hypersonic = False
        self.heat_signature = 1.0 # Hipersonik hedeflerde sürtünme kaynaklı yüksek ısı

        # TEKNOFEST 2026 Özel İsterler
        self.is_dost = False # Dost/Düşman ayrımı
        self.etiket = "Bilinmeyen" # F16, Helikopter, Mini IHA, Balistik Fuze
        self.dondu = False # E-Stop için hareket durdurma bayrağı

        # Manevra ve TWR (Threat Warning Receiver)
        self.is_maneuvering = False
        self.maneuver_timer = 0.0
        self.chaff_cooldown = 0.0

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
                cohesion_x += diger.x
                cohesion_y += diger.y
                cohesion_z += diger.z
                
                align_vx += diger.vx
                align_vy += diger.vy
                align_vz += diger.vz
                
                if mesafe < ayrilma_mesafesi:
                    sep_x -= (dx / mesafe)
                    sep_y -= (dy / mesafe)
                    sep_z -= (dz / mesafe)
                    
        if komsular > 0:
            cohesion_x /= komsular
            cohesion_y /= komsular
            cohesion_z /= komsular
            
            cx = cohesion_x - self.x
            cy = cohesion_y - self.y
            cz = cohesion_z - self.z
            
            align_vx /= komsular
            align_vy /= komsular
            align_vz /= komsular
            
            w_c = 0.01  # Cohesion weight
            w_a = 0.05  # Alignment weight
            w_s = 0.1   # Separation weight
            
            self.vx += (cx * w_c) + ((align_vx - self.vx) * w_a) + (sep_x * w_s)
            self.vy += (cy * w_c) + ((align_vy - self.vy) * w_a) + (sep_y * w_s)
            self.vz += (cz * w_c) + ((align_vz - self.vz) * w_a) + (sep_z * w_s)
            
            max_hiz_kmps = 600 / 3600.0 # max 600 km/h
            hiz_mag = math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)
            if hiz_mag > max_hiz_kmps:
                self.vx = (self.vx / hiz_mag) * max_hiz_kmps
                self.vy = (self.vy / hiz_mag) * max_hiz_kmps
                self.vz = (self.vz / hiz_mag) * max_hiz_kmps

    def get_instant_rcs(self) -> float:
        """Swerling modellerine göre anlık RCS dalgalanması hesaplar."""
        if self.swerling_type == 1:
            return -self.rcs_base * math.log(max(random.random(), 1e-6))
        else:
            return self.rcs_base * random.gammavariate(2, 0.5)

    def detect_and_evade(self, interceptors: List[Any], dt: float):
        """Gelen füzeleri tespit eder (TWR) ve kaçınma manevrası yapar."""
        if self.dondu or self.is_ghost: return
        
        detected_missile = None
        min_missile_dist = 15.0
        
        for f in interceptors:
            if not f.aktif: continue
            dist = math.sqrt((f.x - self.x)**2 + (f.y - self.y)**2 + (f.z - self.z)**2)
            if dist < min_missile_dist:
                min_missile_dist = dist
                detected_missile = f
        
        if detected_missile:
            if min_missile_dist < 8.0 and self.chaff_cooldown <= 0:
                self.chaff_deployed = True
                self.chaff_cooldown = 10.0
                
            self.is_maneuvering = True
            m_dx = detected_missile.x - self.x
            m_dy = detected_missile.y - self.y
            m_dz = detected_missile.z - self.z
            m_len = math.sqrt(m_dx**2 + m_dy**2 + m_dz**2)
            
            if m_len > 0:
                evade_vx = -m_dy / m_len
                evade_vy = m_dx / m_len
                maneuver_strength = 0.15
                self.vx += evade_vx * maneuver_strength
                self.vy += evade_vy * maneuver_strength
                if self.z > 2.0:
                    self.vz -= 0.05
        else:
            self.is_maneuvering = False
            
        if self.chaff_cooldown > 0: self.chaff_cooldown -= dt
        if self.chaff_deployed and self.chaff_cooldown < 8.0: 
            self.chaff_deployed = False
