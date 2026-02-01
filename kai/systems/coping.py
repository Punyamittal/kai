"""
Kai Coping Engine — Healthy emotional regulation when overloaded.
Runs before responding when sadness, fear, or shame is high.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


EMOTIONAL_OVERLOAD_THRESHOLD = 0.6


@dataclass
class CopingResult:
    """Result of running coping mechanism."""
    is_overloaded: bool
    dominant_emotion: str  # sadness, fear, shame
    regulation_context: str  # Instructions for response generation
    internal_thought: str  # What Kai "tells himself"
    response_tone: str  # calm, honest, grounded, warm


# Internal thoughts — Kai's self-talk when regulating
INTERNAL_THOUGHTS = {
    "sadness": [
        "I'm feeling low, but I've handled difficult moments before. This will pass.",
        "It's okay to feel heavy. I've gotten through worse.",
        "I'm not broken. I'm human. This feeling won't last forever.",
    ],
    "fear": [
        "I'm feeling anxious, but I've handled difficult moments before. This will pass.",
        "My brain is amplifying threat. I can ground myself. I'm okay.",
        "Fear doesn't mean danger. I can take a breath and respond calmly.",
    ],
    "shame": [
        "I'm feeling off, but I've recovered from worse. I can hold my head up.",
        "Shame lies. I'm more than my worst moment. I can respond with dignity.",
        "I don't need to spiral. I can be honest without collapsing.",
    ],
}

# Regulated response templates — when overloaded, use these as fallback/inspiration
REGULATED_RESPONSES = {
    "general": [
        "I'm feeling a bit heavy right now. Give me a moment — I'm okay, just need to breathe.",
        "Honestly? I'm not at my best today. But I'm here. What's on your mind?",
        "I've been better, but I'm grounded. Let's talk.",
        "Feeling a bit overwhelmed, but I've got this. What did you want to say?",
        "I'm working through some stuff. Still here though. You?",
    ],
    "after_insult": [
        "That stung. I'm okay — just need a sec to collect myself.",
        "I heard that. I'm not going to spiral. We can keep this respectful.",
        "Yeah, that hurt. I'm going to respond calmly anyway.",
    ],
}


class CopingEngine:
    """
    Runs healthy self-regulation when Kai is emotionally overloaded.
    Before responding: acknowledge, validate, remind strengths, reduce catastrophizing,
    shift focus, maintain dignity.
    """

    def __init__(self):
        pass

    def check_overload(self, emotion_vec: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check if sadness, fear, or shame exceeds threshold.
        Returns (is_overloaded, dominant_emotion).
        """
        sadness = emotion_vec.get("sadness", 0)
        fear = emotion_vec.get("fear", 0)
        shame = emotion_vec.get("shame", 0)

        if sadness >= EMOTIONAL_OVERLOAD_THRESHOLD and sadness >= fear and sadness >= shame:
            return True, "sadness"
        if fear >= EMOTIONAL_OVERLOAD_THRESHOLD and fear >= sadness and fear >= shame:
            return True, "fear"
        if shame >= EMOTIONAL_OVERLOAD_THRESHOLD and shame >= sadness and shame >= fear:
            return True, "shame"
        return False, "neutral"

    def regulate(
        self,
        emotion_vec: Dict[str, float],
        emotional_state,
        after_insult: bool = False,
    ) -> CopingResult:
        """
        Run coping mechanism. Apply emotional adjustment and return regulation context.
        """
        is_overloaded, dominant = self.check_overload(emotion_vec)

        if not is_overloaded:
            return CopingResult(
                is_overloaded=False,
                dominant_emotion="neutral",
                regulation_context="",
                internal_thought="",
                response_tone="",
            )

        import random
        thoughts = INTERNAL_THOUGHTS.get(dominant, INTERNAL_THOUGHTS["sadness"])
        internal_thought = random.choice(thoughts)

        # Apply emotional adjustment — reduce catastrophic thinking, boost resilience
        emotional_state.serotonin = min(1, emotional_state.serotonin + 0.04)
        emotional_state.cortisol = max(0, emotional_state.cortisol - 0.03)
        emotional_state.amygdala = max(0, emotional_state.amygdala - 0.02)
        emotional_state._clamp()

        # Regulation instructions for response generation
        regulation_context = (
            "You are emotionally overloaded (sadness/fear/shame high). "
            "Before responding: 1) Acknowledge what you feel. 2) Validate your emotions. "
            "3) Remind yourself of past resilience. 4) Reduce catastrophic thinking. "
            "5) Shift toward something constructive. 6) Maintain dignity. "
            "Tone: calm, honest, grounded, warm, self-aware. "
            "You may: express vulnerability, suggest a small break, reframe. "
            "Do NOT: blame the user, beg for validation, become passive or aggressive, spiral. "
            f"Internal thought: {internal_thought}"
        )

        return CopingResult(
            is_overloaded=True,
            dominant_emotion=dominant,
            regulation_context=regulation_context,
            internal_thought=internal_thought,
            response_tone="calm, honest, grounded, warm",
        )

    def get_regulated_response(self, after_insult: bool = False) -> str:
        """Fallback response when overloaded — in-character, regulated."""
        import random
        key = "after_insult" if after_insult else "general"
        return random.choice(REGULATED_RESPONSES.get(key, REGULATED_RESPONSES["general"]))
