# 🎯 TEKNOFEST 2026 Çelikkubbe Hava Savunma Sistemleri Yarışması Şartnamesi ve GökKalkan AI Entegrasyonu

GökKalkan AI, **TEKNOFEST 2026 Çelikkubbe Hava Savunma Sistemleri Yarışması** teknik şartnamesine tam uyumlu bir şekilde, modern harp doktrinleriyle modernize edilmiştir. Bu belge, şartnamede istenen görev aşamalarının GökKalkan AI sisteminde nasıl simüle edildiğini açıklamaktadır.

## 📖 Şartname Özeti

Yarışma üç temel operasyonel aşamadan oluşmaktadır:

### 1️⃣ Aşama 1: Farklı Menzillerde Duran Hedef İmhası
- **Amaç:** Sabit konumda bulunan düşman hedeflerinin hava savunma sistemi ile imha edilmesi.
- **Hedef Tipi:** Sabit / Duran Hedef (F16, Helikopter, Mini İHA, Balistik Füze)
- **Menziller:** Parkur içi **5m, 10m ve 15m** mesafeler.
- **Değerlendirme Puanı:** Bu aşamadaki başarıya göre sistemin temel tespit ve angajman kararlılığı puanlanır.

### 2️⃣ Aşama 2: Sürü Saldırısı ve Hedeflerin İmhası
- **Amaç:** Hava savunma sistemine ya da korunan alana (bataryaya) doğru koordineli olarak gelen "Sürü (Swarm) İHA" saldırısını defetmek.
- **Hedef Tipi:** 3 koldan yaklaşan Kamikaze İHA ve Balistik Füze maketleri.
- **Menziller:** 15m'den başlayıp merkeze yaklaşan hedefler.
- **Sistem Beklentisi:** Sistem, çoklu tehdidi tekilleştirmeli, hedeflerin yörünge/sürü merkezini analiz etmeli ve birimleri kinetik ya da lazer CIWS gibi farklı angajman yöntemleriyle imha edebilmelidir.

### 3️⃣ Aşama 3: Farklı Katmanlardaki Hareketli Hedeflerin İmhası
- **Amaç:** Farklı irtifalarda (katmanlarda) ve farklı hızlarda ilerleyen tehditlerin aynı anda sınıflandırılıp vurulması.
- **Hedef Tipleri:** 1 Düşman maket ve 2 Dost maket (F16, Helikopter, Mini İHA).
- **Menziller:** Parkur sınırları (0-15m) içinde katmanlı savunma.
- **Sistem Beklentisi:** 3D radar izleme, dost unsurları ayıklama (IFF benzeri) ve doğru angajman süresiyle fırlatılma.

---

## 🛠️ GökKalkan AI Şartname Uyumu

Sistemimizin çekirdek mekaniği, yarışmanın üç aşamasını da doğrudan destekleyecek ve aşacak (military-grade) seviyede tasarlanmıştır:

| Şartname Görevi | GökKalkan AI Modülü | Nasıl Sağlanıyor? |
| :--- | :--- | :--- |
| **Aşama-1 (Duran Hedefler)** | `radar.py` & `interceptor.py` | Radar taramamız yavaş veya sabit hedefleri (hız $\approx$ 0) tespit eder ve kinetik önleyiciler hedefe saniyeler içinde kilitlenir. |
| **Aşama-2 (Sürü Saldırısı)** | `Boids Algoritması` & `CIWS` | Sistemi özel Boids (Flocking) algoritması ile aynı anda 5-12 adet V ve otonom formasyonlu İHA simülasyonu üretir (`tara_suru_saldirisi` metodu). Hedefler yaklaştığında füzeler veya enerji silahları (Lazer-CIWS) devreye girer. |
| **Aşama-3 (Katmanlı Savunma)** | `AI Sınıflandırma` & `Kalman Filresi` | Radarımız 3D hacimde X, Y ve Z koordinatlarını tarar. Random Forest modelimiz, seyir füzesi (hızlı, yüksek) ile İHA'ları (yavaş, alçak) eş zamanlı olarak algılayıp tehdit endeksini önceliklendirir. |
| **Puanlama Kriterleri** | `telemetry.py` | Başarıyla imha edilen (Hit-to-Kill Onaylı) hedefler anbean kaydedilir ve yarışma jürisine rapor formatında sunulabilir. |

## 🚀 Sonuç
GökKalkan AI, TEKNOFEST 2026 için sadece asgari müşterekleri sağlayan bir betik değil, aynı zamanda siber harp, EH (Elektronik Harp / Jammer) ve yağmur (Weather Attenuation) gibi çevresel zorlukları barındıran; Çelikkubbe'nin beklentilerinin ötesinde yüksek sadakatli bir Hava Savunma Doktrini simülasyonudur.
