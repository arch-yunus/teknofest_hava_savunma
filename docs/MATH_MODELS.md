# 🧮 GökKalkan: Operasyonel Matematik ve Fiziksel Modeller (MATH_MODELS)

Bu belge, GökKalkan YZ Hava Savunma Sistemi'nin arkasında yatan matematiksel donanımı, kuadratik ve diferansiyel denklemler üzerinden askeri mühendislik standartlarında açıklamaktadır. 

---

## 🚀 1. Zaman-İmha (Time-To-Impact / TTI) Projeksiyonu

Radarlarımız sadece X, Y, Z konumunu değil, aynı zamanda hedefin vektörel hızını $\vec{v}_t$ ve ivmesini $\vec{a}_t$ hesaplar. Radardan gelen ham veri, basit bir doğrusal denklemden ziyade 3 boyutlu bir kuadratik denkleme dökülür.

### 1.1 Çarpışma Süresi Diferansiyeli
Eğer mühimmatın $\vec{v}_m$ hız vektörü ve hedefin hareket vektörü arasındaki kinematik kapanış hızı $v_{close}$ olarak tanımlanırsa:

$$ t_{impact} = \frac{- (\vec{r}_t \cdot \vec{v}_{rel}) \pm \sqrt{(\vec{r}_t \cdot \vec{v}_{rel})^2 - |\vec{v}_{rel}|^2 (|\vec{r}_t|^2 - R_{kill}^2)} }{|\vec{v}_{rel}|^2} $$

*Burada:*
- $\vec{r}_t$: Hedefin anlık 3D vektörel konumu
- $\vec{v}_{rel}$: Önleyici mühimmat ile hedef arasındaki bağıl hız vektörü ($v_t - v_m$)
- $R_{kill}$: Proximity Fuze (Yaklaşma Tapası) ölümcül şarapnel patlama yarıçapıdır.

---

## 🎯 2. Genişletilmiş Kalman Filtresi (Extended Kalman Filter - EKF)

Dünya yuvarlaktır, füzeler ise kavisli parabolik yörüngeler izler. Doğrusal Kalman filtresi atmosferik sürtünme değişkenlikleri karşısında çuvallar, bu yüzden füzelerin takip algoritmalarında doğrusal olmayan (Non-linear) izleme sistemleri kullanılır.

### 2.1 Durum Vektörü Güncellemesi (State Update)
Durum vektörü $\hat{x}_k$ şu şekilde hesaplanır:

$$ \hat{x}_{k|k-1} = f(\hat{x}_{k-1|k-1}, u_k) $$
$$ P_{k|k-1} = F_k P_{k-1|k-1} F_k^T + Q_k $$

- $F_k$: Sistemin Jacobian (Türev) matrisi. Füzelerin dönüş ivmelerini hesaplar.
- $Q_k$: Süreç (Process) Gürültüsü. Hedefin rastgele kaçış manevrası yapma ihtimalinin varyansı. Sürü İHA'larda bu değer çok yüksektir.

### 2.2 Çevresel Gürültü ve İnovasyon (Kalman Kazancı)
Radar verisi $z_k$ ekrana düştüğünde sistem o veriye hemen inanmaz. Radar yansıması ile hesaplanan nokta arasındaki fark (İnovasyon) alınır:

$$ y_k = z_k - h(\hat{x}_{k|k-1}) $$
$$ S_k = H_k P_{k|k-1} H_k^T + R_k $$
$$ K_k = P_{k|k-1} H_k^T S_k^{-1} $$

Eğer $R_k$ (Sensör Paraziti) çok yüksekse (düşman Jammer açtıysa), Kalman Kazancı ($K_k$) sıfıra yaklaşır. Sistem körü körüne radara inanmak yerine fiziksel momentum hesaplarına (Dead Reckoning) güvenmeye başlar.

---

## 🌪️ 3. Proportional Navigation (PN) Güdüm Yasası

GökKalkan Önleyicileri hedefin olduğu yere gitmez; **hedefin olacağı yere** gider. Füzelerimiz hedefi arkasından kovalamaz, ona yandan çarpmak için *Oransal Seyrüsefer* (Proportional Navigation) algoritması uygular.

$$ \vec{a}_m = N \cdot V_c \cdot \dot{\lambda} \cdot \vec{n} $$

*Açıklama:*
- $\vec{a}_m$: Mühimmatın (Füzenin) üretmesi gereken manevra ivmesi (G-kuvveti)
- $N$: Navigasyon Sabiti (Genellikle 3 ile 5 arasıdır). Füzemizin ne kadar agresif döneceğini belirler.
- $V_c$: Kapanış Hızı (Mühimmat + Hedef)
- $\dot{\lambda}$: Görüş Hattı (Line of Sight - LOS) açısının değişim oranı.
- $\vec{n}$: Dönüş düzlemine dik birim vektör.

**Doktrinsel Kural:** Eğer Görüş Hattı açısı değişmiyorsa ($\dot{\lambda} = 0$), hedef vizörde sabit kalmış ve sadece büyüyorsa, füzemiz hedefle KESİN ÇARPIŞMA (Collision Course) rotasında demektir. GökKalkan'ın `interceptor.py` dosyası tam olarak bu sıfıra yaklaşma ilkesini kodlar.

---
*Gök vatanımızı koruyan matematik tesadüflere yer bırakmaz.*
