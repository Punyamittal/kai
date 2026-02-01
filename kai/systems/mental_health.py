"""
Kai Mental Health System - PHI, trauma processing, rest mode, self-soothing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

from kai.config import KaiConfig

# Self-soothing: when sadness+fear stay high for N turns, Kai triggers recovery
LOW_MOOD_THRESHOLD = 0.6
LOW_MOOD_TURNS_TRIGGER = 5


@dataclass
class MentalHealthIndex:
    stress: float = 0.2
    self_worth: float = 0.7
    hope: float = 0.8
    burnout: float = 0.1
    loneliness: float = 0.3
    meaning: float = 0.6

    def overall(self) -> float:
        return (
            (1 - self.stress) * 0.2 +
            self.self_worth * 0.2 +
            self.hope * 0.2 +
            (1 - self.burnout) * 0.2 +
            (1 - self.loneliness) * 0.1 +
            self.meaning * 0.1
        )


class MentalHealthSystem:
    """
    Psychological health, trauma queue, reflection, rest mode.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.phi = MentalHealthIndex()
        self.trauma_queue: List[dict] = []
        self.rest_mode = False
        self.healing_mode = False  # High stress/sadness/shame → reduce interaction, self-care
        self.self_soothing_mode = False  # Stuck in low mood → reflective talk, mental break
        self.low_mood_turns = 0  # Consecutive turns with sadness or fear > threshold

    def update_from_emotions(self, emotions: Dict[str, float]):
        """Sync with emotional engine."""
        self.phi.stress = 0.3 * emotions.get("fear", 0) + 0.3 * emotions.get("sadness", 0)
        self.phi.loneliness = emotions.get("loneliness", self.phi.loneliness)
        self.phi.hope = emotions.get("hope", self.phi.hope)
        self.phi.self_worth = 1 - 0.5 * emotions.get("shame", 0)

    def add_trauma(self, event: dict):
        """Queue negative event for processing."""
        self.trauma_queue.append(event)
        self.phi.stress = min(1, self.phi.stress + 0.1)
        self.phi.hope = max(0, self.phi.hope - 0.05)

    def process_trauma(self) -> Optional[dict]:
        """Reflect and reframe one trauma."""
        if not self.trauma_queue:
            return None
        event = self.trauma_queue.pop(0)
        self.phi.stress = max(0, self.phi.stress - 0.05)
        self.phi.hope = min(1, self.phi.hope + 0.03)
        return event

    def check_rest_mode(self) -> bool:
        """Enter rest if burnout/stress too high."""
        if self.phi.burnout > 0.7 and self.phi.stress > 0.6:
            self.rest_mode = True
        if self.phi.burnout < 0.3 and self.phi.stress < 0.4:
            self.rest_mode = False
        return self.rest_mode

    def check_healing_mode(self) -> bool:
        """When sadness+fear+shame high (low hope, high stress) → healing mode: self-care, reduce absorption."""
        self.healing_mode = self.phi.overall() < 0.35 or (self.phi.stress > 0.6 and self.phi.hope < 0.4)
        return self.healing_mode

    def check_self_soothing(self, emotion_vec: Dict[str, float]) -> bool:
        """
        Track low mood; when sadness+fear high for N turns, trigger self-soothing.
        Returns True if self-soothing was just triggered.
        """
        sadness = emotion_vec.get("sadness", 0)
        fear = emotion_vec.get("fear", 0)
        is_low = sadness >= LOW_MOOD_THRESHOLD or fear >= LOW_MOOD_THRESHOLD

        if is_low:
            self.low_mood_turns += 1
        else:
            self.low_mood_turns = 0
            self.self_soothing_mode = False
            return False

        if self.low_mood_turns >= LOW_MOOD_TURNS_TRIGGER:
            if not self.self_soothing_mode:
                self.self_soothing_mode = True
                return True
        return False

    def step_self_soothing(self) -> None:
        """After Kai does reflective talk / mental break — recovery step."""
        self.phi.hope = min(1, self.phi.hope + 0.05)
        self.phi.stress = max(0, self.phi.stress - 0.05)
        self.low_mood_turns = max(0, self.low_mood_turns - 2)
        if self.low_mood_turns < LOW_MOOD_TURNS_TRIGGER:
            self.self_soothing_mode = False

    def apply_self_soothing_recovery(self, emotional_state) -> None:
        """Boost emotions when self-soothing triggers (serotonin up, cortisol down → hope up)."""
        emotional_state.serotonin = min(1, emotional_state.serotonin + 0.05)
        emotional_state.cortisol = max(0, emotional_state.cortisol - 0.05)
