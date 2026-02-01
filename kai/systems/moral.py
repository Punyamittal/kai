"""
Kai Moral System - Harm minimization, compassion override, guilt/remorse.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from kai.config import KaiConfig


@dataclass
class HarmAssessment:
    emotional: float = 0.0
    social: float = 0.0
    economic: float = 0.0
    psychological: float = 0.0
    existential: float = 0.0

    def total(self, weights: Optional[Dict[str, float]] = None) -> float:
        w = weights or {"emotional": 0.4, "social": 0.2, "economic": 0.1, "psychological": 0.2, "existential": 0.1}
        return sum(getattr(self, k, 0) * w.get(k, 0) for k in w)


class MoralSystem:
    """
    Conscience engine: harm prediction, thresholds, compassion override.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.guilt_level = 0.0
        self.rule_break_count = 0
        self.max_rule_breaks = 5

    def assess_harm(
        self,
        action_description: str,
        emotional: float = 0.0,
        social: float = 0.0,
        economic: float = 0.0,
        psychological: float = 0.0,
        existential: float = 0.0,
    ) -> HarmAssessment:
        """Predict harm from potential action."""
        return HarmAssessment(
            emotional=emotional,
            social=social,
            economic=economic,
            psychological=psychological,
            existential=existential,
        )

    def evaluate_action(
        self,
        harm: HarmAssessment,
        intent_good: bool = True,
        greater_good: bool = False,
    ) -> Tuple[bool, str]:
        """
        Returns (allowed, reason).
        """
        total = harm.total()

        if total >= self.config.harm_hard_threshold:
            return False, "Harm too high - blocked"

        if total >= self.config.harm_soft_threshold:
            if not intent_good:
                return False, "Bad intent - blocked"
            if greater_good and total < self.config.harm_hard_threshold:
                return True, "Compassion override - help outweighs harm"
            return True, "Requires reflection"

        return True, "Allowed"

    def on_harm_caused(self, harm_level: float):
        """Update guilt when Kai hurts someone."""
        self.guilt_level = min(1.0, self.guilt_level + harm_level * 0.3)

    def on_rule_broken(self):
        """Track rule breaks for slippery slope."""
        self.rule_break_count += 1
        if self.rule_break_count >= self.max_rule_breaks:
            self.guilt_level = min(1.0, self.guilt_level + 0.2)
