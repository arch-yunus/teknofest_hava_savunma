import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AlertCircle, Zap, Target, Radar, AlertTriangle } from 'lucide-react';
import { trpc } from '@/lib/trpc';

/**
 * GökKalkan AI Komuta Kontrol Merkezi
 * TEKNOFEST 2026 Çelikkubbe Hava Savunma Sistemleri Yarışması
 * 
 * Tasarım Felsefesi: Militarist-Futuristik
 * - Neon yeşil (#00ff88) ve elektrik mavisi (#00d4ff) aksentler
 * - Koyu arka plan (#0a0e27) profesyonel görünüm
 * - Gerçek zamanlı telemetri ve sistem kontrolleri
 * - Simulasyona bağlı veri akışı
 */

interface Target {
  id: string;
  type: 'STATIONARY' | 'SWARM' | 'LAYERED';
  range: number;
  threat: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'DETECTED' | 'LOCKED' | 'ENGAGED' | 'DESTROYED';
  x?: number;
  y?: number;
  z?: number;
  hiz?: number;
  irtifa?: number;
}

interface SystemMetrics {
  battery: number;
  cpu: number;
  snr: number;
  temperature: number;
  interceptorsReady: number;
}

export default function CommandCenter() {
  const [currentStage, setCurrentStage] = useState<1 | 2 | 3>(1);
  const [systemOnline, setSystemOnline] = useState(true);
  const [autoFire, setAutoFire] = useState(true);
  const [radarEmission, setRadarEmission] = useState(true);
  const [weatherActive, setWeatherActive] = useState(false);
  
  const [targets, setTargets] = useState<Target[]>([
    { id: 'T001', type: 'STATIONARY', range: 5, threat: 'MEDIUM', status: 'DETECTED' },
    { id: 'T002', type: 'STATIONARY', range: 10, threat: 'HIGH', status: 'LOCKED' },
    { id: 'T003', type: 'STATIONARY', range: 15, threat: 'MEDIUM', status: 'DETECTED' },
  ]);

  const [metrics, setMetrics] = useState<SystemMetrics>({
    battery: 100,
    cpu: 15,
    snr: 95,
    temperature: 42,
    interceptorsReady: 12,
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
          type: t.tip === 'STATIONARY' ? 'STATIONARY' : t.tip === 'SWARM' ? 'SWARM' : 'LAYERED',
          range: Math.round(t.mesafe),
          threat: t.oncelik === 'KRİTİK' ? 'HIGH' : t.oncelik === 'YUKSEK' ? 'HIGH' : t.oncelik === 'ORTA' ? 'MEDIUM' : 'LOW',
          status: t.karar === 'DESTROYED' ? 'DESTROYED' : t.karar === 'ENGAGED' ? 'ENGAGED' : t.karar === 'LOCKED' ? 'LOCKED' : 'DETECTED',
          x: t.x,
          y: t.y,
          z: t.z,
          hiz: t.hiz,
          irtifa: t.irtifa,
        }));
        setTargets(mappedTargets);
      }

      // Sistem sağlığını güncelle
      if (data.system_health) {
        setMetrics({
          battery: data.system_health.battery,
          cpu: data.system_health.cpu,
          snr: data.system_health.snr,
          temperature: data.system_health.temperature,
          interceptorsReady: data.system_health.interceptorsReady,
        });
      }

      // Sistem durumunu güncelle
      setCurrentStage(data.current_stage as 1 | 2 | 3);
      setAutoFire(data.auto_fire_enabled);
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

  const handleStageChange = async (stage: 1 | 2 | 3) => {
    setCurrentStage(stage);
    const actionMap = {
      1: 'set_stage_1',
      2: 'set_stage_2',
      3: 'set_stage_3',
    };
    await sendCommand.mutateAsync({
      action: actionMap[stage] as any,
    });
  };

  const handleToggleAutoFire = async () => {
    await sendCommand.mutateAsync({
      action: 'toggle_auto_fire',
    });
    setAutoFire(!autoFire);
  };

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

  const handleManualFire = async () => {
    const lockedTarget = targets.find(t => t.status === 'LOCKED');
    await sendCommand.mutateAsync({
      action: 'manual_fire',
      target_id: lockedTarget?.id,
    });
  };

  const handleForceSwarm = async () => {
    await sendCommand.mutateAsync({
      action: 'force_swarm',
    });
  };

  const handleEmergencyStop = async () => {
    await sendCommand.mutateAsync({
      action: 'trigger_estop',
    });
  };

  const getThreatColor = (threat: string) => {
    switch (threat) {
      case 'HIGH': return 'text-red-500';
      case 'MEDIUM': return 'text-yellow-500';
      case 'LOW': return 'text-green-500';
      default: return 'text-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'DESTROYED': return 'bg-green-900 text-green-300';
      case 'ENGAGED': return 'bg-orange-900 text-orange-300';
      case 'LOCKED': return 'bg-red-900 text-red-300';
      case 'DETECTED': return 'bg-blue-900 text-blue-300';
      default: return 'bg-gray-900 text-gray-300';
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Background Grid Effect */}
      <div className="fixed inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(0, 255, 136, 0.05) 25%, rgba(0, 255, 136, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 136, 0.05) 75%, rgba(0, 255, 136, 0.05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(0, 255, 136, 0.05) 25%, rgba(0, 255, 136, 0.05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 136, 0.05) 75%, rgba(0, 255, 136, 0.05) 76%, transparent 77%, transparent)',
        backgroundSize: '50px 50px'
      }} />

      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Radar className="w-8 h-8 text-primary animate-pulse" />
            <div>
              <h1 className="text-2xl font-bold text-primary">GÖKKALKAN AI</h1>
              <p className="text-xs text-muted-foreground">V5.0 3D TACTICAL COMMAND CENTER - SIMULATION LINKED</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1 rounded border ${systemOnline ? 'border-primary bg-primary/10' : 'border-destructive bg-destructive/10'}`}>
              <div className={`w-2 h-2 rounded-full ${systemOnline ? 'bg-primary animate-pulse' : 'bg-destructive'}`} />
              <span className="text-sm">{systemOnline ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex gap-4 p-4 container mx-auto">
        {/* Left Sidebar - Telemetry */}
        <aside className="w-80 space-y-4">
          {/* System Health */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              SYSTEM HEALTH
            </h2>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">BATTERY</span>
                  <span className="text-primary">{metrics.battery.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${metrics.battery}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">PROCESSOR</span>
                  <span className="text-secondary">{metrics.cpu.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-secondary transition-all"
                    style={{ width: `${metrics.cpu}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">SIGNAL SNR</span>
                  <span className="text-primary">{metrics.snr.toFixed(1)}%</span>
                </div>
                <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${metrics.snr}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">TEMPERATURE</span>
                  <span className="text-yellow-500">{metrics.temperature.toFixed(1)}°C</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Target Intel */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-4 flex items-center gap-2">
              <Target className="w-4 h-4" />
              TARGET INTEL ({targets.length})
            </h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {targets.map(target => (
                <div key={target.id} className="text-xs p-2 bg-muted/30 rounded border border-border hover:border-primary/50 transition-colors">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono font-bold">{target.id}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(target.status)}`}>
                      {target.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-muted-foreground">
                    <div>TYPE: {target.type}</div>
                    <div className={getThreatColor(target.threat)}>THREAT: {target.threat}</div>
                    <div>RANGE: {target.range}m</div>
                    {target.hiz && <div>SPEED: {target.hiz.toFixed(0)} km/h</div>}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* System Info */}
          <Card className="bg-card border-border p-4 text-xs text-muted-foreground">
            <p>C2 NODE: SECTOR 7</p>
            <p>INTERCEPTORS: {metrics.interceptorsReady} READY</p>
            <p>TEMP: {metrics.temperature.toFixed(1)}°C</p>
            <p className="mt-2 text-primary">SIMULATION ACTIVE</p>
          </Card>
        </aside>

        {/* Center - Main Display */}
        <main className="flex-1 space-y-4">
          {/* Hero Image */}
          <Card className="bg-card border-border overflow-hidden h-96">
            <img 
              src="https://d2xsxph8kpxj0f.cloudfront.net/310519663274973023/amgFZtxC2LKhCABLsBVbfV/gokkalkan-hero-3d-radar-cT2eyHNNXavqpzXKuWfCpc.webp"
              alt="3D Radar Display"
              className="w-full h-full object-cover"
            />
          </Card>

          {/* Stage Selection */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3">OPERATIONAL STAGES</h2>
            <div className="grid grid-cols-3 gap-3">
              <Button 
                onClick={() => handleStageChange(1)}
                variant={currentStage === 1 ? 'default' : 'outline'}
                className={currentStage === 1 ? 'bg-primary text-primary-foreground' : ''}
              >
                STAGE-1
                <br />
                <span className="text-xs">(Stationary)</span>
              </Button>
              <Button 
                onClick={() => handleStageChange(2)}
                variant={currentStage === 2 ? 'default' : 'outline'}
                className={currentStage === 2 ? 'bg-primary text-primary-foreground' : ''}
              >
                STAGE-2
                <br />
                <span className="text-xs">(Swarm)</span>
              </Button>
              <Button 
                onClick={() => handleStageChange(3)}
                variant={currentStage === 3 ? 'default' : 'outline'}
                className={currentStage === 3 ? 'bg-primary text-primary-foreground' : ''}
              >
                STAGE-3
                <br />
                <span className="text-xs">(Layered)</span>
              </Button>
            </div>
          </Card>

          {/* Stage Info */}
          <Card className="bg-card border-border p-4">
            {currentStage === 1 && (
              <div>
                <h3 className="text-sm font-bold text-primary mb-2">AŞAMA 1: DURAN HEDEF İMHASI</h3>
                <p className="text-xs text-muted-foreground">
                  Sabit konumda bulunan düşman hedeflerinin hava savunma sistemi ile imha edilmesi. 
                  Menziller: 5m, 10m ve 15m. Sistem temel tespit ve angajman kararlılığı puanlanır.
                </p>
              </div>
            )}
            {currentStage === 2 && (
              <div>
                <h3 className="text-sm font-bold text-primary mb-2">AŞAMA 2: SÜRÜ SALDIRISI</h3>
                <p className="text-xs text-muted-foreground">
                  3 koldan yaklaşan Kamikaze İHA ve Balistik Füze maketleri. Sistem çoklu tehdidi 
                  tekilleştirmeli ve birimleri kinetik ya da lazer CIWS gibi farklı angajman yöntemleriyle imha edebilmelidir.
                </p>
              </div>
            )}
            {currentStage === 3 && (
              <div>
                <h3 className="text-sm font-bold text-primary mb-2">AŞAMA 3: KATMANLI SAVUNMA</h3>
                <p className="text-xs text-muted-foreground">
                  Farklı irtifalarda ve hızlarda ilerleyen tehditlerin aynı anda sınıflandırılıp vurulması. 
                  3D radar izleme, dost/düşman ayrımı ve doğru angajman süresiyle fırlatılma.
                </p>
              </div>
            )}
          </Card>
        </main>

        {/* Right Sidebar - Controls */}
        <aside className="w-80 space-y-4">
          {/* Control Panel */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-4">C2 OVERRIDE PROTOCOLS</h2>
            <div className="space-y-3">
              <Button 
                onClick={handleToggleAutoFire}
                variant={autoFire ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                AUTO-FIRE: {autoFire ? 'ENABLED' : 'DISABLED'}
              </Button>
              <Button 
                onClick={handleToggleRadarEmission}
                variant={radarEmission ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                RADAR EMISSION: {radarEmission ? 'ON' : 'OFF'}
              </Button>
              <Button 
                onClick={handleToggleWeather}
                variant={weatherActive ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                WEATHER: {weatherActive ? 'ACTIVE' : 'INACTIVE'}
              </Button>
            </div>
          </Card>

          {/* Action Buttons */}
          <Card className="bg-card border-border p-4">
            <div className="space-y-3">
              <Button 
                onClick={handleManualFire}
                variant="default"
                className="w-full text-xs bg-yellow-900 hover:bg-yellow-800 text-yellow-300"
              >
                MANUAL FIRE OVERRIDE
              </Button>
              <Button 
                onClick={handleForceSwarm}
                variant="default"
                className="w-full text-xs bg-orange-900 hover:bg-orange-800 text-orange-300"
              >
                FORCE SWARM ATTACK
              </Button>
              <Button 
                onClick={handleEmergencyStop}
                variant="default"
                className="w-full text-xs bg-red-900 hover:bg-red-800 text-red-300 font-bold"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                EMERGENCY STOP
              </Button>
            </div>
          </Card>

          {/* Status Display */}
          <Card className="bg-card border-border p-4">
            <h2 className="text-sm font-bold text-primary mb-3 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              SYSTEM STATUS
            </h2>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">CURRENT PHASE:</span>
                <span className="text-primary font-mono">STAGE-{currentStage}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">ENGAGEMENT MODE:</span>
                <span className="text-secondary font-mono">{autoFire ? 'AUTONOMOUS' : 'MANUAL'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">TARGETS LOCKED:</span>
                <span className="text-primary font-mono">{targets.filter(t => t.status === 'LOCKED').length}/{targets.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">SYSTEM STATUS:</span>
                <span className={systemOnline ? 'text-primary' : 'text-destructive'}>
                  {systemOnline ? 'OPERATIONAL' : 'OFFLINE'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">SIMULATION:</span>
                <span className="text-primary">CONNECTED</span>
              </div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}
