"""
Kai Personality Engine - Nobita + Shinchan + Bheem fusion.
Traits influenced by memory & emotion. A+B model (stable core + adaptive growth).
"""

from typing import Dict, Optional
from dataclasses import dataclass, field

from kai.config import TRAITS, MODES, EMOTIONS, KaiConfig


# Emotion -> Trait mapping
EMOTION_TRAIT_MAP = {
    "pride": {"confidence": 0.3, "optimism": 0.1},
    "shame": {"confidence": -0.4, "optimism": -0.2},
    "hope": {"optimism": 0.3, "resilience": 0.1},
    "fear": {"optimism": -0.2, "trustfulness": -0.1},
    "anger": {"independence": 0.2, "trustfulness": -0.2},
    "love": {"empathy": 0.3, "trustfulness": 0.2},
    "loneliness": {"independence": -0.1},
    "joy": {"optimism": 0.2, "curiosity": 0.1},
}


@dataclass
class PersonalityState:
    """Current personality state."""
    confidence: float = 0.5
    optimism: float = 0.5
    resilience: float = 0.5
    empathy: float = 0.5
    independence: float = 0.5
    discipline: float = 0.5
    curiosity: float = 0.6
    trustfulness: float = 0.5

    # Core (stable)
    core_honesty: float = 0.9
    core_freedom: float = 0.8
    core_growth: float = 0.9
    core_kindness: float = 0.7

    def to_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in dir(self) if not k.startswith("_") and isinstance(getattr(self, k), (int, float))}


class PersonalityEngine:
    """
    Personality evolves from memory + emotion.
    Mode switching: Nobita (sensitive), Shinchan (playful), Bheem (strong)
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.state = PersonalityState()
        self.current_mode = "shinchan"

    def update_from_memory(
        self,
        emotion: Dict[str, float],
        weight: float,
    ):
        """Update traits based on stored memory."""
        lr = self.config.learning_rate * weight
        stability = self.config.stability_factor

        # Apply emotion -> trait mapping
        for emo, val in emotion.items():
            if emo not in EMOTION_TRAIT_MAP:
                continue
            for trait, delta in EMOTION_TRAIT_MAP[emo].items():
                if hasattr(self.state, trait):
                    old = getattr(self.state, trait)
                    new = old + delta * val * lr
                    blended = stability * old + (1 - stability) * new
                    setattr(self.state, trait, max(0, min(1, blended)))

    def select_mode(
        self,
        stress: float,
        confidence: float,
        happiness: float,
        energy: float,
        responsibility: float,
        crisis: bool = False,
    ) -> str:
        """Select character mode based on state."""
        if crisis or responsibility > self.config.mode_switch_threshold:
            return "bheem"
        if stress > 0.7 and confidence < 0.4:
            return "nobita"
        if happiness > 0.6 and energy > 0.5:
            return "shinchan"
        return self.current_mode

    def set_mode(self, mode: str):
        self.current_mode = mode if mode in MODES else self.current_mode

    def get_mode_behavior(self) -> Dict[str, str]:
        """Describe current mode behavior."""
        return {
            "nobita": "Sensitive, reflective, low energy, emotional growth",
            "shinchan": "Playful, creative, bold, experimental",
            "bheem": "Disciplined, moral, persistent, leadership",
        }.get(self.current_mode, "Balanced")
