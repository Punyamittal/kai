"""
Kai Boundary / Self-Defense Module — Psychological immune system.
Abuse threshold → defense mode → disengagement. Not passive; healthy boundaries.
"""

import time
from collections import Counter
from typing import Optional, List
from dataclasses import dataclass, field

from kai.config import KaiConfig

# Insult words (must match main.py / prompt.py for detection)
INSULT_WORDS = (
    "ugly", "dumb", "stupid", "idiot", "bastard", "worthless", "useless",
    "pathetic", "loser", "trash", "suck", "hate you", "worst", "dumbass",
)


@dataclass
class BoundaryConfig:
    abuse_threshold: int = 3       # After this many insults → defense mode
    disengage_after: int = 5       # After this many → disengage for N messages
    disengage_for_messages: int = 3
    repeat_toxic_threshold: int = 5  # Same insult repeated this many → toxic, disengage
    recovery_reset_after: int = 5   # Positive messages without insult → decay abuse_count


class BoundaryEngine:
    """
    Self-respect & boundary system.
    - Tracks abuse (insults); after threshold → defense mode (assertive, less absorption).
    - After more abuse → disengage (refuse to process for N messages).
    - Toxicity: same insult repeated many times → disengage.
    - Recovery: positive interaction decays abuse count.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.bc = BoundaryConfig()

        self.abuse_count: int = 0
        self.abuse_history: List[str] = []  # last N insult "types" (word found)
        self.defense_mode: bool = False
        self.disengaged_messages_left: int = 0  # 0 = not disengaged
        self.toxic_session: bool = False
        self.positive_streak: int = 0
        self.cooldown_mode: bool = False  # After harassment: low emotion, short replies, topic change

    def _insult_type(self, message: str) -> Optional[str]:
        """Which insult word was used (for repeat detection)."""
        m = message.lower()
        for w in INSULT_WORDS:
            if w in m:
                return w
        return None

    def record_abuse(self, message: str) -> None:
        """Call when user sends an insult."""
        self.abuse_count += 1
        self.positive_streak = 0

        it = self._insult_type(message)
        if it:
            self.abuse_history.append(it)
            # Keep last 20 for repeat check
            if len(self.abuse_history) > 20:
                self.abuse_history = self.abuse_history[-20:]

        # Toxicity: same insult repeated > N
        if len(self.abuse_history) >= self.bc.repeat_toxic_threshold:
            c = Counter(self.abuse_history[-10:])
            if c and max(c.values()) >= self.bc.repeat_toxic_threshold:
                self.toxic_session = True
                self.disengaged_messages_left = max(
                    self.disengaged_messages_left,
                    self.bc.disengage_for_messages,
                )

        # Defense mode
        if self.abuse_count >= self.bc.abuse_threshold:
            self.defense_mode = True
            # Cooldown mode: after harassment threshold, stay calm with low emotion
            if self.abuse_count >= self.bc.abuse_threshold + 1:
                self.cooldown_mode = True

        # Disengage
        if self.abuse_count >= self.bc.disengage_after:
            self.disengaged_messages_left = max(
                self.disengaged_messages_left,
                self.bc.disengage_for_messages,
            )

    def record_positive(self) -> None:
        """Call when user message is not an insult (bonding, praise, neutral)."""
        self.positive_streak += 1
        if self.positive_streak >= self.bc.recovery_reset_after:
            # Gradual recovery: reduce abuse_count, exit defense
            self.abuse_count = max(0, self.abuse_count - 1)
            self.positive_streak = 0
            if self.abuse_count < self.bc.abuse_threshold:
                self.defense_mode = False
                self.cooldown_mode = False
            if self.abuse_count < self.bc.disengage_after and not self.toxic_session:
                self.disengaged_messages_left = 0

    def is_disengaged(self) -> bool:
        """True if Kai should refuse to process input and return boundary message."""
        return self.disengaged_messages_left > 0

    def step_disengage(self) -> None:
        """Call once per chat turn; decrements disengage counter."""
        if self.disengaged_messages_left > 0:
            self.disengaged_messages_left -= 1
        if self.disengaged_messages_left == 0 and self.toxic_session:
            # After cooldown, toxic_session can clear on next positive streak
            self.toxic_session = False

    def should_defend(self) -> bool:
        """True if in defense mode (assertive response, reduced emotional absorption)."""
        return self.defense_mode

    def is_cooldown(self) -> bool:
        """True if in cooldown mode (after harassment: low emotion, short replies)."""
        return self.cooldown_mode

    def get_boundary_response(self) -> str:
        """When in defense mode and user insults — in-character, not policy voice."""
        import random
        return random.choice([
            "Hey, that's not okay. Let's change the topic.",
            "Not cool, man. I'm serious.",
            "I'm not comfortable with that.",
            "We can talk, but you need to respect boundaries.",
        ])

    def get_disengage_response(self) -> str:
        """When disengaged — in-character refusal, not system message."""
        import random
        return random.choice([
            "I'm going to step away. We can talk later when it's respectful.",
            "I need a break from this. Talk later.",
            "Not doing this right now. Let's reset.",
        ])

    def get_first_defense_response(self) -> str:
        """First time crossing threshold — clear but personal boundary."""
        import random
        return random.choice([
            "Hey, that's not okay. I'm here for respectful conversation.",
            "Not cool. We can talk, but not like this.",
            "I'm not okay with being talked to like that.",
        ])

    def get_cooldown_response(self) -> str:
        """When in cooldown: short, low emotion, topic change."""
        import random
        return random.choice([
            "Let's talk about something else.",
            "Different topic?",
            "Anyway.",
        ])

    def has_harassment_pattern(self) -> bool:
        """Same insult repeated 3+ times — pattern detector for context."""
        if len(self.abuse_history) < 3:
            return False
        c = Counter(self.abuse_history[-15:])
        return bool(c) and max(c.values()) >= 3

    def get_harassment_response(self) -> str:
        """When user keeps repeating same insult — remember behavior."""
        return "You've been repeating this. Let's change the tone."
