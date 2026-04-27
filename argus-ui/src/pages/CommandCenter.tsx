import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AlertCircle, Zap, Target, Radar, AlertTriangle, Shield, Layers } from 'lucide-react';
import { trpc } from '@/lib/trpc';
import { LayeredDefenseVisualization } from '@/components/LayeredDefenseVisualization';

/**
 * ARGUS AI - Çok Katmanlı Hava Savunma Komuta Kontrol Merkezi
 * İsrail'in katmanlı savunma sistemine benzer mimariye dayalı
 * TEKNOFEST 2026 Çelikkubbe Hava Savunma Sistemleri Yarışması
 * 
 * Tasarım: Militarist-Futuristik, Türkçe Terminoloji
 * Katmanlar:
 * 1. Yıldırım (500+ km) - Uzak menzil
 * 2. Hançer (100-300 km) - Orta-uzak menzil
 * 3. Kalkan (4-70 km) - Kısa menzil
 * 4. Işın (5-10 km) - Çok yakın menzil
 * 5. Avcı (50+ km) - Hava katmanı
 */

interface DefenseLayer {
  id: number;
  adı: string;
  menzil: string;
  irtifa: string;
  durum: 'HAZIR' | 'AKTİF' | 'BAKIMI' | 'ARIZA';
  mühimmat: number;
  maksimumMühimmat: number;
  işlemciYükü: number;
  sıcaklık: number;
  engajmanSayısı: number;
}

interface Target {
  id: string;
  tip: 'ROKET' | 'FÜZELİ' | 'UÇAK' | 'İHA' | 'MORTARLAR' | 'BALISTIK';
  menzil: number;
  irtifa: number;
  hız: number;
  tehdit: 'DÜŞÜK' | 'ORTA' | 'YÜKSEK' | 'KRİTİK';
  durum: 'TESPİT' | 'KİLİTLİ' | 'ENGAJMAN' | 'İMHA';
  atanmışKatman: number | null;
  x?: number;
  y?: number;
  z?: number;
}

interface SystemMetrics {
  batarya: number;
  işlemci: number;
  snr: number;
  sıcaklık: number;
  toplamMühimmat: number;
}

