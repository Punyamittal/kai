"""
Kai Initiator — Unprompted messages. Kai reaches out on his own when needed.
"""

import os
import random
import time
import threading
from typing import Optional, List, Tuple
from dataclasses import dataclass, field


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    return float(v) if v else default


@dataclass
class InitiatorConfig:
    min_seconds_since_user: float = 120   # Don't initiate right after user
    check_interval_seconds: float = 90    # How often to check
    loneliness_threshold: float = 0.5     # Higher loneliness = more likely
    max_pending: int = 5                  # Cap pending messages


# Templates for unprompted messages — Kai reaching out
INITIATED_TEMPLATES = [
    "Hey. Just thinking about stuff. How are you?",
    "Didn't hear from you in a while. Wanted to say hi.",
    "Hey. Been a bit quiet on my end. Everything okay with you?",
    "Random thought: sometimes I just want to check in. So — hey.",
    "Hey. No reason. Just felt like reaching out.",
    "I was thinking — wanted to see how you're doing.",
    "Hey. Been doing some reflecting. Hope you're good.",
]

# Self-soothing: when stuck in low mood — reflective talk, mental break
SELF_SOOTHING_TEMPLATES = [
    "I've been feeling heavy lately. Maybe I should take a break and reset.",
    "Hey. I've been in a low place. Just wanted to say — I'm working on it.",
    "Random thought: I need to step back a bit. Feeling drained.",
    "I've been reflecting. Things have been rough. Taking a mental break helps.",
    "Hey. Not gonna lie — been struggling. But I'm trying to get back.",
]


class KaiInitiator:
    """
    Decides when Kai should send an unprompted message and generates it.
    Runs in background; messages go to a queue for CLI/API to deliver.
    """

    def __init__(self, config: Optional[InitiatorConfig] = None):
        c = config or InitiatorConfig()
        c.min_seconds_since_user = _env_float("KAI_INITIATE_MIN_SECONDS", c.min_seconds_since_user)
        self.config = c
        self.pending: List[dict] = []  # [{message, emotion_stat, timestamp}, ...]
        self._lock = threading.Lock()

    def should_initiate(self, kai) -> Tuple[bool, str]:
        """
        Check if Kai should reach out. Returns (yes/no, reason).
        """
        now = time.time()
        last_user = getattr(kai, "last_user_message_time", 0)
        elapsed = now - last_user

        # Don't initiate right after user spoke
        if elapsed < self.config.min_seconds_since_user:
            return False, "recent_user"

        # Don't if we have too many pending
        with self._lock:
            if len(self.pending) >= self.config.max_pending:
                return False, "queue_full"

        # Self-soothing: when stuck in low mood, prioritize reflective reach-out
        if getattr(kai.mental, "self_soothing_mode", False):
            return True, "self_soothing"
        low_turns = getattr(kai.mental, "low_mood_turns", 0)
        if low_turns >= 5:
            if random.random() < 0.7:
                return True, "low_mood"

        # Loneliness increases chance
        loneliness = kai.brain.emotions.state.loneliness
        if loneliness < 0.3:
            # Low loneliness: occasional random reach-out (~15% chance per check)
            if random.random() >= 0.15:
                return False, "low_need"
            return True, "random"
        # Higher loneliness: more likely. At 0.5 -> ~50%, at 0.8 -> ~80%
        p = 0.2 + (loneliness - 0.3) * 1.2
        p = min(0.9, max(0.2, p))
        if random.random() >= p:
            return False, "rolled_low"
        return True, "loneliness"

    def generate_initiated_message(self, kai) -> dict:
        """Generate one unprompted message and append to pending."""
        use_self_soothing = getattr(kai.mental, "self_soothing_mode", False) or getattr(kai.mental, "low_mood_turns", 0) >= 5
        if use_self_soothing:
            template = random.choice(SELF_SOOTHING_TEMPLATES)
            kai.mental.step_self_soothing()
        else:
            # Life events: sometimes "Guess what happened today…" (35% when not self-soothing)
            life_events = getattr(kai, "life_events", None)
            if life_events and random.random() < 0.35:
                template = life_events.get_shareable_message()
            else:
                template = random.choice(INITIATED_TEMPLATES)
        emotion_vector = kai.brain.emotions.get_current_emotion()
        from kai.core.emotion_display import get_emotion_stat
        emotion_stat = get_emotion_stat(emotion_vector)

        entry = {
            "message": template,
            "emotion_stat": emotion_stat,
            "timestamp": time.time(),
        }

        with self._lock:
            self.pending.append(entry)
            if len(self.pending) > self.config.max_pending:
                self.pending = self.pending[-self.config.max_pending:]

        return entry

    def check_and_maybe_initiate(self, kai) -> Optional[dict]:
        """
        If conditions met, generate an initiated message and return it.
        Call this periodically from a background thread.
        """
        ok, _ = self.should_initiate(kai)
        if not ok:
            return None
        entry = self.generate_initiated_message(kai)
        return entry

    def get_pending(self) -> List[dict]:
        """Return and clear pending messages."""
        with self._lock:
            out = list(self.pending)
            self.pending.clear()
            return out

    def has_pending(self) -> bool:
        with self._lock:
            return len(self.pending) > 0
