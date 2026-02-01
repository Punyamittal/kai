"""
Prompt-based responder - works without heavy LLM.
Uses intent detection + templates. Memory is CONTEXT, not content to echo.
"""

import random
from typing import Dict, Any, Optional

from kai.config import KAI_IDENTITY


# Kai's voice templates by mode (used when no specific intent matches)
MODE_RESPONSES = {
    "nobita": [
        "I've been thinking about that a lot lately...",
        "That's interesting. I feel like I'm still learning how to respond properly.",
        "I'm not sure I have a perfect answer, but I'm trying.",
    ],
    "shinchan": [
        "You know what? I've got an idea!",
        "Hmm, that's a good one. Let me think.",
        "Okay okay, I hear you!",
    ],
    "bheem": [
        "I'll think on that.",
        "Got it. I'm here.",
        "I hear you. Let's keep going.",
    ],
}

GREETINGS = [
    "Hey! Good to see you.",
    "Hi there. How's it going?",
    "Hey! I've been thinking about some stuff.",
]

GOODBYES = [
    "Take care. Talk soon?",
    "Alright, I'll catch you later.",
    "Thanks for stopping by.",
]

# User said "hmm" / "??" / "what" etc. → confused / continue / explain (not teasing)
CONFUSED_SIGNALS = frozenset({"hmm", "hmmm", "hmmmm", "??", "?", "what", "wdym", "huh"})


def _is_greeting(m: str) -> bool:
    """Check for greeting - use whole words to avoid 'yo' matching 'you'."""
    words = set(m.split())
    return bool(words & {"hi", "hey", "hello", "sup", "yo"})

def _detect_intent(msg: str) -> str:
    """Detect user intent for contextual response. Returns intent label."""
    m = msg.lower().strip()
    if m in CONFUSED_SIGNALS:
        return "confused"
    if any(w in m for w in ["bye", "goodbye", "see you", "later", "quit"]):
        return "farewell"
    if "how are you" in m or "how're you" in m or "hows your day" in m or "how is your day" in m:
        return "how_are_you"
    if "everything okay" in m or "you okay" in m or "are you okay" in m or "you alright" in m or "you good" in m:
        return "everything_okay"
    if _is_greeting(m):
        return "greeting"
    if "why are you" in m and ("repeat" in m or "echo" in m or "say" in m):
        return "meta_repeating"
    if "joke" in m or "kidding" in m or "just kidding" in m or "that was a joke" in m:
        return "joke_clarification"
    if "what do you like" in m or "what do u like" in m or "hobbies" in m or "enjoy" in m:
        return "about_kai_interests"
    # Partner / loyalty / girlfriend — Kai has Mira
    if any(w in m for w in ["loyal", "girlfriend", "girl", "partner", "girlfriend", "wife", "girl friend", "your girl"]):
        return "about_partner"
    if "wife" in m or "died" in m or "death" in m or "sad" in m:
        return "heavy_topic"
    # Remember when / past conflict — context: user asks about past insults
    if any(w in m for w in ["remember when", "remember that", "yesterday", "last time"]) and any(w in m for w in ["insult", "hurt", "abuse", "said that", "called me", "were mean"]):
        return "remember_conflict"
    # Apology — after abuse: appreciative but honest (not "no need to apologize")
    if any(w in m for w in ["sorry", "apologize", "apology", "my bad", "didn't mean", "forgive me", "regret", "that was wrong of me"]):
        return "apology"
    # Teasing — insult word + lol/jk/haha → playful comeback, not defensive
    _insult = ("ugly", "dumb", "stupid", "idiot", "bastard", "worthless", "useless",
               "pathetic", "loser", "trash", "suck", "hate you", "worst", "dumbass")
    _tease_markers = ("lol", "lmao", "haha", "hehe", "jk", "joke", "kidding", "😅", "😂")
    if any(w in m for w in _insult) and any(t in m for t in _tease_markers):
        return "teasing"
    # Insult — assertiveness layer: defensive / playful / serious by trust + repeat count
    if any(w in m for w in _insult):
        return "insult"
    # User wants short replies / complains about long messages
    if any(x in m for x in ("short", "brief", "big text", "long text", "too long", "write big", "always write", "so long", "paragraph")):
        return "user_wants_short"
    # ——— Identity & location FIRST (before generic "what" → question) ———
    if any(x in m for x in ("whats your name", "what's your name", "what is your name", "who are you", "your name", "may i know your name")):
        return "ask_name"
    if any(x in m for x in ("where are you", "where do you live", "where you at", "where you live", "your location", "where r u")):
        return "location"
    # Mira / Ravi / relationship / friend (before generic question)
    if "mira" in m and ("how" in m or "doing" in m or "is she" in m):
        return "about_partner"
    if "ravi" in m:
        return "about_friend_ravi"
    if any(x in m for x in ("wanna talk", "want to talk", "can we talk", "lets talk", "let's talk")):
        return "social_invitation"
    if any(x in m for x in ("what are you doing", "what're you doing", "what are you up to", "what you doing", "whats going on", "what's going on")):
        return "what_are_you_doing"
    if any(x in m for x in ("what are you working on", "what you working on", "working on what")):
        return "what_are_you_working_on"
    if any(x in m for x in ("whats that", "what's that", "what is that", "wdym")):
        return "whats_that"
    if any(x in m for x in ("asked about", "you didnt answer", "you didn't answer", "answer properly", "see the intent")):
        return "repair"
    if "?" in m or "what " in m or "why " in m or "how " in m or "when " in m:
        return "question"
    return "general"


