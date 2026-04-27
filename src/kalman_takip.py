"""
kalman_takip.py
===============
SANCAR YZ - Kalman Filtresi Tabanlı Hedef Takip Sistemi

Gürültülü radar ölçümlerini filtreler ve hedefin gelecek konumunu tahmin eder.
Doğrusal hareket modeli varsayımıyla 6-boyutlu durum vektörü kullanır:
    durum = [x, y, z, vx, vy, vz]

Referans: R. E. Kalman, "A New Approach to Linear Filtering and Prediction Problems" (1960)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class KalmanIzci:
    """
    Tek bir hedef için 9-Boyutlu Sabit İvme (CA) Kalman filtresi.

    Durum vektörü: [x, y, z, vx, vy, vz, ax, ay, az]
    """
    hedef_id: str
    dt: float = 1.0
    sigma_a: float = 0.5        # İvme değişim gürültüsü (m/s^3)
    sigma_r: float = 1.5        # Ölçüm gürültüsü (konum, km)

    x: np.ndarray = field(init=False)
    P: np.ndarray = field(init=False)
    F: np.ndarray = field(init=False)
    H: np.ndarray = field(init=False)
    Q: np.ndarray = field(init=False)
    R: np.ndarray = field(init=False)
    baslangic_yapildi: bool = field(default=False, init=False)
    guncelleme_sayisi: int = field(default=0, init=False)

    def __post_init__(self):
        dt = self.dt
        # Sabit İvme Modeli F matrisi
        # x = x + v*dt + 0.5*a*dt^2
        # v = v + a*dt
        # a = a
        self.F = np.eye(9, dtype=float)
        for i in range(3):
            self.F[i, i+3] = dt
            self.F[i, i+6] = 0.5 * dt**2
            self.F[i+3, i+6] = dt

        # Konum ölçümü (x, y, z)
        self.H = np.zeros((3, 9), dtype=float)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0

        # Süreç Gürültüsü (Sürekli Beyaz İvme Gürültüsü Modeli)
        q_val = self.sigma_a ** 2
        self.Q = np.zeros((9, 9), dtype=float)
        # Basit blok diyagonal varsayılan Q
        for i in range(3):
            self.Q[i+6, i+6] = q_val 

        # Ölçüm Gürültüsü
        self.R = (self.sigma_r ** 2) * np.eye(3)

        self.x = np.zeros(9, dtype=float)
        self.P = np.eye(9) * 100.0

    def ilklendir(self, x: float, y: float, z: float,
                   vx: float = 0.0, vy: float = 0.0, vz: float = 0.0,
                   ax: float = 0.0, ay: float = 0.0, az: float = 0.0):
        self.x = np.array([x, y, z, vx, vy, vz, ax, ay, az], dtype=float)
        self.baslangic_yapildi = True

    def tahmin_et(self) -> np.ndarray:
        if not self.baslangic_yapildi:
            raise RuntimeError("Filtre ilklendirilmedi.")
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x.copy()

    def guncelle(self, olcum_x: float, olcum_y: float, olcum_z: float) -> np.ndarray:
        z = np.array([olcum_x, olcum_y, olcum_z])
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        self.x = self.x + K @ y
        self.P = (np.eye(9) - K @ self.H) @ self.P
        
        self.guncelleme_sayisi += 1
        return self.x.copy()

    def konum_tahmini(self) -> tuple[float, float, float]:
        return float(self.x[0]), float(self.x[1]), float(self.x[2])

    def hiz_tahmini(self) -> tuple[float, float, float]:
        return float(self.x[3]), float(self.x[4]), float(self.x[5])

    def ivme_tahmini(self) -> tuple[float, float, float]:
        """Anlık ivme vektörü tahmini (km/s^2)."""
        return float(self.x[6]), float(self.x[7]), float(self.x[8])

    def ilerideki_konum(self, adim: int = 5) -> tuple[float, float, float]:
        """n saniye sonrası için 2. derece yörünge tahmini."""
        dt = self.dt * adim
        x_pred = self.x[0] + self.x[3]*dt + 0.5*self.x[6]*dt**2
        y_pred = self.x[1] + self.x[4]*dt + 0.5*self.x[7]*dt**2
        z_pred = self.x[2] + self.x[5]*dt + 0.5*self.x[8]*dt**2
        return float(x_pred), float(y_pred), float(z_pred)

    def F_adim(self, n: int) -> np.ndarray:
        """n adım için durum geçiş matrisini hesapla."""
        dt_n = self.dt * n
        F_n = np.eye(6, dtype=float)
        F_n[0, 3] = dt_n
        F_n[1, 4] = dt_n
        F_n[2, 5] = dt_n
        return F_n


class KalmanTakipYoneticisi:
    """
    Çoklu hedef Kalman filtresi izci havuzu yöneticisi.
    Her hedef için ayrı bir KalmanIzci tutar; atar ve siler.
    """

    def __init__(self, dt: float = 1.0):
        self.dt = dt
        self._izciler: dict[str, KalmanIzci] = {}

    def hedef_guncelle(
        self,
        hedef_id: str,
        x: float, y: float, z: float,
        vx: float = 0.0, vy: float = 0.0, vz: float = 0.0,
        ax: float = 0.0, ay: float = 0.0, az: float = 0.0
    ) -> KalmanIzci:
        """
        Radardan gelen ham ölçümler ile Kalman filtresini günceller.
        İzci yoksa yeni bir tane oluşturur.
        """
        if hedef_id not in self._izciler:
            izci = KalmanIzci(hedef_id=hedef_id, dt=self.dt)
            izci.ilklendir(x, y, z, vx, vy, vz, ax, ay, az)
            self._izciler[hedef_id] = izci
        else:
            izci = self._izciler[hedef_id]
            izci.tahmin_et()
            izci.guncelle(x, y, z)
        return izci

    def izci_al(self, hedef_id: str) -> Optional[KalmanIzci]:
        """Verilen ID'ye ait izciyi döndür."""
        return self._izciler.get(hedef_id)

    def hedef_sil(self, hedef_id: str):
        """İzciyi havuzdan kaldır (hedef imha/kayıp durumunda)."""
        self._izciler.pop(hedef_id, None)

    def aktif_izci_sayisi(self) -> int:
        return len(self._izciler)
