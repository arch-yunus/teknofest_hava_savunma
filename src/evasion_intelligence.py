import math
import random
from typing import Tuple

class EvasionAI:
    """
    Yapay Zeka Tabanlı Kaçınma Manevra Motoru (V10.0)
    Füzelerin önleyicilere karşı akıllı kaçınma yapmasını sağlar.
    """
    def __init__(self, maneuverability: float = 2.0):
        self.maneuverability = maneuverability # G-kapasitesi
        self.maneuver_timer = 0
        self.current_strategy = "NONE"
        self.jink_amplitude = 0.05 # km
        
    def calculate_maneuver(self, pos: Tuple[float, float, float], interceptors: list) -> Tuple[float, float, float]:
        """
        Yaklaşan önleyicilere göre hız vektörüne eklenecek sapmayı hesaplar.
        """
        if not interceptors:
            return 0.0, 0.0, 0.0
            
        # En yakın önleyiciyi bul
        closest_dist = 999.0
        target_int = None
        for f in interceptors:
            # f is a dict from telemetry: {id, x, y, z, target_id}
            dx, dy, dz = f['x'] - pos[0], f['y'] - pos[1], f['z'] - pos[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < closest_dist:
                closest_dist = dist
                target_int = f
                
        # Eğer önleyici çok yakınsa (5km altı), manevra yap
        if closest_dist < 5.0:
            self.maneuver_timer += 1
            # S-Turn / Jinking Manevrası
            freq = 0.5
            amp = self.jink_amplitude * self.maneuverability
            
            # Önleyici yönüne dik kaçış
            offset_x = math.sin(self.maneuver_timer * freq) * amp
            offset_z = math.cos(self.maneuver_timer * freq) * amp
            
            return offset_x, 0.0, offset_z
            
        return 0.0, 0.0, 0.0

    def get_strategy_label(self) -> str:
        if self.maneuver_timer > 0:
            return "EVASIVE: S-TURN"
        return "CRUISING"
