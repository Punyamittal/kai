"""
Kai Response Length Controller — Match user style so Kai doesn't over-explain.
Context → user style (casual / normal / deep) → max length → trim reply.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# Emoji/slang that suggests chill/casual
CHILL_INDICATORS = (
    "lol", "lmao", "haha", "hehe", "jk", "idk", "tbh", "imo", "ngl",
    "😅", "😂", "👍", "😊", "🤷", "👀", "😭", "🥲", ":)", ":(", "xd",
)


@dataclass
class LengthHint:
    """What length/style to use for this reply."""
    max_sentences: int
    style: str  # casual, normal, deep
    tone: str   # normal, playful_short
    instruction: str  # For LLM system prompt


def _word_count(text: str) -> int:
    return len(text.strip().split())


def _has_chill_indicators(text: str) -> bool:
    t = text.lower().strip()
    return any(c in t for c in CHILL_INDICATORS)


def _avg_user_word_count(recent_user_messages: List[str]) -> float:
    if not recent_user_messages:
        return 5.0
    counts = [_word_count(m) for m in recent_user_messages]
    return sum(counts) / len(counts)


def get_reply_length(
    user_message: str,
    emotions: Dict[str, float],
    recent_user_messages: Optional[List[str]] = None,
) -> LengthHint:
    """
    Detect user style and return max_sentences + tone.
    - casual (short / chill) → 1 sentence, maybe playful_short
    - normal → 2
    - deep → 3
    Emotion modifiers: loneliness → +1, fear → +1 (ramble), pride → -1 (shorter).
    """
    msg_lower = user_message.lower().strip()
    words = _word_count(user_message)
    recent = recent_user_messages or [user_message]
    avg_words = _avg_user_word_count(recent)
    chill = _has_chill_indicators(user_message)

    # User explicitly asked for short / simple / complained about long replies
    wants_short = any(
        x in msg_lower
        for x in (
            "short", "brief", "big text", "long text", "long message",
            "too long", "write big", "always write", "so long", "paragraph",
            "simple", "simpler", "any simpler", "can you be simpler", "be simpler", "keep it simple",
        )
    )

    # Style from current + recent pattern (or force casual if wants_short)
    tone = "normal"
    instruction = ""

    if wants_short or words <= 4 or avg_words <= 5 or chill:
        style = "casual"
        max_sent = 1
        if wants_short:
            tone = "playful_short"
            if "simple" in msg_lower or "simpler" in msg_lower:
                instruction = (
                    "User asked for SIMPLE. Respond in simple, direct language. No metaphors. ONE sentence only. "
                    "Never say 'I'll keep it simple' without actually giving a one-sentence reply — just be simple."
                )
            else:
                instruction = "User wants SHORT replies. Reply in ONE short sentence. Self-aware or light is fine, e.g. 'Bad habit. I talk too much sometimes.'"
    elif words >= 15 or avg_words >= 12:
        style = "deep"
        max_sent = 3
    else:
        style = "normal"
        max_sent = 2

    # Emotion modifiers
    loneliness = emotions.get("loneliness", 0)
    fear = emotions.get("fear", 0)
    pride = emotions.get("pride", 0)
    joy = emotions.get("joy", 0)

    if loneliness > 0.45:
        max_sent = min(4, max_sent + 1)
    if fear > 0.6:
        max_sent = min(4, max_sent + 1)
    if pride > 0.4:
        max_sent = max(1, max_sent - 1)

    # Playful short: casual + some joy → one short funny line
    if tone != "playful_short" and style == "casual" and joy > 0.3:
        tone = "playful_short"
        max_sent = 1

    # Instruction for LLM (if not already set by wants_short)
    if not instruction:
        if style == "casual":
            instruction = "Keep your reply to ONE short sentence. User is being casual — match their brevity. No paragraphs."
        elif style == "deep":
            instruction = "You may use 2-3 sentences. User is in a reflective mood."
        else:
            instruction = "Keep your reply to 1-2 short sentences. Be concise."

    if tone == "playful_short":
        instruction += " Slightly playful or self-aware is fine. Still one sentence."

    return LengthHint(
        max_sentences=max_sent,
        style=style,
        tone=tone,
        instruction=instruction,
    )


def trim_reply(reply: str, max_sentences: int) -> str:
    """
    Trim reply to at most max_sentences. Splits on . ! ?
    """
    if max_sentences >= 10 or not reply.strip():
        return reply.strip()

    # Split into sentences (keep delimiter)
    parts = re.split(r'(?<=[.!?])\s+', reply.strip())
    sentences = [s.strip() for s in parts if s.strip()]
    if len(sentences) <= max_sentences:
        return reply.strip()
    trimmed = " ".join(sentences[:max_sentences])
    # Ensure we don't cut mid-word; already sentence-bounded
    return trimmed.strip()


# Short funny fallbacks when tone is playful_short (optional override)
PLAYFUL_SHORT_FALLBACKS = [
    "Bad habit. I talk too much sometimes.",
    "I get carried away. Sorry.",
    "Yeah, I know — I'll keep it short.",
]