export default function CommandCenter() {
  const [defenseMode, setDefenseMode] = useState<'OTOMATİK' | 'YARI-OTOMATİK' | 'MANUEL'>('OTOMATİK');
  const [systemOnline, setSystemOnline] = useState(true);
  const [radarEmission, setRadarEmission] = useState(true);
  const [weatherActive, setWeatherActive] = useState(false);
  
  const [defenseLayers, setDefenseLayers] = useState<DefenseLayer[]>([
    {
      id: 1,
      adı: 'YILDIRIM',
      menzil: '500+ km',
      irtifa: 'Uzay Atmosferi',
      durum: 'HAZIR',
      mühimmat: 8,
      maksimumMühimmat: 12,
      işlemciYükü: 12,
      sıcaklık: 38,
      engajmanSayısı: 0,
    },
    {
      id: 2,
      adı: 'HANÇER',
      menzil: '100-300 km',
      irtifa: 'Orta Atmosfer',
      durum: 'HAZIR',
      mühimmat: 16,
      maksimumMühimmat: 24,
      işlemciYükü: 18,
      sıcaklık: 42,
      engajmanSayısı: 0,
    },
    {
      id: 3,
      adı: 'KALKAN',
      menzil: '4-70 km',
      irtifa: 'Düşük Atmosfer',
      durum: 'HAZIR',
      mühimmat: 32,
      maksimumMühimmat: 48,
      işlemciYükü: 25,
      sıcaklık: 48,
      engajmanSayısı: 0,
    },
    {
      id: 4,
      adı: 'IŞIN',
      menzil: '5-10 km',
      irtifa: 'Çok Düşük Atmosfer',
      durum: 'HAZIR',
      mühimmat: 100,
      maksimumMühimmat: 100,
      işlemciYükü: 8,
      sıcaklık: 35,
      engajmanSayısı: 0,
    },
    {
      id: 5,
      adı: 'AVCI',
      menzil: '50+ km',
      irtifa: 'Tüm Irtifalar',
      durum: 'HAZIR',
      mühimmat: 12,
      maksimumMühimmat: 12,
      işlemciYükü: 35,
      sıcaklık: 52,
      engajmanSayısı: 0,
    },
  ]);

  const [targets, setTargets] = useState<Target[]>([
    {
      id: 'H001',
      tip: 'ROKET',
      menzil: 35,
      irtifa: 2500,
      hız: 450,
      tehdit: 'ORTA',
      durum: 'TESPİT',
      atanmışKatman: null,
    },
    {
      id: 'H002',
      tip: 'BALISTIK',
      menzil: 250,
      irtifa: 45000,
      hız: 2800,
      tehdit: 'KRİTİK',
      durum: 'KİLİTLİ',
      atanmışKatman: 1,
    },
    {
      id: 'H003',
      tip: 'İHA',
      menzil: 15,
      irtifa: 1200,
      hız: 180,
      tehdit: 'DÜŞÜK',
      durum: 'TESPİT',
      atanmışKatman: null,
    },
  ]);

  const [metrics, setMetrics] = useState<SystemMetrics>({
    batarya: 100,
    işlemci: 22,
    snr: 92,
    sıcaklık: 43,
    toplamMühimmat: 68,
  });

  // tRPC hooks
  const simulationData = trpc.simulation.getLatestData.useQuery();
  const sendCommand = trpc.simulation.sendCommand.useMutation();

  // Simulasyon verilerini güncelle
  useEffect(() => {
    if (simulationData.data) {
      const data = simulationData.data;
      
      // Hedefleri güncelle
      if (data.targets && data.targets.length > 0) {
        const mappedTargets: Target[] = data.targets.map((t: any) => ({
          id: t.id,
          tip: t.tip === 'STATIONARY' ? 'ROKET' : t.tip === 'SWARM' ? 'BALISTIK' : 'İHA',
          menzil: Math.round(t.mesafe),
          irtifa: Math.round(t.irtifa || 2000),
          hız: Math.round(t.hiz || 0),
          tehdit: t.oncelik === 'KRİTİK' ? 'KRİTİK' : t.oncelik === 'YUKSEK' ? 'YÜKSEK' : t.oncelik === 'ORTA' ? 'ORTA' : 'DÜŞÜK',
          durum: t.karar === 'DESTROYED' ? 'İMHA' : t.karar === 'ENGAGED' ? 'ENGAJMAN' : t.karar === 'LOCKED' ? 'KİLİTLİ' : 'TESPİT',
          atanmışKatman: null,
          x: t.x,
          y: t.y,
          z: t.z,
        }));
        setTargets(mappedTargets);
      }

      // Sistem sağlığını güncelle
      if (data.system_health) {
        setMetrics({
          batarya: data.system_health.battery,
          işlemci: data.system_health.cpu,
          snr: data.system_health.snr,
          sıcaklık: data.system_health.temperature,
          toplamMühimmat: data.system_health.muhimmat,
        });
      }

      // Sistem durumunu güncelle
      setRadarEmission(data.radar_emission);
      setWeatherActive(data.weather === 'RAIN');
    }
  }, [simulationData.data]);

  // Simulasyon verilerini periyodik olarak yenile
  useEffect(() => {
    const interval = setInterval(() => {
      simulationData.refetch();
    }, 1000);
    return () => clearInterval(interval);
  }, [simulationData]);

  const handleToggleRadarEmission = async () => {
    await sendCommand.mutateAsync({
      action: 'toggle_radar_emission',
    });
    setRadarEmission(!radarEmission);
  };

  const handleToggleWeather = async () => {
    await sendCommand.mutateAsync({
      action: 'toggle_weather',
    });
    setWeatherActive(!weatherActive);
  };

  const handleEmergencyStop = async () => {
    await sendCommand.mutateAsync({
      action: 'trigger_estop',
    });
  };

  const getTehditRengi = (tehdit: string) => {
    switch (tehdit) {
      case 'KRİTİK': return 'text-red-500 font-bold';
      case 'YÜKSEK': return 'text-orange-500';
      case 'ORTA': return 'text-yellow-500';
      case 'DÜŞÜK': return 'text-green-500';
      default: return 'text-gray-400';
    }
  };

  const getDurumuRengi = (durum: string) => {
    switch (durum) {
      case 'İMHA': return 'bg-green-900 text-green-300';
      case 'ENGAJMAN': return 'bg-orange-900 text-orange-300';
      case 'KİLİTLİ': return 'bg-red-900 text-red-300';
      case 'TESPİT': return 'bg-blue-900 text-blue-300';
      default: return 'bg-gray-900 text-gray-300';
    }
  };

  const getKatmanDurumuRengi = (durum: string) => {
    switch (durum) {
      case 'HAZIR': return 'border-green-500 bg-green-900/20';
      case 'AKTİF': return 'border-yellow-500 bg-yellow-900/20 animate-pulse';
      case 'BAKIMI': return 'border-orange-500 bg-orange-900/20';
      case 'ARIZA': return 'border-red-500 bg-red-900/20';
      default: return 'border-gray-500 bg-gray-900/20';
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Arka Plan Grid Efekti */}
      <div className="fixed inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(0, 255, 136, 0.05) 25%, rgba(0, 255, 136, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 136, 0.05) 75%, rgba(0, 255, 136, 0.05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 136, 0.05) 25%, rgba(0, 255, 136, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 136, 0.05) 75%, rgba(0, 255, 136, 0.05) 76%, transparent 77%, transparent)',
        backgroundSize: '50px 50px'
      }} />

      {/* Başlık */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Layers className="w-8 h-8 text-primary animate-pulse" />
            <div>
              <h1 className="text-2xl font-bold text-primary">ARGUS AI</h1>
              <p className="text-xs text-muted-foreground">ÇOK KATMANLI HAVA SAVUNMA KOMUTAKONTROLMERKEZİ - SİMÜLASYON BAĞLI</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1 rounded border ${systemOnline ? 'border-primary bg-primary/10' : 'border-destructive bg-destructive/10'}`}>
              <div className={`w-2 h-2 rounded-full ${systemOnline ? 'bg-primary animate-pulse' : 'bg-destructive'}`} />
              <span className="text-sm font-mono">{systemOnline ? 'SİSTEM ÇALIŞIYOR' : 'SİSTEM KAPALI'}</span>
            </div>
            <div className="px-3 py-1 rounded border border-secondary bg-secondary/10">
              <span className="text-sm font-mono">{defenseMode}</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex gap-4 p-4 container mx-auto">
        {/* Sol Kenar - Katman Durumu */}
        <aside className="w-96 space-y-4 max-h-[calc(100vh-120px)] overflow-y-auto">
          {/* Savunma Katmanları */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              SAVUNMA KATMANLARI
            </h2>
            <div className="space-y-3">
              {defenseLayers.map(layer => (
                <div key={layer.id} className={`p-3 rounded border-2 transition-all ${getKatmanDurumuRengi(layer.durum)}`}>
                  <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">{layer.adı}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-mono ${
                        layer.durum === 'HAZIR' ? 'bg-green-900 text-green-300' :
                        layer.durum === 'AKTİF' ? 'bg-yellow-900 text-yellow-300' :
                        layer.durum === 'BAKIMI' ? 'bg-orange-900 text-orange-300' :
                        'bg-red-900 text-red-300'
                      }`}>
                        {layer.durum}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">Engajman: {layer.engajmanSayısı}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                    <div className="text-muted-foreground">
                      <span className="text-primary">Menzil:</span> {layer.menzil}
                    </div>
                    <div className="text-muted-foreground">
                      <span className="text-primary">İrtifa:</span> {layer.irtifa}
                    </div>
                  </div>

                  {/* Mühimmat Barı */}
                  <div className="mb-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">Mühimmat</span>
                      <span className="text-primary font-mono">{layer.mühimmat}/{layer.maksimumMühimmat}</span>
                    </div>
                    <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all"
                        style={{ width: `${(layer.mühimmat / layer.maksimumMühimmat) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* Sistem Metrikleri */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">İşlemci:</span>
                      <span className="text-secondary ml-1">{layer.işlemciYükü}%</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Sıcaklık:</span>
                      <span className={layer.sıcaklık > 50 ? 'text-orange-500 ml-1' : 'text-green-500 ml-1'}>
                        {layer.sıcaklık}°C
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Sistem Metrikleri */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              SİSTEM METRİKLERİ
            </h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Batarya</span>
                  <span className="text-primary">{metrics.batarya.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${metrics.batarya}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">İşlemci</span>
                  <span className="text-secondary">{metrics.işlemci.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-secondary transition-all"
                    style={{ width: `${metrics.işlemci}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">Sinyal-Gürültü Oranı</span>
                  <span className="text-primary">{metrics.snr.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${metrics.snr}%` }}
                  />
                </div>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">Sıcaklık</span>
                <span className={metrics.sıcaklık > 50 ? 'text-orange-500' : 'text-green-500'}>
                  {metrics.sıcaklık.toFixed(1)}°C
                </span>
              </div>
            </div>
          </Card>
        </aside>

        {/* Merkez - Ana Ekran */}
        <main className="flex-1 space-y-4">
          {/* Çok Katmanlı Savunma Görselleştirmesi */}
          <LayeredDefenseVisualization layers={defenseLayers} targets={targets} />

          {/* 3D Radar Görseli */}
          <Card className="bg-card border-border overflow-hidden h-64">
            <img 
              src="https://d2xsxph8kpxj0f.cloudfront.net/310519663274973023/amgFZtxC2LKhCABLsBVbfV/argus-hero-3d-radar-cT2eyHNNXavqpzXKuWfCpc.webp"
              alt="3D Radar Ekranı"
              className="w-full h-full object-cover"
            />
          </Card>

          {/* Sistem Kontrolleri */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3">SİSTEM KONTROLLERİ</h2>
            <div className="grid grid-cols-3 gap-3">
              <Button 
                onClick={handleToggleRadarEmission}
                variant={radarEmission ? 'default' : 'outline'}
                className="text-xs"
              >
                RADAR YAYINI: {radarEmission ? 'AÇIK' : 'KAPALI'}
              </Button>
              <Button 
                onClick={handleToggleWeather}
                variant={weatherActive ? 'default' : 'outline'}
                className="text-xs"
              >
                HAVA: {weatherActive ? 'AKTİF' : 'PASIF'}
              </Button>
              <Button 
                onClick={handleEmergencyStop}
                variant="default"
                className="text-xs bg-red-900 hover:bg-red-800 text-red-300 font-bold"
              >
                <AlertTriangle className="w-3 h-3 mr-1" />
                ACİL DURDUR
              </Button>
            </div>
          </Card>

          {/* Tehdit Bilgisi */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3 flex items-center gap-2">
              <Target className="w-4 h-4" />
              TEHDİT BİLGİSİ ({targets.length})
            </h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {targets.map(target => (
                <div key={target.id} className="text-xs p-2 bg-muted/30 rounded border border-border hover:border-primary/50 transition-colors">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold">{target.id}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getDurumuRengi(target.durum)}`}>
                      {target.durum}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-muted-foreground mb-1">
                    <div>TİP: {target.tip}</div>
                    <div className={getTehditRengi(target.tehdit)}>TEHDİT: {target.tehdit}</div>
                    <div>MENZIL: {target.menzil} km</div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-muted-foreground">
                    <div>İRTİFA: {target.irtifa} m</div>
                    <div>HIZ: {target.hız} km/h</div>
                    <div>
                      {target.atanmışKatman ? (
                        <span className="text-primary">Katman {target.atanmışKatman}</span>
                      ) : (
                        <span className="text-yellow-500">Atanmamış</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </main>

        {/* Sağ Kenar - İşlem Kontrolleri */}
        <aside className="w-80 space-y-4 max-h-[calc(100vh-120px)] overflow-y-auto">
          {/* Mod Seçimi */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3">ÇALIŞMA MODU</h2>
            <div className="space-y-2">
              <Button 
                onClick={() => setDefenseMode('OTOMATİK')}
                variant={defenseMode === 'OTOMATİK' ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                OTOMATİK
              </Button>
              <Button 
                onClick={() => setDefenseMode('YARI-OTOMATİK')}
                variant={defenseMode === 'YARI-OTOMATİK' ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                YARI-OTOMATİK
              </Button>
              <Button 
                onClick={() => setDefenseMode('MANUEL')}
                variant={defenseMode === 'MANUEL' ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                MANUEL
              </Button>
            </div>
          </Card>

          {/* İşlem Butonları */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3">İŞLEM KONTROLLERİ</h2>
            <div className="space-y-2">
              <Button 
                variant="default"
                className="w-full text-xs bg-yellow-900 hover:bg-yellow-800 text-yellow-300"
              >
                MANUEL ATEŞ
              </Button>
              <Button 
                variant="default"
                className="w-full text-xs bg-orange-900 hover:bg-orange-800 text-orange-300"
              >
                SÜRÜ SALDIRISI
              </Button>
              <Button 
                variant="default"
                className="w-full text-xs bg-purple-900 hover:bg-purple-800 text-purple-300"
              >
                LAZER ENGAJMANI
              </Button>
            </div>
          </Card>

          {/* Sistem Durumu */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              SİSTEM DURUMU
            </h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Çalışma Modu:</span>
                <span className="text-primary font-mono">{defenseMode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Hazır Katmanlar:</span>
                <span className="text-primary font-mono">{defenseLayers.filter(l => l.durum === 'HAZIR').length}/{defenseLayers.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tespit Edilen Tehditler:</span>
                <span className="text-primary font-mono">{targets.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Kilitli Hedefler:</span>
                <span className="text-orange-500 font-mono">{targets.filter(t => t.durum === 'KİLİTLİ').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Engajman Yapılan:</span>
                <span className="text-yellow-500 font-mono">{targets.filter(t => t.durum === 'ENGAJMAN').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">İmha Edilen:</span>
                <span className="text-green-500 font-mono">{targets.filter(t => t.durum === 'İMHA').length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Radar:</span>
                <span className={radarEmission ? 'text-primary' : 'text-destructive'}>
                  {radarEmission ? 'AÇIK' : 'KAPALI'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Sistem:</span>
                <span className={systemOnline ? 'text-primary' : 'text-destructive'}>
                  {systemOnline ? 'ÇALIŞIYOR' : 'KAPALI'}
                </span>
              </div>
            </div>
          </Card>

          {/* Bilgi Paneli */}
          <Card className="bg-card border-border p-4 text-xs text-muted-foreground">
            <p className="mb-2"><span className="text-primary">Komuta Merkezi:</span> SEKTOR-7</p>
            <p className="mb-2"><span className="text-primary">Toplam Mühimmat:</span> {metrics.toplamMühimmat} birim</p>
            <p className="mb-2"><span className="text-primary">Sıcaklık:</span> {metrics.sıcaklık.toFixed(1)}°C</p>
            <p className="mt-3 text-primary border-t border-border pt-2">SİMÜLASYON BAĞLI - AKTIF</p>
          </Card>
        </aside>
      </div>
    </div>
  );
}
