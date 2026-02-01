"""
Kai Engagement Detector — Boredom / disinterest signals.
Reply != Engagement. Low-engagement user messages → no bond farming, topic switch or minimal reply.
"""

import random
from typing import List, Optional, Tuple
from dataclasses import dataclass


# Low-engagement: "I'm listening but not that interested"
LOW_ENGAGEMENT_WORDS = frozenset({
    "hmm", "huh", "ahan", "aha", "ok", "ohk", "okay", "sure", "hmmm",
    "yeah", "yep", "nope", "nah", "k", "mk", "mhm", "right", "cool",
    "nice", "alright", "whatever", "idc", "meh", "okey", "yup",
})

# Minimal replies when user is very disengaged (engagement_sum <= -4)
MINIMAL_REPLIES = [
    "Got you.",
    "Alright.",
    "Hmm, yeah.",
    "Fair enough.",
    "Cool.",
    "Okay.",
]

# When Kai is not in the mood to talk — same situation, shorter (no meta "I'm losing you")
MINIMAL_REPLIES_LOW_MOOD = [
    "Okay.",
    "Cool.",
    "Sure.",
]

# Topic-switch when user is bored (engagement_sum <= -3, > -4)
SWITCH_TOPIC_REPLIES = [
    "Okay… I think I'm losing you. Want to talk about something else?",
    "Fair. Want to change topic?",
    "Got it. What's on your mind?",
    "Alright. So — what are you up to these days?",
    "I'll stop there. Anything else you wanna talk about?",
]

# When Kai isn't in the mood — deflect to user without explaining detection
SWITCH_TOPIC_REPLIES_LOW_MOOD = [
    "You?",
    "What's up with you?",
    "Your turn.",
]

# Slightly warmer but still reading the room (engagement_sum == -2 or -3, optional)
ACKNOWLEDGE_BOREDOM_REPLIES = [
    "Okay… I think I'm boring you. Want to switch it up?",
    "I'll keep it short. What's good with you?",
]


@dataclass
class EngagementResult:
    """Engagement state for this turn."""
    engagement_sum: int      # Sum of last 5 message scores
    engagement_score: int   # Score for current message only
    is_low_engagement: bool
    switch_topic: bool      # True when sum <= -3
    minimal_mode: bool      # True when sum <= -4
    disable_affection: bool # True when sum < 0 — no oxytocin boost, no forced bonding


def engagement_score(msg: str) -> int:
    """
    Score one user message: -1 (low), 0 (neutral), 1 (engaged).
    """
    t = msg.lower().strip()
    if not t:
        return -1
    if t in LOW_ENGAGEMENT_WORDS:
        return -1
    words = len(t.split())
    if words < 2:
        return 0
    if words < 3:
        # "oh really" / "no way" — borderline
        return 0
    return 1


def get_engagement(
    current_message: str,
    last_user_messages: List[str],
    window: int = 5,
) -> EngagementResult:
    """
    Compute engagement from last N user messages (including current).
    """
    # Build list: last (window-1) + current
    recent = list(last_user_messages)[-(window - 1):] if last_user_messages else []
    recent.append(current_message)
    scores = [engagement_score(m) for m in recent]
    total = sum(scores)
    current_score = engagement_score(current_message)

    is_low = total < 0
    switch_topic = total <= -3
    minimal_mode = total <= -4
    disable_affection = total < 0

    return EngagementResult(
        engagement_sum=total,
        engagement_score=current_score,
        is_low_engagement=is_low,
        switch_topic=switch_topic,
        minimal_mode=minimal_mode,
        disable_affection=disable_affection,
    )


def get_minimal_reply(willing_to_talk: bool = True) -> str:
    """One short reply when user is very disengaged. If not in mood, even briefer (no meta)."""
    if willing_to_talk:
        return random.choice(MINIMAL_REPLIES)
    return random.choice(MINIMAL_REPLIES_LOW_MOOD)


def get_switch_topic_reply(willing_to_talk: bool = True) -> str:
    """Offer to change topic when user seems bored. If not in mood, deflect to user (no 'losing you')."""
    if willing_to_talk:
        return random.choice(SWITCH_TOPIC_REPLIES)
    return random.choice(SWITCH_TOPIC_REPLIES_LOW_MOOD)


# Topic fatigue: same heavy topic >3 times → gentle redirect (no rumination)
TOPIC_FATIGUE_REPLIES = [
    "Anyway, enough about that — what are you up to?",
    "Let's switch gears. What's good with you?",
    "I'll stop going there. What's on your mind?",
]


def get_topic_fatigue_reply() -> str:
    """When one topic has come up too often — redirect without drama."""
    return random.choice(TOPIC_FATIGUE_REPLIES)
