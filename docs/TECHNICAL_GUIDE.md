# 🧮 GökKalkan AI: Teknik Dokümantasyon ve Operasyonel Fizik

Bu kılavuz, GökKalkan sisteminin kalbinde yatan matematiksel modelleri ve uçuş fiziği kurallarını detaylandırmaktadır.

## 1. Radar Menzil Denklemi (SNR Analizi)

Sistemimiz, bir hedefin tespit edilip edilemeyeceğini belirlemek için **SNR (Signal-to-Noise Ratio)** değerini anlık olarak hesaplar:

$$SNR = \frac{P_t \cdot G^2 \cdot \lambda^2 \cdot \sigma}{(4\pi)^3 \cdot R^4 \cdot k \cdot T \cdot B \cdot L_{total}}$$

**Bileşenler:**
*   **$P_t$:** Verici Gücü (Watt)
*   **$G$:** Anten Kazancı
*   **$\lambda$:** Dalga boyu ($c / f$)
*   **$\sigma$:** Radar Kesit Alanı (RCS) - Swerling modelleriyle dalgalanır.
*   **$R$:** Hedefe olan mesafe (Metre)
*   **$L_{total}$:** Atmosferik kayıplar + Yağmur zayıflatması + Sistem kayıpları.

---

## 2. Kalman Filtresi (Yörünge Takibi)

Gürültülü radar verilerinden pürüzsüz bir iz sürmek için `KalmanFilter` kullanılır. Durum vektörümüz:

$$x = [x, y, z, v_x, v_y, v_z, a_x, a_y, a_z]^T$$

**Süreç:**
1.  **Tahmin (Prediction):** Bir sonraki konumu fizik kurallarına göre tahmin et.
2.  **Güncelleme (Update):** Radardan gelen yeni ölçümü (Kalman Gain ile) tahmine yedir.

---

## 3. Sürü Zekası: Boids Algoritması

Düşman sürü İHA'ları, birbirleriyle çarpışmadan ve koordine hareket etmek için üç temel kuralı uygular:

1.  **Ayrılma (Separation):** Komşularıyla çok yakın olmaktan kaçın.
2.  **Hizalanma (Alignment):** Komşularının ortalama hız vektörüne uyum sağla.
3.  **Birleşme (Cohesion):** Sürünün kütle merkezine doğru yönel.

---

## 4. Önleme Mantığı: Proportional Navigation (PN)

Önleyici füzelerimiz, hedefi sadece kovalamak yerine (Pure Pursuit), gelecekteki çarpışma noktasına doğru yönelir. **CPA (Closest Point of Approach)** ve **TTI (Time to Impact)** değerleri milisaniyelik hassasiyetle güncellenir.

> [!TIP]
> **Hit-to-Kill:** Sistemimiz, hedefin yakınında patlamak yerine doğrudan kinetik çarpışmayı hedefler. Vuruş hassasiyeti `interceptor.py` içindeki `vurus_mesafesi` parametresiyle kontrol edilir.
