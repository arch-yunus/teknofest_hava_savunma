from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

class MissionStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class Mission:
    """ARGUS Operasyonel Görev Tanımı."""
    id: str
    name: str
    description: str
    target_count: int
    speed_range: tuple  # (min, max) km/h
    alt_range: tuple    # (min, max) km
    rcs_range: tuple    # (min, max) m^2
    is_swarm: bool = False
    has_jammer: bool = False
    has_arm: bool = False
    is_hypersonic: bool = False
    dost_unsur_count: int = 0

class MissionManager:
    """Dinamik görev senaryolarını yöneten merkez."""
    
    MISSIONS = {
        "SWARM_ATTACK": Mission(
            id="SWARM_ATTACK",
            name="Sürü İHA Taarruzu",
            description="15+ adet düşük RCS'li İHA'nın koordineli saldırısı. Alan savunması testi.",
            target_count=18,
            speed_range=(150, 400),
            alt_range=(0.5, 3.0),
            rcs_range=(0.01, 0.1),
            is_swarm=True
        ),
        "BALLISTIC_SALVO": Mission(
            id="BALLISTIC_SALVO",
            name="Balistik Füze Yaylımı",
            description="Yüksek irtifa ve yüksek hızda yaklaşan 4 adet balistik füze.",
            target_count=4,
            speed_range=(3500, 5000),
            alt_range=(25.0, 45.0),
            rcs_range=(0.5, 1.2),
            is_hypersonic=False
        ),
        "HYPERSONIC_THREAT": Mission(
            id="HYPERSONIC_THREAT",
            name="Hipersonik Önleme",
            description="Mach 5+ hızda manevra yapan kritik tehdit. PN Navigasyon testi.",
            target_count=2,
            speed_range=(6200, 8000),
            alt_range=(15.0, 25.0),
            rcs_range=(0.3, 0.8),
            is_hypersonic=True
        ),
        "EW_OPERATIONS": Mission(
            id="EW_OPERATIONS",
            name="Elektronik Harp Altında Savunma",
            description="Yoğun karıştırma ve ghost ekoları içeren karma saldırı.",
            target_count=8,
            speed_range=(600, 1200),
            alt_range=(2.0, 10.0),
            rcs_range=(0.1, 1.0),
            has_jammer=True
        ),
        "HYBRID_ESCORT": Mission(
            id="HYBRID_ESCORT",
            name="Karma Refakat Senaryosu",
            description="Dost unsurların arasından sızmaya çalışan düşman uçakları. IFF testi.",
            target_count=3,
            speed_range=(800, 1500),
            alt_range=(5.0, 12.0),
            rcs_range=(1.0, 5.0),
            dost_unsur_count=3
        )
    }

    @staticmethod
    def get_mission(mission_id: str) -> Optional[Mission]:
        return MissionManager.MISSIONS.get(mission_id)

    @staticmethod
    def list_missions():
        return [{"id": m.id, "name": m.name, "description": m.description} for m in MissionManager.MISSIONS.values()]
