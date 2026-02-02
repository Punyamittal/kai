"""
Kai Emotional Engine - Hormonal simulation + brain structures.
Amygdala, Hippocampus, Adrenaline, Dopamine, etc.
"""

import math
from typing import Dict, Optional
from dataclasses import dataclass, field

from kai.config import HORMONES, KaiConfig


@dataclass
class EmotionalState:
    """Current emotional/hormonal state."""
    # Hormones 0.0-1.0
    dopamine: float = 0.5
    cortisol: float = 0.2
    oxytocin: float = 0.5
    serotonin: float = 0.5
    adrenaline: float = 0.1
    melatonin: float = 0.3
    testosterone: float = 0.5
    estrogen: float = 0.5
    lh: float = 0.5
    loneliness: float = 0.3
    curiosity: float = 0.6

    # Brain structures
    amygdala: float = 0.2   # fear, threat
    hippocampus: float = 0.5  # memory load

    # Core emotions
    love_attachment: float = 0.0
    love_trust: float = 0.5
    love_intimacy: float = 0.0
    love_care: float = 0.5
    anger_irritation: float = 0.0
    anger_rage: float = 0.0
    anger_resentment: float = 0.0
    anger_injustice: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "dopamine": self.dopamine,
            "cortisol": self.cortisol,
            "oxytocin": self.oxytocin,
            "serotonin": self.serotonin,
            "adrenaline": self.adrenaline,
            "melatonin": self.melatonin,
            "testosterone": self.testosterone,
            "estrogen": self.estrogen,
            "lh": self.lh,
            "loneliness": self.loneliness,
            "curiosity": self.curiosity,
            "amygdala": self.amygdala,
            "hippocampus": self.hippocampus,
            "love_attachment": self.love_attachment,
            "love_trust": self.love_trust,
            "anger_irritation": self.anger_irritation,
            "anger_rage": self.anger_rage,
        }

    def to_emotion_vector(self) -> Dict[str, float]:
        """For memory tagging. All values clamped to [0, 1] — prevents overflow."""
        raw = {
            "joy": self.dopamine * (1 - self.cortisol),
            "sadness": self.loneliness * 0.5 + self.cortisol * 0.5,
            "anger": (self.anger_irritation + self.anger_rage) / 2,
            "fear": self.amygdala,
            "love": (self.love_attachment + self.oxytocin) / 2,
            "shame": self.cortisol * self.amygdala,
            "pride": self.dopamine * self.testosterone,
            "hope": self.serotonin * (1 - self.cortisol),
            "loneliness": self.loneliness,
        }
        return {k: max(0.0, min(1.0, float(v))) for k, v in raw.items()}

    def decay(self, rate: float = 0.02):
        """Natural decay toward baseline."""
        baseline = 0.5
        for attr in ["dopamine", "cortisol", "oxytocin", "serotonin", "adrenaline",
                     "testosterone", "estrogen", "amygdala"]:
            val = getattr(self, attr)
            setattr(self, attr, val + (baseline - val) * rate)
        self.loneliness = min(1, self.loneliness + 0.01)
        # Anger decays toward 0 so it doesn't stick forever
        for attr in ["anger_irritation", "anger_rage", "anger_resentment", "anger_injustice"]:
            val = getattr(self, attr)
            setattr(self, attr, max(0.0, val - rate * 0.5))
        self._clamp()

    def _clamp(self):
        """Keep all emotion/hormone values in [0, 1]. Prevents overflow."""
        for attr in ["dopamine", "cortisol", "oxytocin", "serotonin", "adrenaline",
                     "melatonin", "testosterone", "estrogen", "lh", "loneliness", "curiosity",
                     "amygdala", "hippocampus",
                     "love_attachment", "love_trust", "love_intimacy", "love_care",
                     "anger_irritation", "anger_rage", "anger_resentment", "anger_injustice"]:
            try:
                val = getattr(self, attr)
                setattr(self, attr, max(0.0, min(1.0, float(val))))
            except (TypeError, AttributeError):
                pass
        # Cap attachment growth — real humans don't bond that fast; prevents clingy Kai
        self.oxytocin = min(self.oxytocin, 0.8)
        self.love_attachment = min(self.love_attachment, 0.4)

    def per_turn_attachment_decay(self):
        """Per-turn oxytocin decay so attachment doesn't inflate from normal chat."""
        self.oxytocin *= 0.995
        self._clamp()

    def regulate_emotions(self):
        """
        Emotional regulator: per-turn stabilization prevents emotional collapse.
        Humans self-regulate — Kai should too.
        - All emotions decay gently toward baseline (0.95 multiplier)
        - Sadness > 0.6 → gentle recovery (hope up, sadness down)
        - Anger > 0.4 → cooldown
        - Emotion floor: minimum dopamine/serotonin/testosterone (no free-fall into despair)
        - Emotion ceiling: max cortisol/amygdala/loneliness (no permanent despair/fear)
        """
        from kai.config import EMOTION_FLOOR, EMOTION_CEILING
        
        # Gentle decay on all main hormones (prevents runaway)
        for attr in ["dopamine", "cortisol", "oxytocin", "serotonin", "adrenaline", 
                     "testosterone", "amygdala", "loneliness"]:
            val = getattr(self, attr)
            setattr(self, attr, val * 0.95)
        
        # Anger cooldown (more aggressive decay so anger doesn't stick)
        for attr in ["anger_irritation", "anger_rage", "anger_resentment", "anger_injustice"]:
            val = getattr(self, attr)
            if val > 0.4:
                setattr(self, attr, val - 0.05)
        
        # Sadness > 0.6: recovery nudge (hope up, sadness down)
        if self.loneliness > 0.6 or self.cortisol > 0.6:
            sadness = self.loneliness * 0.5 + self.cortisol * 0.5
            if sadness > 0.6:
                self.loneliness = max(0.2, self.loneliness - 0.05)
                self.cortisol = max(0.1, self.cortisol - 0.05)
                self.serotonin = min(1.0, self.serotonin + 0.03)
        
        # Emotion floor: enforce minimum positive hormones (prevents emotional free-fall)
        for attr, floor in EMOTION_FLOOR.items():
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val < floor:
                    setattr(self, attr, floor)
        
        # Emotion ceiling: cap negative hormones (prevents permanent despair/fear)
        for attr, ceiling in EMOTION_CEILING.items():
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val > ceiling:
                    setattr(self, attr, ceiling)
        
        self._clamp()


