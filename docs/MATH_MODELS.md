# 🧮 ARGUS: Operasyonel Matematik Modelleri (MATH_MODELS)

Bu doküman, ARGUS AI sisteminin çekirdeğinde (Core Engine) saniyede binlerce kez işletilen fizik, diferansiyel denklem ve istatistiksel olasılık algoritmalarının matematiksel izdüşümüdür.

## 1. Kalman Filtresi: Özyineli Durum Tahmini (Recursive State Estimation)

Radardan gelen ölçümler her zaman "clutter" (çevresel gürültü) içerir. ARGUS, `kalman_takip.py` modülü ile hedefin *gerçek* uzay koordinatlarını $X_k$ şu denklemlerle bulur:

### Durum Tahmini (Zaman Güncellemesi / Time Update)
Hedefin bir sonraki $(k+1)$ anındaki durumu, mevcut bilgi ve fizik kuralları çerçevesinde tahmin edilir:

$$ \hat{x}_{k+1|k} = F \cdot \hat{x}_{k|k} + B \cdot u_k $$
$$ P_{k+1|k} = F \cdot P_{k|k} \cdot F^T + Q $$

* $\hat{x}$: Durum Vektörü $[x, y, z, v_x, v_y, v_z]^T$
* $F$: Durum Geçiş Matrisi (Kinematik hareket modeli)
* $P$: Hata Kovaryans Matrisi (Tahminimize ne kadar güvendiğimiz)
* $Q$: Süreç Gürültüsü (Rüzgar vb. tahmin edilemeyen dış kuvvetler)

### Ölçüm Güncellemesi (Measurement Update)
Radardan alınan yeni ölçüm ($z_k$) ile yapılan tahmin "Kalman Kazancı" ($K$) oranında harmanlanır:

$$ K_k = P_{k|k-1} \cdot H^T \cdot (H \cdot P_{k|k-1} \cdot H^T + R)^{-1} $$
$$ \hat{x}_{k|k} = \hat{x}_{k|k-1} + K_k \cdot (z_k - H \cdot \hat{x}_{k|k-1}) $$
$$ P_{k|k} = (I - K_k \cdot H) \cdot P_{k|k-1} $$

* $K_k$: Kalman Kazancı (Ölçüme mi, tahmine mi daha çok güvenileceği)
* $R$: Ölçüm Gürültü Kovaryansı (Radarın donanım hatası)
* $z_k - H \hat{x}$: İnovasyon (Beklenen ile ölçülen arasındaki fark)

---

## 2. AESA Radar Menzil Denklemi (The Radar Equation)

ARGUS `radar.py` içerisinde bir Sinyal-Gürültü Oranı (SNR) filtresi kullanır. Hedefin tespiti, radar kesit alanına ($\sigma$) ve mesafeye ($R$) bağlı dördüncü dereceden ters orantılı bir fonksiyondur:

$$ SNR = \frac{P_t \cdot G^2 \cdot \lambda^2 \cdot \sigma}{(4\pi)^3 \cdot R^4 \cdot k \cdot T_s \cdot B \cdot L} $$

* $P_t$: Verici Gücü (Watt)
* $G$: Anten Kazancı
* $\lambda$: Dalga Boyu ($c / f$)
* $\sigma$: Hedefin Radar Kesit Alanı (RCS, $m^2$)
* $R$: Radara olan mesafe
* $k$: Boltzmann Sabiti ($1.38 \times 10^{-23}$)
* $T_s$: Sistem Gürültü Sıcaklığı (Kelvin)
* $B$: Bant Genişliği (Hz)
* $L$: Sistem Kayıpları

Eğer hesaplanan $SNR > SNR_{min\_esik\_db}$ ise, hedef (Blip) ekrana yansıtılır.

### Swerling Hedef Modelleri (RCS Dalgalanması)
ARGUS, hedefin sabit bir demir parçası değil, dönen türbinleri ve manevra yapan kanatları olduğunu varsayar (Swerling I/III). RCS dalgalanması Exponential (Rayleigh) veya Gamma dağılımlarıyla modellenir:

$$ p(\sigma) = \frac{1}{\sigma_{avg}} e^{-\sigma/\sigma_{avg}} \quad \text{(Swerling 1)} $$

---

## 3. Oransal Seyrüsefer (Proportional Navigation - PN)

`interceptor.py` içerisindeki füzelerimiz, hedeflerini kovalamazlar, hedeflerinin *olacakları yere* uçarlar. Görüş Hattı (Line-of-Sight, LOS) açısının değişim oranı kullanılarak en ideal ivme vektörü çıkarılır:

$$ a_m = N \cdot V_c \cdot \dot{\lambda} $$

* $a_m$: Füzenin uygulanması gereken yanal ivmesi (Commanded Acceleration)
* $N$: Navigasyon Sabiti (Genellikle 3.0 ile 5.0 arası)
* $V_c$: Kapanma Hızı (Closing Velocity, Füze ve hedefin göreli hızı)
* $\dot{\lambda}$: LOS (Görüş Hattı) Açısının Değişim Hızı (Türev)

Eğer $\dot{\lambda} = 0$ ise, füze hedeflerle mükemmel bir çarpışma rotasındadır.

---

## 4. Time To Impact (TTI) ve Closest Point of Approach (CPA)

Tehdit Sınıflandırıcımız (AI) sadece kimliğe değil, **geometriye** de bakar.

**TTI (Çarpışma Süresi):**
$$ TTI = - \frac{||\vec{r}_{hedef} - \vec{r}_{radar}||}{||\vec{v}_{hedef} \cdot \hat{u}_r||} $$

**CPA (En Yakın Geçiş Noktası):**
$$ t_{CPA} = - \frac{\vec{r}_{hedef} \cdot \vec{v}_{hedef}}{||\vec{v}_{hedef}||^2} $$
$$ \vec{P}_{CPA} = \vec{r}_{hedef} + \vec{v}_{hedef} \cdot t_{CPA} $$
$$ CPA_{Mesafe} = ||\vec{P}_{CPA}|| $$

*ARGUS bu denklemleri harmanlayarak, "hangi hedefin saniyeler içinde başımıza dert açacağını" mekanik bir soğukkanlılıkla bulur.*
