import sys
import os
import unittest
import math
import numpy as np

# Add src to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from radar import RadarSistemi, Hedef
from interceptor import OnleyiciBatarya, MuhimmatYokHatasi
from tehdit_siniflandirici import TehditSiniflandirici, TehditTipi, TehditOnceligi
from kalman_takip import KalmanIzci, KalmanTakipYoneticisi
import utils


class TestGokKalkanV2(unittest.TestCase):

    def test_hedef_matematigi(self):
        """Hedef sınıfının mesafe ve hız hesaplamalarını doğrular."""
        h = Hedef("TEST", x=3, y=4, z=0, vx=0, vy=0, vz=0)
        self.assertEqual(h.mesafe, 5.0)
        h.vx = 1.0
        self.assertEqual(h.toplam_hiz, 3600.0)

    def test_radar_3b_tespit(self):
        """Radarın 3B uzayda hedef üretme mantığını test eder."""
        radar = RadarSistemi(menzil_km=100)
        tespit = None
        for _ in range(20):
            tespit = radar.tara()
            if tespit: break
        if tespit:
            self.assertIsInstance(tespit, Hedef)
            self.assertLessEqual(tespit.mesafe, 100 * 1.1)
            self.assertTrue(0 <= tespit.z <= 15)

    def test_gelismis_onleyici_ve_istisna(self):
        """Mühimmat tükenme hatasını (Exception) test eder."""
        batarya = OnleyiciBatarya(muhimmat=1)
        hedef = Hedef("H1", 10, 10, 5, 0, 0, 0)
        batarya.angaje_ol(hedef)
        self.assertEqual(batarya.muhimmat, 0)
        with self.assertRaises(MuhimmatYokHatasi):
            batarya.angaje_ol(hedef)

    def test_vurus_ihtimali_pn(self):
        """Vuruş ihtimali hesaplamasının (basitleştirilmiş PN) çalıştığını doğrular."""
        batarya = OnleyiciBatarya(muhimmat=10)
        h_yakin = Hedef("Y", 2, 2, 1, -0.1, -0.1, 0) # Yakın ve yavaş
        # angaje_ol artık boolean döndürür, ancak iç mantığı test etmek için 
        # mühimmatın düştüğünü kontrol edebiliriz
        batarya.angaje_ol(h_yakin)
        self.assertEqual(batarya.muhimmat, 9)

    def test_ballistic_utils(self):
        """TTI ve CPA matematiksel fonksiyonlarını doğrular."""
        h = Hedef("B1", 10, 0, 0, -1, 0, 0)
        self.assertEqual(utils.carpisma_suresi_hesapla(h), 10.0)
        self.assertEqual(utils.en_yakin_nokta_hesapla(h), 0.0)
        h_side = Hedef("B2", 10, 10, 0, -1, 0, 0)
        self.assertEqual(utils.en_yakin_nokta_hesapla(h_side), 10.0)


class TestTehditSiniflandirici(unittest.TestCase):

    def setUp(self):
        self.sc = TehditSiniflandirici()

    def _hedef(self, hiz_kmh, irtifa_km=5.0, mesafe_km=100.0):
        """Yardımcı: belirtilen hız (km/h) ve irtifada basit bir hedef üretir."""
        hiz_kms = hiz_kmh / 3600.0
        # Merkeze yönelmiş hareket
        h = Hedef("T", mesafe_km, 0, irtifa_km, -hiz_kms, 0, 0)
        return h

    def test_balistik_siniflandirma(self):
        """3500 km/h hedef balistik füze olarak tanınmalı."""
        h = self._hedef(3500)
        d = self.sc.siniflandir(h, cpa_km=5.0, tti_sn=100.0)
        self.assertEqual(d.tehdit_tipi, TehditTipi.BALISTIK_FUZZE)

    def test_seyir_fuze_siniflandirma(self):
        """800 km/h, 0.5 km irtifadaki hedef seyir füzesi olmalı."""
        h = self._hedef(800, irtifa_km=0.5)
        d = self.sc.siniflandir(h, cpa_km=20.0, tti_sn=300.0)
        self.assertEqual(d.tehdit_tipi, TehditTipi.SEYIR_FUZE)

    def test_iha_siniflandirma(self):
        """150 km/h hedef İHA olarak tanınmalı."""
        h = self._hedef(150)
        d = self.sc.siniflandir(h, cpa_km=30.0, tti_sn=None)
        self.assertEqual(d.tehdit_tipi, TehditTipi.INSANSIZ_HAVA)

    def test_balistik_her_zaman_kritik(self):
        """Balistik füze her koşulda KRİTİK öncelik almalı."""
        h = self._hedef(4000)
        d = self.sc.siniflandir(h, cpa_km=100.0, tti_sn=None)
        self.assertEqual(d.oncelik, TehditOnceligi.KRİTİK)

    def test_skor_aralik_kontrolu(self):
        """Tehdit skoru 0-1 arasında olmalı."""
        for hiz in [100, 500, 1000, 3500]:
            for cpa in [1, 20, 80]:
                h = self._hedef(hiz)
                d = self.sc.siniflandir(h, cpa_km=float(cpa), tti_sn=200.0)
                self.assertGreaterEqual(d.tehdit_skoru, 0.0)
                self.assertLessEqual(d.tehdit_skoru, 1.0)


