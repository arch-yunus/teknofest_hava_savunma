"""
tehdit_siniflandirici.py
========================
GökKalkan YZ - Tehdit Sınıflandırma Motoru

Hedefin kinematik parametrelerinden (hız, irtifa, manevra kabiliyeti, 
CPA) yararlanarak tehdit tipini ve öncelik skorunu belirler.
Kural tabanlı bir karar motoru ile desteklenir.
"""

import math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Tuple
from radar import Hedef

class TehditTipi(Enum):
    """Tanımlanmış hava tehdit kategorileri."""
    BALISTIK_FUZZE    = auto()   # Yüksek hız, dik profil, yüksek tehdit
    SEYIR_FUZE        = auto()   # Orta hız, alçak uçuş
    HIPERSONIK_FUZE   = auto()   # Mach 5+ hızlar, manevra kabiliyeti yüksek
    SABIT_KANAT_UCAK  = auto()   # Orta-yüksek hız, sabit irtifa
    INSANSIZ_HAVA     = auto()   # Düşük hız, değişken irtifa
    DOST_UNSUR        = auto()   # Dost unsurlar (IFF doğrulanmış)
    BILINMEYEN        = auto()   # Sınıflandırılamayan
    CLUTTER           = auto()   # Yeni: Radar gürültüsü / Yanlış alarm


class TehditOnceligi(Enum):
    """Angajman öncelik seviyeleri."""
    KRİTİK   = 4
    YUKSEK   = 3
    ORTA     = 2
    DUSUK    = 1


@dataclass
class TehditDegerlendirmesi:
    """Bir hedef için üretilen tam tehdit değerlendirmesi."""
    hedef_id: str
    tehdit_tipi: TehditTipi
    oncelik: TehditOnceligi
    tehdit_skoru: float          # 0.0 - 1.0 arası normalize skor
    tahmini_mensei: str          # İnsan-okunabilir tanım
    onerilen_karar: str          # Angajman önerisi
    ek_notlar: list = field(default_factory=list)

    def ozet(self) -> str:
        """Konsol çıktısı için kısa özet."""
        return (
            f"[{self.hedef_id}] TİP:{self.tehdit_tipi.name} "
            f"| ÖNCELİK:{self.oncelik.name} "
            f"| SKOR:{self.tehdit_skoru:.2f} "
            f"| KARAR:{self.onerilen_karar}"
        )