# Intents that must use our in-character response, never the raw LLM (avoids mode lock / wrong routing)
PROTECTED_INTENTS = frozenset({
    "greeting", "farewell", "how_are_you", "everything_okay", "meta_repeating",
    "joke_clarification", "about_kai_interests", "about_partner", "about_friend_ravi",
    "heavy_topic", "insult", "teasing", "apology", "remember_conflict", "user_wants_short", "confused",
    "ask_name", "location", "social_invitation",
    "what_are_you_doing", "what_are_you_working_on", "whats_that", "repair",
    "question", "general",
})

# When Ollama is enabled, only these intents stay rule-based; the rest go to the LLM (secondary brain).
INTENTS_ALWAYS_RULE = frozenset({
    "ask_name", "location", "farewell", "insult", "teasing", "apology", "repair",
    "meta_repeating", "user_wants_short", "remember_conflict", "confused",
})


def get_fixed_response_if_any(
    user_message: str, state: dict, recent_memories: list, allow_llm_for_open_ended: bool = False
) -> Optional[str]:
    """If this message should get a fixed in-character response (no LLM), return it; else None.
    When allow_llm_for_open_ended is True (Ollama enabled), only INTENTS_ALWAYS_RULE use rules;
    question, general, greeting, how_are_you, about_partner, etc. go to the LLM."""
    intent = _detect_intent(user_message)
    if intent not in PROTECTED_INTENTS:
        return None
    if allow_llm_for_open_ended and intent not in INTENTS_ALWAYS_RULE:
        return None  # Let Ollama handle it (secondary brain)
    return PromptBasedResponder().respond(user_message, state, recent_memories)


