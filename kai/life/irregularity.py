"""
Kai Irregularity Engine - Chaos, variability, procrastination, flow.
"""

import random
from typing import Optional
from dataclasses import dataclass

from kai.config import DAY_TYPES, KaiConfig


@dataclass
class DayState:
    day_type: str
    energy: float
    in_flow: bool
    procrastinating: bool
    disruption: Optional[str] = None


class IrregularityEngine:
    """
    Makes Kai's life unpredictable - like humans.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()

    def roll_day(
        self,
        mental_health: float = 0.7,
    ) -> DayState:
        """Roll random day type and energy."""
        # Weight by mental health
        if mental_health < 0.4:
            pool = ["lazy", "lonely", "burnt_out", "anxious"]
        elif mental_health > 0.8:
            pool = ["productive", "inspired", "adventurous", "social"]
        else:
            pool = DAY_TYPES

        day_type = random.choice(pool)
        energy = 0.5 + random.uniform(-0.2, 0.2)

        # Flow state
        in_flow = random.random() < 0.1 and energy > 0.6

        # Procrastination
        procrastinating = random.random() < 0.15

        # Disruption
        disruption = None
        if random.random() < self.config.irregularity_chance:
            disruptions = [
                "client_crisis", "friend_conflict", "unexpected_success",
                "opportunity", "loss", "illness"
            ]
            disruption = random.choice(disruptions)

        return DayState(
            day_type=day_type,
            energy=max(0, min(1, energy)),
            in_flow=in_flow,
            procrastinating=procrastinating,
            disruption=disruption,
        )