class TehditSiniflandirici:
    """
    Kural tabanlı tehdit sınıflandırma ve önceliklendirme motoru.
    
    Her hedef için TehditDegerlendirmesi üretir. Gelecek iterasyonlarda
    bu motor bir ML modeli ile entegre edilebilir.
    """

    # Sınıflandırma eşik değerleri (km/h)
    HIPERSONIK_HIZ_ESIGI= 6125.0   # > 6125 km/h (Mach 5+)
    BALISTIK_HIZ_ESIGI  = 3000.0   # > 3000 km/h → Balistik füze şüphesi
    SEYIR_HIZ_UST       = 1200.0   # 600-1200 km/h arası → Seyir füzesi
    SEYIR_HIZ_ALT       = 600.0
    UCAK_HIZ_UST        = 1800.0   # 300-1800 km/h → Sabit kanat
    UCAK_HIZ_ALT        = 300.0
    IHA_HIZ_UST         = 300.0    # < 300 km/h → İHA

    # İrtifa eşikleri (km)
    BALISTIK_IRTIFA_ALT = 20.0
    ALCAK_IRTIFA_UST    = 1.0     # < 1 km → alçak uçuş profili

    def siniflandir(self, hedef: Hedef, cpa_km: float, tti_sn: float | None) -> TehditDegerlendirmesi:
        """
        Verilen hedefi sınıflandırır ve değerlendirme üretir.

        Args:
            hedef:  Hedef nesnesi
            cpa_km: En Yakın Geçiş Mesafesi (km)
            tti_sn: Çarpışmaya Kalan Süre (sn), yaklaşmıyorsa None

        Returns:
            TehditDegerlendirmesi nesnesi
        """
        if getattr(hedef, 'is_dost', False):
            return TehditDegerlendirmesi(
                hedef_id=hedef.id,
                tehdit_tipi=TehditTipi.DOST_UNSUR,
                oncelik=TehditOnceligi.DUSUK,
                tehdit_skoru=0.0,
                tahmini_mensei="Doğrulanmış Dost Unsur (IFF)",
                onerilen_karar="DOST - ANGAJMAN YASAK",
                ek_notlar=["Sistem Kilidi: Kinetik müdahale engellendi."]
            )

        hiz = hedef.toplam_hiz           # km/h
        irtifa = hedef.z                 # km
        mesafe = hedef.mesafe            # km

        tehdit_tipi, mensei = self._tip_belirle(hiz, irtifa)
        tehdit_skoru = self._skor_hesapla(mesafe, cpa_km, tti_sn, hiz, tehdit_tipi)
        oncelik = self._oncelik_belirle(tehdit_skoru, tehdit_tipi)
        karar = self._karar_olustur(oncelik, cpa_km, tti_sn)
        notlar = self._ek_notlar_ekle(hiz, irtifa, cpa_km, tti_sn, tehdit_tipi)

        return TehditDegerlendirmesi(
            hedef_id=hedef.id,
            tehdit_tipi=tehdit_tipi,
            oncelik=oncelik,
            tehdit_skoru=tehdit_skoru,
            tahmini_mensei=mensei,
            onerilen_karar=karar,
            ek_notlar=notlar
        )

    # ------------------------------------------------------------------ #
    #  İÇ YARDIMCI METODLAR                                               #
    # ------------------------------------------------------------------ #

    def _tip_belirle(self, hiz: float, irtifa: float) -> Tuple[TehditTipi, str]:
        if hiz >= self.HIPERSONIK_HIZ_ESIGI:
            return TehditTipi.HIPERSONIK_FUZE, "Mach 5+ Hipersonik Tehdit! Kritik önleme penceresi."
        if hiz >= self.BALISTIK_HIZ_ESIGI:
            return TehditTipi.BALISTIK_FUZZE, "Yüksek hızlı balistik tehdit"
        if self.SEYIR_HIZ_ALT <= hiz < self.SEYIR_HIZ_UST and irtifa < self.ALCAK_IRTIFA_UST:
            return TehditTipi.SEYIR_FUZE, "Alçak uçuşlu seyir füzesi"
        if self.UCAK_HIZ_ALT <= hiz < self.UCAK_HIZ_UST:
            return TehditTipi.SABIT_KANAT_UCAK, "Sabit kanatlı hava aracı"
        if hiz < self.IHA_HIZ_UST:
            return TehditTipi.INSANSIZ_HAVA, "İnsansız Hava Aracı (İHA)"
        
        # Aşama 10.2: Clutter/Gürültü tespiti
        # Eğer etiket CLUTTER ise veya hız/irtifa çok düşük/düzensiz ise
        return TehditTipi.BILINMEYEN, "Kimliği doğrulanamayan hava unsuru"

    def _clutter_kontrol(self, hedef: Hedef) -> bool:
        """Hedefin clutter olup olmadığını kontrol eder."""
        if getattr(hedef, 'etiket', "") == "CLUTTER":
            return True
        if getattr(hedef, 'is_ghost', False) and hedef.toplam_hiz < 100:
            return True
        return False

    def _skor_hesapla(
        self,
        mesafe: float,
        cpa: float,
        tti: float | None,
        hiz: float,
        tip: TehditTipi,
    ) -> float:
        """0-1 arasında tehdit skoru üretir."""
        # Bileşen 1: CPA (yaklaştıkça tehlike artar)
        cpa_skorlama = max(0.0, 1.0 - (cpa / 80.0))   # 0 km → 1.0, 80+ km → 0

        # Bileşen 2: TTI (zaman kısaldıkça tehlike artar)
        if tti is not None:
            tti_skorlama = max(0.0, 1.0 - (tti / 600.0))  # 0sn → 1.0, 600sn+ → 0
        else:
            tti_skorlama = 0.0

        # Bileşen 3: Tehdit tipi ağırlığı
        tip_agirlik = {
            TehditTipi.HIPERSONIK_FUZE:   1.0,
            TehditTipi.BALISTIK_FUZZE:    0.95,
            TehditTipi.SEYIR_FUZE:        0.85,
            TehditTipi.SABIT_KANAT_UCAK:  0.60,
            TehditTipi.INSANSIZ_HAVA:     0.40,
            TehditTipi.BILINMEYEN:        0.50,
            TehditTipi.CLUTTER:           0.01, # Clutter skoru çok düşük
        }.get(tip, 0.5)

        # Bileşen 4: Hız bileşeni (normalleştirilmiş)
        hiz_skoru = min(1.0, hiz / 4000.0)

        # Ağırlıklı ortalama
        skor = (
            0.35 * cpa_skorlama
            + 0.30 * tti_skorlama
            + 0.20 * tip_agirlik
            + 0.15 * hiz_skoru
        )
        return round(min(1.0, max(0.0, skor)), 4)

    def _oncelik_belirle(self, skor: float, tip: TehditTipi) -> TehditOnceligi:
        # Balistik füzeler her zaman kritik
        if tip == TehditTipi.BALISTIK_FUZZE:
            return TehditOnceligi.KRİTİK
        if skor >= 0.75:
            return TehditOnceligi.KRİTİK
        if skor >= 0.50:
            return TehditOnceligi.YUKSEK
        if skor >= 0.25:
            return TehditOnceligi.ORTA
        return TehditOnceligi.DUSUK

    def _karar_olustur(self, oncelik: TehditOnceligi, cpa: float, tti: float | None) -> str:
        if oncelik == TehditOnceligi.KRİTİK:
            return "ANINDA ANGAJ ET"
        if oncelik == TehditOnceligi.YUKSEK:
            return "ANGAJMANA HAZIRLAN"
        if oncelik == TehditOnceligi.ORTA:
            return "TAKİP ET / BEKLE"
        return "GÖZLEM"

    def _ek_notlar_ekle(
        self,
        hiz: float,
        irtifa: float,
        cpa: float,
        tti: float | None,
        tip: TehditTipi,
    ) -> list:
        notlar = []
        if irtifa < 0.5:
            notlar.append("UYARI: Aşırı alçak irtifa — radar gölge bölgesi riski")
        if hiz > 2000:
            notlar.append("UYARI: Hipersonik hız eşiği — kısa angajman penceresi")
        if tti is not None and tti < 60:
            notlar.append("KRİTİK: 60 saniye altı çarpışma süresi!")
        if cpa < 5.0:
            notlar.append("KRİTİK: CPA 5 km altında — doğrudan vuruş tehdidi")
        return notlar
