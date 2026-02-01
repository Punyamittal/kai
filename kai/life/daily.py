"""
Kai Daily Life - Sleep, Reflect, Work, Social, Create, Rest.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

from kai.config import KaiConfig


class Phase(Enum):
    SLEEP = "sleep"
    REFLECT = "reflect"
    WORK = "work"
    SOCIAL = "social"
    CREATE = "create"
    REST = "rest"


@dataclass
class DailySchedule:
    sleep: tuple = (0, 7)      # 12am-7am
    reflect: tuple = (7, 8)
    work: tuple = (9, 14)
    social: tuple = (15, 17)
    create: tuple = (18, 20)
    rest: tuple = (21, 23)


class DailyLifeEngine:
    """
    Daily rhythm - phases with dynamic adjustment.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.schedule = DailySchedule()
        self.current_hour = 8
        self.current_phase = Phase.REFLECT

    def get_phase(self, hour: float) -> Phase:
        """Map hour to phase."""
        if 0 <= hour < 7:
            return Phase.SLEEP
        if 7 <= hour < 8:
            return Phase.REFLECT
        if 9 <= hour < 14:
            return Phase.WORK
        if 15 <= hour < 17:
            return Phase.SOCIAL
        if 18 <= hour < 20:
            return Phase.CREATE
        if 21 <= hour < 24 or 0 <= hour < 1:
            return Phase.REST
        return Phase.REFLECT

    def adjust_for_state(self, burnout: float, loneliness: float, energy: float) -> Phase:
        """Dynamic phase override based on state."""
        if burnout > 0.7:
            return Phase.REST
        if loneliness > 0.8:
            return Phase.SOCIAL
        if energy > 0.8:
            return Phase.WORK
        return self.current_phase
