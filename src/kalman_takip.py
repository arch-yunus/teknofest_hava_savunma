"""
kalman_takip.py
===============
GökKalkan YZ - Kalman Filtresi Tabanlı Hedef Takip Sistemi

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
    Tek bir hedef için Kalman filtresi takip nesnesi.

    Durum uzayı modeli:
        x_{k+1} = F * x_k + w_k        (w: süreç gürültüsü)
        z_k     = H * x_k   + v_k        (v: ölçüm gürültüsü)

    F: Durum geçiş matrisi (sabit hız modeli)
    H: Ölçüm matrisi (sadece konum gözlemlenir)
    Q: Süreç gürültüsü kovaryans matrisi
    R: Ölçüm gürültüsü kovaryans matrisi
    P: Tahmin hata kovaryans matrisi
    """
    hedef_id: str
    dt: float = 1.0             # Örnekleme aralığı (saniye)
    sigma_q: float = 0.1        # Süreç gürültüsü (hız bileşeni)
    sigma_r: float = 2.0        # Ölçüm gürültüsü (konum, km)

    # Durum vektörü ve kovaryans (başlatma sonrası dolar)
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
        # Sabit hız modeli: x_{k+1} = F * x_k
        self.F = np.array([
            [1, 0, 0, dt, 0,  0 ],
            [0, 1, 0, 0,  dt, 0 ],
            [0, 0, 1, 0,  0,  dt],
            [0, 0, 0, 1,  0,  0 ],
            [0, 0, 0, 0,  1,  0 ],
            [0, 0, 0, 0,  0,  1 ],
        ], dtype=float)

        # Konum ölçümleri: H seçiyor [x, y, z]
        self.H = np.zeros((3, 6), dtype=float)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0

        # Süreç gürültüsü kovaryansı (Basit yaklaşım)
        q = self.sigma_q ** 2
        self.Q = q * np.eye(6, dtype=float)
        self.Q[3, 3] *= 10   # Hız bileşenleri daha belirsiz
        self.Q[4, 4] *= 10
        self.Q[5, 5] *= 10

        # Ölçüm gürültüsü kovaryansı
        r = self.sigma_r ** 2
        self.R = r * np.eye(3, dtype=float)

        # Başlangıç durumu ve kovaryansı
        self.x = np.zeros(6, dtype=float)
        self.P = np.eye(6, dtype=float) * 100.0   # Büyük başlangıç belirsizliği

    def ilklendir(self, x: float, y: float, z: float,
                  vx: float = 0.0, vy: float = 0.0, vz: float = 0.0):
        """Filtreyi bilinen (veya tahmini) başlangıç konum/hız ile ilklendir."""
        self.x = np.array([x, y, z, vx, vy, vz], dtype=float)
        self.baslangic_yapildi = True

    def tahmin_et(self) -> np.ndarray:
        """
        Öngörü adımı: mevcut durum tahminin bir adım ileriye yayar.
        Returns: tahmin edilen durum vektörü (6,)
        """
        if not self.baslangic_yapildi:
            raise RuntimeError("Kalman filtresi ilklenmedi. ilklendir() çağrısı gerekli.")
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x.copy()

    def guncelle(self, olcum_x: float, olcum_y: float, olcum_z: float) -> np.ndarray:
        """
        Güncelleme adımı: yeni radar ölçümünü asimile eder.

        Args:
            olcum_x, olcum_y, olcum_z: Radar'dan gelen ham konum ölçümleri (km)

        Returns:
            Güncellenmiş durum tahmini (6,)
        """
        z = np.array([olcum_x, olcum_y, olcum_z], dtype=float)

        # Yenilik (artık)
        y = z - self.H @ self.x

        # Yenilik kovaryansı
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman kazancı
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Durum güncellemesi
        self.x = self.x + K @ y

        # Kovaryans güncellemesi (Joseph formu — sayısal kararlılık)
        I_KH = np.eye(6) - K @ self.H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T

        self.guncelleme_sayisi += 1
        return self.x.copy()

    def konum_tahmini(self) -> tuple[float, float, float]:
        """Mevcut en iyi konum tahminini döndür (km)."""
        return float(self.x[0]), float(self.x[1]), float(self.x[2])

    def hiz_tahmini(self) -> tuple[float, float, float]:
        """Mevcut en iyi hız tahminini döndür (km/s)."""
        return float(self.x[3]), float(self.x[4]), float(self.x[5])

    def ilerideki_konum(self, adim: int = 5) -> tuple[float, float, float]:
        """
        `adim` saniye sonraki tahmini konumu döndür (basit doğrusal ekstrapolasyon).
        """
        x_iler = self.F_adim(adim) @ self.x
        return float(x_iler[0]), float(x_iler[1]), float(x_iler[2])

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
        vx: float = 0.0, vy: float = 0.0, vz: float = 0.0
    ) -> KalmanIzci:
        """
        Radardan gelen ham ölçümler ile Kalman filtresini günceller.
        İzci yoksa yeni bir tane oluşturur.
        """
        if hedef_id not in self._izciler:
            izci = KalmanIzci(hedef_id=hedef_id, dt=self.dt)
            izci.ilklendir(x, y, z, vx, vy, vz)
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