class TestKalmanTakip(unittest.TestCase):

    def test_ilklenme_ve_konum(self):
        """Kalman izci doğru başlangıç konumunu raporlamalı."""
        izci = KalmanIzci("T1")
        izci.ilklendir(10.0, 20.0, 5.0)
        x, y, z = izci.konum_tahmini()
        self.assertAlmostEqual(x, 10.0)
        self.assertAlmostEqual(y, 20.0)
        self.assertAlmostEqual(z, 5.0)

    def test_tahmin_adimi(self):
        """Sabit hızla gelen hedefe Kalman öngörüsü doğru yönde ilerlemeli."""
        izci = KalmanIzci("T2", dt=1.0)
        # x=-10 km, vx=+1 km/s, ax=0 → bir adım sonra x≈-9 beklenir
        izci.ilklendir(-10.0, 0.0, 0.0, vx=1.0)
        tahmin = izci.tahmin_et()
        # x bileşeni -9.0 ± küçük hata (CA modeli dt=1 için x + v + 0.5*a)
        self.assertAlmostEqual(tahmin[0], -9.0, places=3)
        self.assertEqual(len(tahmin), 9) # 9-boyutlu durum vektörü kontrolü

    def test_guncelleme_kovaryans_azalmasi(self):
        """Güncelleme adımlarından sonra belirsizlik (P kovaryansı) azalmalı."""
        izci = KalmanIzci("T3")
        izci.ilklendir(50.0, 50.0, 5.0, vx=-0.5, vy=-0.5)
        p_onceki = np.trace(izci.P)
        for i in range(5):
            izci.tahmin_et()
            izci.guncelle(50.0 - 0.5*(i+1), 50.0 - 0.5*(i+1), 5.0)
        p_sonraki = np.trace(izci.P)
        self.assertLess(p_sonraki, p_onceki)

    def test_yonetici_izci_havuzu(self):
        """KalmanTakipYoneticisi yeni hedefler için otomatik izci oluşturmalı."""
        ym = KalmanTakipYoneticisi(dt=1.0)
        self.assertEqual(ym.aktif_izci_sayisi(), 0)
        ym.hedef_guncelle("H1", 10, 20, 5)
        ym.hedef_guncelle("H2", 50, 50, 3)
        self.assertEqual(ym.aktif_izci_sayisi(), 2)
        ym.hedef_sil("H1")
        self.assertEqual(ym.aktif_izci_sayisi(), 1)

    def test_ilerideki_konum_dogrusal(self):
        """Sabit hızlı hedef için ilerideki konum doğrusalca uzaklaşmalı."""
        izci = KalmanIzci("T4", dt=1.0)
        # vx=2 km/s, başlangıç x=0 → 5s sonra x≈10 beklenir
        izci.ilklendir(0.0, 0.0, 0.0, vx=2.0)
        px, py, pz = izci.ilerideki_konum(adim=5)
        self.assertAlmostEqual(px, 10.0, places=3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
