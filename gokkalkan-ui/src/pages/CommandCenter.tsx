import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { AlertCircle, Zap, Target, Radar, AlertTriangle } from 'lucide-react';

/**
 * GökKalkan AI Komuta Kontrol Merkezi
 * TEKNOFEST 2026 Çelikkubbe Hava Savunma Sistemleri Yarışması
 * 
 * Tasarım Felsefesi: Militarist-Futuristik
 * - Neon yeşil (#00ff88) ve elektrik mavisi (#00d4ff) aksentler
 * - Koyu arka plan (#0a0e27) profesyonel görünüm
 * - Gerçek zamanlı telemetri ve sistem kontrolleri
 */

interface Target {
  id: string;
  type: 'STATIONARY' | 'SWARM' | 'LAYERED';
  range: number;
  threat: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'DETECTED' | 'LOCKED' | 'ENGAGED' | 'DESTROYED';
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

  // Simüle et sistem metriklerini
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        battery: Math.max(prev.battery - 0.1, 0),
        cpu: Math.random() * 40 + 10,
        snr: Math.random() * 10 + 85,
        temperature: Math.random() * 15 + 35,
        interceptorsReady: Math.floor(Math.random() * 3) + 10,
      }));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleStageChange = (stage: 1 | 2 | 3) => {
    setCurrentStage(stage);
    // Aşamaya göre hedefleri güncelle
    if (stage === 1) {
      setTargets([
        { id: 'T001', type: 'STATIONARY', range: 5, threat: 'MEDIUM', status: 'DETECTED' },
        { id: 'T002', type: 'STATIONARY', range: 10, threat: 'HIGH', status: 'LOCKED' },
        { id: 'T003', type: 'STATIONARY', range: 15, threat: 'MEDIUM', status: 'DETECTED' },
      ]);
    } else if (stage === 2) {
      setTargets([
        { id: 'S001', type: 'SWARM', range: 8, threat: 'HIGH', status: 'DETECTED' },
        { id: 'S002', type: 'SWARM', range: 10, threat: 'HIGH', status: 'LOCKED' },
        { id: 'S003', type: 'SWARM', range: 12, threat: 'HIGH', status: 'DETECTED' },
        { id: 'S004', type: 'SWARM', range: 14, threat: 'MEDIUM', status: 'DETECTED' },
      ]);
    } else {
      setTargets([
        { id: 'L001', type: 'LAYERED', range: 3, threat: 'HIGH', status: 'LOCKED' },
        { id: 'L002', type: 'LAYERED', range: 8, threat: 'MEDIUM', status: 'DETECTED' },
        { id: 'L003', type: 'LAYERED', range: 15, threat: 'HIGH', status: 'DETECTED' },
      ]);
    }
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
              <p className="text-xs text-muted-foreground">V5.0 3D TACTICAL COMMAND CENTER</p>
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
                onClick={() => setAutoFire(!autoFire)}
                variant={autoFire ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                AUTO-FIRE: {autoFire ? 'ENABLED' : 'DISABLED'}
              </Button>
              <Button 
                onClick={() => setRadarEmission(!radarEmission)}
                variant={radarEmission ? 'default' : 'outline'}
                className="w-full text-xs"
              >
                RADAR EMISSION: {radarEmission ? 'ON' : 'OFF'}
              </Button>
              <Button 
                onClick={() => setWeatherActive(!weatherActive)}
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
                variant="default"
                className="w-full text-xs bg-yellow-900 hover:bg-yellow-800 text-yellow-300"
              >
                MANUAL FIRE OVERRIDE
              </Button>
              <Button 
                variant="default"
                className="w-full text-xs bg-orange-900 hover:bg-orange-800 text-orange-300"
              >
                FORCE SWARM ATTACK
              </Button>
              <Button 
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
                <span className="text-secondary font-mono">AUTONOMOUS</span>
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
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );
}