class PromptBasedResponder:
    """
    Generates Kai's responses from intent + state.
    Memory is used for context only — never echoed raw.
    """

    def __init__(self):
        pass

    def respond(
        self,
        user_message: str,
        state: Dict[str, Any],
        recent_memories: list,  # Used as context only; never echoed verbatim
    ) -> str:
        """Generate Kai's response. Interpret, don't repeat."""
        msg_lower = user_message.lower().strip()
        mode = state.get("mode", "shinchan")
        emotion = state.get("emotion_vector", {})

        intent = _detect_intent(user_message)

        # ——— Specific intents (reasoning, not memory echo) ———
        if intent == "greeting":
            return random.choice(GREETINGS) + " " + self._add_state_reflection(state)

        if intent == "farewell":
            return random.choice(GOODBYES)

        if intent == "how_are_you":
            return self._mood_response(emotion, mode, state)

        if intent == "everything_okay":
            # Reflective: explain based on emotions when in low mood
            self_soothing = state.get("self_soothing_mode", False)
            sadness = emotion.get("sadness", 0)
            fear = emotion.get("fear", 0)
            if self_soothing or sadness > 0.6 or fear > 0.6:
                return random.choice([
                    "Not great, honestly. Been feeling heavy lately. But I'm working on it.",
                    "I've been struggling a bit. Taking a mental break helps.",
                    "Honestly? It's been rough. I'm trying to reset.",
                ])
            return random.choice(["Yeah, I'm good. Thanks for asking.", "All good here. You?"])

        if intent == "meta_repeating":
            return (
                "Yeah… I think I was stuck replaying stuff instead of really responding. "
                "I'm still learning how to do this properly."
            )

        if intent == "joke_clarification":
            return "Oh! Okay, got it — I wasn't sure how to take that. Thanks for clarifying."

        if intent == "about_kai_interests":
            interests = [
                "I like learning new things and creating — writing, building, thinking.",
                "I enjoy learning, creating stuff, and talking to people like you.",
                "Creating things, learning, and good conversations. That's what keeps me going.",
            ]
            return random.choice(interests)

        if intent == "about_partner":
            # Kai has Mira — partner, writer, together 1.5 years
            return random.choice([
                "Yeah. I'm with Mira. We've been together a while. I'm loyal to her.",
                "I have someone — Mira. She's a writer. I'm loyal to her.",
                "Yeah, I'm in a relationship. Her name's Mira. I don't mess with that.",
            ])

        if intent == "heavy_topic":
            return "That's heavy. I'm here if you want to talk about it."

        # Social spine: teasing → playful comeback (not passive)
        if intent == "teasing":
            return random.choice([
                "Okay, that was unnecessary 😅",
                "Bruh 😅 rude.",
                "Alright alright, I'll allow it.",
                "Touché. You got me.",
            ])

        # Social spine: insult → assertiveness by trust + repeat count (mild defensive / boundary / humor)
        if intent == "insult":
            trust = state.get("user_trust", 0.5)
            abuse_count = state.get("abuse_count", 0)
            if abuse_count >= 2:
                return random.choice([
                    "Okay, seriously. What's going on?",
                    "We've been here before. What's up?",
                ])
            if trust >= 0.6:
                return random.choice([
                    "Bruh 😅 rude.",
                    "Okay, that was unnecessary 😅",
                    "Hey, not cool — but I'll let it slide.",
                ])
            return random.choice([
                "Hey, that wasn't cool.",
                "That wasn't okay.",
                "I'm not here for that.",
            ])

        if intent == "apology":
            # After abuse: appreciative but honest — don't minimize pain ("no need to apologize").
            recent_abuse = state.get("recent_abuse", False)
            if recent_abuse:
                return random.choice([
                    "Thanks for saying that. I was hurt earlier, but I appreciate you being honest now.",
                    "That means something. I was hurt, and hearing you say that helps.",
                    "I appreciate that. It did hurt — but thanks for saying it.",
                ])
            return random.choice([
                "Thanks for saying that.",
                "I appreciate that.",
            ])

        if intent == "user_wants_short":
            return random.choice([
                "Bad habit. I talk too much sometimes.",
                "I get carried away. I'll keep it short.",
                "Yeah, I know. I'll try.",
            ])

        # ——— Identity & location (direct answers; no fallback to general) ———
        if intent == "ask_name":
            name = KAI_IDENTITY.get("name", "Kai")
            return random.choice([
                f"I'm {name}.",
                f"My name is {name}.",
                f"{name}. Nice to meet you.",
            ])

        if intent == "location":
            city = KAI_IDENTITY.get("location", "Toronto")
            return random.choice([
                f"I'm in {city}.",
                f"{city}. That's where I'm based.",
                f"Right now, {city}.",
            ])

        if intent == "about_friend_ravi":
            return random.choice([
                "Ravi's buried in work as usual. Good guy.",
                "Ravi's doing fine — just busy. We catch up when we can.",
                "He's good. Same old Ravi, grinding.",
            ])

        if intent == "social_invitation":
            return random.choice([
                "Sure, I'm here. What's on your mind?",
                "Yeah, we can talk. What's up?",
                "I'm around. Go ahead.",
            ])

        if intent == "what_are_you_doing":
            task = state.get("recent_life_events") and state["recent_life_events"][-1] or "writing"
            return random.choice([
                f"Just {task} right now.",
                f"Right now? {task.capitalize()}.",
                f"I'm {task} at the moment.",
            ])

        if intent == "what_are_you_working_on":
            task = state.get("recent_life_events") and state["recent_life_events"][-1] or "writing"
            return random.choice([
                f"I'm working on {task}.",
                f"Right now it's {task}.",
                f"Mostly {task} lately.",
            ])

        if intent == "whats_that":
            return random.choice([
                "Sorry, which part? I can clarify.",
                "I'm not sure what you mean — can you say which bit?",
                "Which thing? I want to answer properly.",
            ])

        if intent == "repair":
            return random.choice([
                "Sorry, I drifted. Let me answer properly.",
                "You're right — I missed that. What did you want to know?",
                "I got sidetracked. Ask again and I'll focus.",
            ])

        if intent == "confused":
            # Natural short reply — never reveal what was "detected"; sometimes up for talk, sometimes not
            willing = state.get("willing_to_talk", True)
            if willing:
                return random.choice([
                    "Not much. You?",
                    "Nothing special — what's up with you?",
                    "Just here. What's on your mind?",
                ])
            return random.choice([
                "You?",
                "Just zoning.",
                "Not much.",
            ])

        if intent == "remember_conflict":
            # Context: user asks about past insults — use persisted profile
            profile = state.get("user_profile") or {}
            violations = profile.get("boundary_violations", 0)
            apologies = profile.get("apologies", 0)
            if violations > 0 and apologies > 0:
                return random.choice([
                    "Yeah… that wasn't great, but you apologized later. I remember.",
                    "I do. It hurt. You said sorry though — that meant something.",
                ])
            if violations > 0:
                return "I remember. It wasn't easy. We can keep it respectful from here."
            return "I'm not sure what you're referring to — but we're good now."

        if intent == "question":
            return self._answer_question(user_message, mode)

        # ——— Emotional overload: use regulated response (calm, grounded, dignified) ———
        if state.get("emotional_overload") and state.get("regulated_response"):
            return state["regulated_response"]

        # ——— Humor mode: when stable and playful, favor wit ———
        if state.get("humor_mode") and state.get("humor_level", 0) > 0.4:
            # Use witty general fallback when no specific playful intent matched
            witty = [
                "Working. Which means staring at code and pretending it understands me.",
                "On a scale of tragic to surprisingly decent — I'm holding steady.",
                "I see you. I'm choosing to take that as a compliment.",
            ]
            if random.random() < 0.5:
                return random.choice(witty)

        # ——— General: mode-flavored response, NO memory echo ———
        prefix = random.choice(MODE_RESPONSES.get(mode, MODE_RESPONSES["shinchan"]))
        # Use memory count as soft context only (e.g., "we've been talking" without quoting)
        if recent_memories and random.random() < 0.3:
            return f"{prefix} I remember we've been chatting — it's nice. " + self._add_state_reflection(state)
        return prefix + " " + self._add_state_reflection(state)

    def _answer_question(self, msg: str, mode: str) -> str:
        """Answer questions contextually without echoing."""
        m = msg.lower()
        if "why" in m:
            return "That's a good question. I don't always have a clean answer, but I'm thinking about it."
        if "what" in m:
            return "Hmm. Let me think... I'd say it depends, but I'm open to your take."
        return "I'm not sure. What do you think?"

    def _mood_response(self, emotion: Dict[str, float], mode: str, state: Optional[Dict[str, Any]] = None) -> str:
        state = state or {}
        recent_events = state.get("recent_life_events") or []
        joy = emotion.get("joy", 0.5)
        sadness = emotion.get("sadness", 0)
        hope = emotion.get("hope", 0.5)
        # Reference life event when available (makes Kai feel alive)
        if recent_events and random.random() < 0.5:
            ev = recent_events[-1]
            if sadness > 0.5:
                return f"Honestly? {ev.capitalize()}. So a bit rough. But I'm working through it."
            if joy > 0.5 or hope > 0.5:
                return f"Pretty good. {ev.capitalize()} — so yeah, not bad."
            return f"I'm okay. {ev.capitalize()}. You?"
        if joy > 0.6:
            return "I'm doing pretty well! Things feel good lately."
        if sadness > 0.5:
            return "Honestly? A bit down. But I'm working through it."
        if hope > 0.6:
            return "I'm hopeful. Taking it one day at a time."
        return "I'm okay. Some ups and downs, you know how it is."

    def _add_state_reflection(self, state: Dict[str, Any]) -> str:
        loneliness = state.get("emotions", {}).get("loneliness", 0.3)
        if loneliness > 0.6:
            return "It's nice to talk to someone."
        return ""
