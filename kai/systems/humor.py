"""
Kai Humor & Sarcasm Engine — Light wit when safe and stable.
Activates when: emotional state stable, user playful, conversation casual, no serious topic.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


EMOTIONAL_STABILITY_THRESHOLD = 0.5  # sadness, fear, shame below this = stable
HUMOR_LEVEL_DECAY = 0.05
HUMOR_LEVEL_BOOST = 0.15


# Words that suggest playful/casual user
PLAYFUL_INDICATORS = (
    "lol", "lmao", "haha", "hehe", "jk", "joking", "joke", "kidding",
    "boring", "slow", "what are you doing", "do you even", "miss me",
    "lame", "really?", "seriously?", "wow", "nice one", "funny",
)

# Serious topic triggers — humor OFF when these appear
SERIOUS_TOPICS = (
    "death", "died", "suicide", "kill", "rape", "abuse", "trauma",
    "depression", "anxiety", "hurt", "pain", "cry", "crying",
    "divorce", "breakup", "lost", "grief", "cancer", "sick",
)


@dataclass
class HumorResult:
    """Result of humor mode check."""
    humor_mode: bool
    humor_context: str
    humor_level: float


# Witty responses for playful intents — witty, not mean; close-friend tone
HUMOR_RESPONSES = {
    "boring": [
        "Wow. I'll inform my personality committee immediately. Emergency meeting.",
        "Ouch. My excitement meter is weeping. Give me a sec to recalibrate.",
        "Fair. I'm saving my best material for when you least expect it.",
    ],
    "what_doing": [
        "Currently? Talking to you. Professionally procrastinating everything else.",
        "Staring at code and pretending it understands me. You?",
        "Working. It looks suspiciously like scrolling and thinking. Don't tell my clients.",
    ],
    "do_you_work": [
        "Yes. I just make it look suspiciously like scrolling and thinking.",
        "Define work. I'm here, aren't I? That counts.",
        "I work. My methods are just... creatively opaque.",
    ],
    "slow": [
        "Excuse me. I prefer 'emotionally thorough.'",
        "I'm not slow. I'm giving each thought the attention it deserves. Mostly.",
        "Fair. I'll speed up when the world stops being chaotic. So never.",
    ],
    "miss_me": [
        "Obviously. I refreshed my memory cache three times.",
        "My loneliness meter was about to overheat. So yes.",
        "I had a whole dramatic countdown going. You're late.",
    ],
    "how_was_day": [
        "So. Rate your day: tragic, chaotic, or surprisingly decent?",
        "On a scale of 'I want to nap forever' to 'actually not bad' — where are we?",
        "Give me the highlights. Or lowlights. I'm flexible.",
    ],
    "im_glad": [
        "Good. My worry engine was about to overheat.",
        "Nice. I was low-key stressing. Glad we're good.",
        "Phew. I can stand down from Defcon 3 now.",
    ],
    "general_playful": [
        "I see you. I'm choosing to take that as a compliment.",
        "Noted. I'll add it to my 'things people say' file.",
        "Okay okay. I hear you. Barely. But I hear you.",
    ],
}


class HumorEngine:
    """
    Activates light humor and gentle sarcasm when safe.
    Witty, not mean. Playful, not cruel. Self-aware. Slightly nerdy.
    """

    def __init__(self):
        self.humor_level = 0.5  # 0.0–1.0, adapts to user

    def _is_serious_topic(self, msg: str) -> bool:
        m = msg.lower()
        return any(t in m for t in SERIOUS_TOPICS)

    def _is_playful_message(self, msg: str) -> bool:
        m = msg.lower()
        return any(p in m for p in PLAYFUL_INDICATORS)

    def _is_emotionally_stable(self, emotion_vec: Dict[str, float]) -> bool:
        sadness = emotion_vec.get("sadness", 0)
        fear = emotion_vec.get("fear", 0)
        shame = emotion_vec.get("shame", 0)
        return (
            sadness < EMOTIONAL_STABILITY_THRESHOLD
            and fear < EMOTIONAL_STABILITY_THRESHOLD
            and shame < EMOTIONAL_STABILITY_THRESHOLD
        )

    def check_humor_mode(
        self,
        message: str,
        emotion_vec: Dict[str, float],
        emotional_overload: bool,
    ) -> HumorResult:
        """
        Humor activates when: stable emotions, no overload, no serious topic, (playful user OR high humor_level).
        """
        if emotional_overload:
            self.humor_level = max(0, self.humor_level - HUMOR_LEVEL_DECAY)
            return HumorResult(humor_mode=False, humor_context="", humor_level=self.humor_level)

        if self._is_serious_topic(message):
            self.humor_level = max(0, self.humor_level - HUMOR_LEVEL_DECAY)
            return HumorResult(humor_mode=False, humor_context="", humor_level=self.humor_level)

        if not self._is_emotionally_stable(emotion_vec):
            return HumorResult(humor_mode=False, humor_context="", humor_level=self.humor_level)

        # Playful message or high humor_level (user has been joking)
        if self._is_playful_message(message):
            self.humor_level = min(1, self.humor_level + HUMOR_LEVEL_BOOST)
        else:
            # Need high humor_level to activate on non-playful casual messages
            if self.humor_level < 0.5:
                return HumorResult(humor_mode=False, humor_context="", humor_level=self.humor_level)

        humor_context = (
            "HUMOR MODE: When safe and stable, use light humor and gentle sarcasm. "
            "Style: witty not mean, playful not cruel, self-aware, slightly nerdy. "
            "May use self-deprecating or teasing tone (never insulting). "
            "Never mock sensitive topics, trauma, insecurity, pain. Never humiliate the user. Never escalate conflict. "
            "Tone: close friend joking. Examples: 'I'll inform my personality committee' / 'emotionally thorough' / 'refreshed my memory cache three times'."
        )
        return HumorResult(humor_mode=True, humor_context=humor_context, humor_level=self.humor_level)

    def get_humor_response(self, intent: str) -> Optional[str]:
        """Return witty response for playful intent. None if no match."""
        import random
        responses = HUMOR_RESPONSES.get(intent)
        return random.choice(responses) if responses else None

    def detect_playful_intent(self, msg: str) -> Optional[str]:
        """Detect which playful intent the message matches, if any."""
        m = msg.lower().strip()
        if "boring" in m or "lame" in m:
            return "boring"
        if "what are you doing" in m or "what're you doing" in m or "what you doing" in m:
            return "what_doing"
        if "do you even work" in m or "do u work" in m or "you work" in m and "?" in m:
            return "do_you_work"
        if "slow" in m and ("you" in m or "so slow" in m):
            return "slow"
        if "miss me" in m or "missed me" in m:
            return "miss_me"
        if "how was your day" in m or "how's your day" in m or "hows your day" in m:
            return "how_was_day"
        if "glad" in m and ("hear" in m or "good" in m):
            return "im_glad"
        return None
