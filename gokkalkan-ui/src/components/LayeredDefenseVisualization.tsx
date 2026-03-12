import { useMemo } from 'react';
import { Card } from '@/components/ui/card';

interface DefenseLayer {
  id: number;
  adı: string;
  menzil: string;
  irtifa: string;
  durum: 'HAZIR' | 'AKTİF' | 'BAKIMI' | 'ARIZA';
  mühimmat: number;
  maksimumMühimmat: number;
}

interface Target {
  id: string;
  menzil: number;
  irtifa: number;
  tehdit: 'DÜŞÜK' | 'ORTA' | 'YÜKSEK' | 'KRİTİK';
  durum: 'TESPİT' | 'KİLİTLİ' | 'ENGAJMAN' | 'İMHA';
}

interface LayeredDefenseVisualizationProps {
  layers: DefenseLayer[];
  targets: Target[];
}

/**
 * Çok Katmanlı Savunma Görselleştirmesi
 * 
 * İsrail'in katmanlı savunma sistemine benzer şekilde,
 * farklı menzil ve irtifada gelen tehditleri gösterir.
 * 
 * Katmanlar (aşağıdan yukarıya):
 * 1. Işın (5-10 km) - Çok yakın
 * 2. Kalkan (4-70 km) - Kısa menzil
 * 3. Hançer (100-300 km) - Orta menzil
 * 4. Yıldırım (500+ km) - Uzak menzil
 * 5. Avcı (50+ km) - Hava katmanı
 */