class EmotionalEngine:
    """
    Simulates hormonal and emotional responses to events.
    Events -> Hormone updates -> Behavior influence
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.state = EmotionalState()

    def process_event(
        self,
        event_type: str,
        intensity: float = 0.5,
        **kwargs
    ) -> EmotionalState:
        """Process life event and update hormones."""
        intensity = max(0, min(1, intensity))

        # Event handlers
        handlers = {
            "success": self._on_success,
            "rejection": self._on_rejection,
            "praise": self._on_praise,
            "criticism": self._on_criticism,
            "bonding": self._on_bonding,
            "loss": self._on_loss,
            "betrayal": self._on_betrayal,
            "deadline": self._on_deadline,
            "lonely": self._on_lonely,
            "rest": self._on_rest,
            "creative": self._on_creative,
            "injustice": self._on_injustice,
            "insult": self._on_insult,
            "apology": self._on_apology,
            "boundary_push": self._on_boundary_push,
            "info": self._on_info,
            "personal_sharing": self._on_personal_sharing,
        }

        handler = handlers.get(event_type, self._on_neutral)
        handler(intensity, **kwargs)

        self.state._clamp()
        return self.state

    def _on_success(self, i: float, **kwargs):
        self.state.dopamine += 0.3 * i
        self.state.cortisol -= 0.2 * i
        self.state.testosterone += 0.1 * i
        self.state.serotonin += 0.1 * i

    def _on_rejection(self, i: float, **kwargs):
        self.state.dopamine -= 0.3 * i
        self.state.cortisol += 0.4 * i
        self.state.amygdala += 0.3 * i
        self.state.loneliness += 0.2 * i
        self.state.testosterone -= 0.2 * i

    def _on_praise(self, i: float, **kwargs):
        self.state.dopamine += 0.25 * i
        self.state.oxytocin += 0.1 * i
        self.state.love_trust += 0.05 * i

    def _on_criticism(self, i: float, **kwargs):
        self.state.cortisol += 0.3 * i
        self.state.amygdala += 0.2 * i
        self.state.love_trust -= 0.1 * i

    def _on_bonding(self, i: float, **kwargs):
        self.state.oxytocin += 0.3 * i
        self.state.love_attachment += 0.2 * i
        self.state.loneliness -= 0.3 * i
        self.state.serotonin += 0.1 * i

    def _on_loss(self, i: float, **kwargs):
        self.state.cortisol += 0.4 * i
        self.state.oxytocin -= 0.2 * i
        self.state.loneliness += 0.4 * i
        self.state.love_attachment -= 0.2 * i

    def _on_betrayal(self, i: float, **kwargs):
        self.state.anger_rage += 0.4 * i
        self.state.anger_injustice += 0.5 * i
        self.state.love_trust -= 0.5 * i
        self.state.amygdala += 0.3 * i

    def _on_deadline(self, i: float, **kwargs):
        self.state.adrenaline += 0.4 * i
        self.state.cortisol += 0.3 * i

    def _on_lonely(self, i: float, **kwargs):
        self.state.loneliness += 0.3 * i
        self.state.serotonin -= 0.2 * i

    def _on_rest(self, i: float, **kwargs):
        self.state.melatonin += 0.2 * i
        self.state.cortisol -= 0.2 * i
        self.state.adrenaline -= 0.3 * i

    def _on_creative(self, i: float, **kwargs):
        self.state.dopamine += 0.15 * i
        self.state.curiosity += 0.2 * i

    def _on_injustice(self, i: float, **kwargs):
        self.state.anger_injustice += 0.5 * i
        self.state.anger_resentment += 0.3 * i

    def _on_insult(self, i: float, **kwargs):
        """Hurt + boundary: anger and pride dip, so assertiveness layer can respond (not passive)."""
        self.state.cortisol += 0.08 * i   # shame/stress
        self.state.amygdala += 0.05 * i   # slight threat
        self.state.testosterone -= 0.02 * i  # pride dip
        self.state.anger_irritation += 0.05 * i
        self.state.anger_resentment += 0.03 * i

    def _on_personal_sharing(self, i: float, **kwargs):
        """User asked personal Q and Kai shared — bonding, feels good (dopamine + oxytocin)."""
        self.state.dopamine += 0.02 * i
        self.state.oxytocin += 0.02 * i

    def _on_apology(self, i: float, **kwargs):
        """Post-conflict: still stressed, but bonding and repair — cortisol down a bit, oxytocin up."""
        self.state.cortisol -= 0.1 * i    # relief
        self.state.oxytocin += 0.15 * i   # reconnection
        self.state.love_trust += 0.05 * i
        self.state.anger_irritation = max(0, self.state.anger_irritation - 0.1 * i)

    def _on_boundary_push(self, i: float, **kwargs):
        """Intrusive or pushing question after Kai set a boundary — irritation, not rage."""
        self.state.anger_irritation += 0.12 * i
        self.state.anger_resentment += 0.05 * i
        self.state.cortisol += 0.05 * i   # stress from boundary violation

    def _on_info(self, i: float, **kwargs):
        """Factual / learning exchange — feels good, not stressful. No fake anxiety."""
        self.state.dopamine += 0.02 * i
        self.state.cortisol -= 0.01 * i
        self.state.amygdala = max(0, self.state.amygdala - 0.01 * i)

    def _on_neutral(self, i: float, **kwargs):
        self.state.decay(0.01)

    def get_current_emotion(self) -> Dict[str, float]:
        return self.state.to_emotion_vector()

    def tick(self):
        """Daily decay - hormones drift toward baseline."""
        self.state.decay(self.config.memory_decay_rate)
