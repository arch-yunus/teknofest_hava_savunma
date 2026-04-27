# 📡 SANCAR AI - İleri Elektronik Harp (EW) ve Sinyal İşleme Doktrini

## 1. Giriş
Bu döküman, SANCAR AI sisteminin elektromanyetik spektrum üzerindeki operasyonel yeteneklerini, sinyal işleme algoritmalarını ve Elektronik Karşı-Karşı Tedbir (ECCM) stratejilerini detaylandırır.

## 2. Radar Menzil Denklemi ve SNR Analizi

Sistemin bir hedefi tespit edebilmesi için gereken minimum Sinyal-Gürültü Oranı (SNR) aşağıdaki denklemle modellenir:

$$SNR = \frac{P_t \cdot G^2 \cdot \lambda^2 \cdot \sigma}{(4\pi)^3 \cdot R^4 \cdot k \cdot T \cdot B \cdot L}$$

Burada:
- $P_t$: Verici gücü
- $G$: Anten kazancı
- $\sigma$: Radar Kesit Alanı (RCS)
- $R$: Hedef mesafesi
- $L$: Sistem kayıpları

**SANCAR V5.0**, statik bir "tespit olasılığı" yerine, anlık SNR değerini hesaplayarak dedeksiyon kararını verir. SNR > $SNR_{threshold}$ ise hedef takibe alınır.

## 3. RCS Dalgalanma Modelleri (Swerling Modelleri)

Gerçek dünyada hedeflerin RCS değeri sabit değildir; hedefin açısına ve hareketine göre sürekli dalgalanır. Sistemimizde aşağıdaki Swerling vakaları simüle edilmektedir:

- **Swerling Case 1:** Birçok bağımsız saçıcıdan oluşan hedefler (örn. büyük uçaklar). RCS, taramadan taramaya yavaş değişir.
- **Swerling Case 3:** Bir ana saçıcı ve birçok küçük saçıcıdan oluşan hedefler (örn. füzeler).

## 4. Mikro-Doppler Analizi: İHA Teşhisi

Pervaneli İHA'ların (Drones) gövde hareketine ek olarak pervanelerinin hızı, radar sinyalinde karakteristik "mikro-Doppler" imzaları oluşturur.

$$f_{mD} = \frac{2 \cdot v_{tip}}{\lambda} \cdot \cos(\theta)$$

SANCAR AI, bu frekans kaymalarını analiz ederek kuş ve drone ayrımını (Bird vs Drone) yüksek doğrulukla gerçekleştirir.

## 5. Elektronik Karşı-Karşı Tedbirler (ECCM)

Düşman parazitlerine (Jamming) karşı uygulanan savunma stratejileri:

1.  **Frekans Atlamalı (Frequency Hopping):** Radar taşıyıcı frekansının rastgele aralıklarla değiştirilmesi.
2.  **Sidelobe Blanking:** Yan loblardan gelen güçlü jamming sinyallerinin ana lob verisinden ayrıştırılarak silinmesi.
3.  **Darbe Sıkıştırma (Pulse Compression):** Düşük tepe gücüyle yüksek menzil çözünürlüğü elde ederek gürültü tabanının altında kalan hedeflerin yakalanması.

---
> [!IMPORTANT]
> Bu döküman askeri sınıf simülasyon parametreleri içerir. Algoritma güncellemeleri yapılırken buradaki matematiksel modeller temel alınmalıdır.