export function LayeredDefenseVisualization({ layers, targets }: LayeredDefenseVisualizationProps) {
  const layerOrder = useMemo(() => {
    // Katmanları menzile göre sırala (en yakın en altta)
    return [
      layers.find(l => l.adı === 'IŞIN'),
      layers.find(l => l.adı === 'KALKAN'),
      layers.find(l => l.adı === 'HANÇER'),
      layers.find(l => l.adı === 'YILDIRIM'),
      layers.find(l => l.adı === 'AVCI'),
    ].filter(Boolean) as DefenseLayer[];
  }, [layers]);

  const getLayerColor = (durum: string) => {
    switch (durum) {
      case 'HAZIR': return 'from-green-600 to-green-800';
      case 'AKTİF': return 'from-yellow-500 to-yellow-700';
      case 'BAKIMI': return 'from-orange-600 to-orange-800';
      case 'ARIZA': return 'from-red-600 to-red-800';
      default: return 'from-gray-600 to-gray-800';
    }
  };

  const getTehditColor = (tehdit: string) => {
    switch (tehdit) {
      case 'KRİTİK': return '#ef4444';
      case 'YÜKSEK': return '#f97316';
      case 'ORTA': return '#eab308';
      case 'DÜŞÜK': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getDurumuColor = (durum: string) => {
    switch (durum) {
      case 'İMHA': return '#22c55e';
      case 'ENGAJMAN': return '#f97316';
      case 'KİLİTLİ': return '#ef4444';
      case 'TESPİT': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  return (
    <Card className="bg-card border-border p-6 overflow-hidden">
      <h2 className="text-sm font-bold text-primary mb-4">ÇOK KATMANLI SAVUNMA GÖRSELLEŞTİRMESİ</h2>
      
      {/* SVG Görselleştirmesi */}
      <svg viewBox="0 0 800 600" className="w-full border border-border rounded bg-black/30">
        {/* Arka Plan Grid */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(0,255,136,0.05)" strokeWidth="0.5"/>
          </pattern>
          <linearGradient id="layerGradient1" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(34, 197, 94, 0.3)" />
            <stop offset="100%" stopColor="rgba(34, 197, 94, 0.1)" />
          </linearGradient>
          <linearGradient id="layerGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(59, 130, 246, 0.3)" />
            <stop offset="100%" stopColor="rgba(59, 130, 246, 0.1)" />
          </linearGradient>
          <linearGradient id="layerGradient3" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(249, 115, 22, 0.3)" />
            <stop offset="100%" stopColor="rgba(249, 115, 22, 0.1)" />
          </linearGradient>
          <linearGradient id="layerGradient4" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(234, 179, 8, 0.3)" />
            <stop offset="100%" stopColor="rgba(234, 179, 8, 0.1)" />
          </linearGradient>
          <linearGradient id="layerGradient5" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(239, 68, 68, 0.3)" />
            <stop offset="100%" stopColor="rgba(239, 68, 68, 0.1)" />
          </linearGradient>
        </defs>

        {/* Arka Plan */}
        <rect width="800" height="600" fill="url(#grid)" />

        {/* Katmanlar (aşağıdan yukarıya) */}
        {layerOrder.map((layer, index) => {
          if (!layer) return null;
          
          const layerHeight = 100;
          const yPos = 500 - (index * layerHeight);
          const gradientId = `layerGradient${index + 1}`;
          
          return (
            <g key={layer.id}>
              {/* Katman Arka Planı */}
              <rect
                x="20"
                y={yPos}
                width="760"
                height={layerHeight}
                fill={`url(#${gradientId})`}
                stroke={layer.durum === 'HAZIR' ? '#22c55e' : layer.durum === 'AKTİF' ? '#eab308' : layer.durum === 'BAKIMI' ? '#f97316' : '#ef4444'}
                strokeWidth="2"
              />

              {/* Katman Adı ve Bilgisi */}
              <text x="40" y={yPos + 25} fontSize="14" fontWeight="bold" fill="#00ff88" fontFamily="monospace">
                {layer.adı}
              </text>
              <text x="40" y={yPos + 45} fontSize="11" fill="#00d4ff" fontFamily="monospace">
                Menzil: {layer.menzil} | İrtifa: {layer.irtifa}
              </text>
              <text x="40" y={yPos + 65} fontSize="11" fill="#00d4ff" fontFamily="monospace">
                Mühimmat: {layer.mühimmat}/{layer.maksimumMühimmat}
              </text>

              {/* Katman Durumu */}
              <rect
                x="700"
                y={yPos + 15}
                width="60"
                height="25"
                fill={layer.durum === 'HAZIR' ? 'rgba(34, 197, 94, 0.3)' : layer.durum === 'AKTİF' ? 'rgba(234, 179, 8, 0.3)' : layer.durum === 'BAKIMI' ? 'rgba(249, 115, 22, 0.3)' : 'rgba(239, 68, 68, 0.3)'}
                stroke={layer.durum === 'HAZIR' ? '#22c55e' : layer.durum === 'AKTİF' ? '#eab308' : layer.durum === 'BAKIMI' ? '#f97316' : '#ef4444'}
                strokeWidth="1"
                rx="3"
              />
              <text x="730" y={yPos + 32} fontSize="10" fontWeight="bold" fill={layer.durum === 'HAZIR' ? '#22c55e' : layer.durum === 'AKTİF' ? '#eab308' : layer.durum === 'BAKIMI' ? '#f97316' : '#ef4444'} fontFamily="monospace" textAnchor="middle">
                {layer.durum}
              </text>
            </g>
          );
        })}

        {/* Hedefler (Tehditler) */}
        {targets.map((target, index) => {
          // Hedefin menzilini katmanlara göre konumlandır
          let layerIndex = 0;
          if (target.menzil > 300) layerIndex = 3; // Yıldırım
          else if (target.menzil > 70) layerIndex = 2; // Hançer
          else if (target.menzil > 10) layerIndex = 1; // Kalkan
          else layerIndex = 0; // Işın

          const yPos = 500 - (layerIndex * 100) + 50;
          const xPos = 100 + (index * 60) % 600;
          const radius = target.tehdit === 'KRİTİK' ? 8 : target.tehdit === 'YÜKSEK' ? 6 : target.tehdit === 'ORTA' ? 5 : 4;

          return (
            <g key={target.id}>
              {/* Hedef Noktası */}
              <circle
                cx={xPos}
                cy={yPos}
                r={radius}
                fill={getDurumuColor(target.durum)}
                opacity="0.8"
              />
              {/* Hedef Halo (Kilitli hedefler için) */}
              {target.durum === 'KİLİTLİ' && (
                <circle
                  cx={xPos}
                  cy={yPos}
                  r={radius + 8}
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="1"
                  opacity="0.5"
                  strokeDasharray="2,2"
                />
              )}
              {/* Hedef Etiketi */}
              <text x={xPos} y={yPos + 15} fontSize="9" fill="#00ff88" fontFamily="monospace" textAnchor="middle">
                {target.id}
              </text>
            </g>
          );
        })}

        {/* Efsane (Legend) */}
        <g>
          <rect x="20" y="20" width="200" height="140" fill="rgba(0, 0, 0, 0.6)" stroke="#00d4ff" strokeWidth="1" rx="3" />
          
          <text x="30" y="40" fontSize="12" fontWeight="bold" fill="#00ff88" fontFamily="monospace">
            EFSANE
          </text>

          {/* Tehdit Seviyeleri */}
          <circle cx="30" cy="60" r="3" fill="#ef4444" />
          <text x="40" y="65" fontSize="10" fill="#ffffff" fontFamily="monospace">
            KRİTİK
          </text>

          <circle cx="30" cy="80" r="3" fill="#f97316" />
          <text x="40" y="85" fontSize="10" fill="#ffffff" fontFamily="monospace">
            YÜKSEK
          </text>

          <circle cx="30" cy="100" r="3" fill="#eab308" />
          <text x="40" y="105" fontSize="10" fill="#ffffff" fontFamily="monospace">
            ORTA
          </text>

          <circle cx="30" cy="120" r="3" fill="#22c55e" />
          <text x="40" y="125" fontSize="10" fill="#ffffff" fontFamily="monospace">
            DÜŞÜK
          </text>

          {/* Durum Göstergeleri */}
          <rect x="130" y="55" width="4" height="4" fill="#22c55e" />
          <text x="140" y="60" fontSize="10" fill="#ffffff" fontFamily="monospace">
            İMHA
          </text>

          <rect x="130" y="75" width="4" height="4" fill="#f97316" />
          <text x="140" y="80" fontSize="10" fill="#ffffff" fontFamily="monospace">
            ENGAJMAN
          </text>

          <rect x="130" y="95" width="4" height="4" fill="#ef4444" />
          <text x="140" y="100" fontSize="10" fill="#ffffff" fontFamily="monospace">
            KİLİTLİ
          </text>

          <rect x="130" y="115" width="4" height="4" fill="#3b82f6" />
          <text x="140" y="120" fontSize="10" fill="#ffffff" fontFamily="monospace">
            TESPİT
          </text>
        </g>
      </svg>

      {/* Katman Açıklamaları */}
      <div className="mt-4 grid grid-cols-5 gap-2 text-xs">
        {layerOrder.map(layer => (
          layer && (
            <div key={layer.id} className="p-2 bg-muted/30 rounded border border-border">
              <div className="font-bold text-primary">{layer.adı}</div>
              <div className="text-muted-foreground text-xs">
                {layer.menzil}
              </div>
              <div className={`text-xs font-mono ${
                layer.durum === 'HAZIR' ? 'text-green-400' :
                layer.durum === 'AKTİF' ? 'text-yellow-400' :
                layer.durum === 'BAKIMI' ? 'text-orange-400' :
                'text-red-400'
              }`}>
                {layer.durum}
              </div>
            </div>
          )
        ))}
      </div>
    </Card>
  );
}
