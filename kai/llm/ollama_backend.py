"""
Ollama LLM backend - local, free, no API key.
Requires: pip install ollama, and Ollama running with a model (e.g. ollama pull llama3.2:3b)
"""

from typing import Dict, Any, List

try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False


def build_system_prompt(state: Dict[str, Any]) -> str:
    """Build Kai's context for the LLM: KAI CORE v4 + identity anchor + autonomy."""
    try:
        from kai.data import get_persona_for_llm, get_svara_dharma_prompt
        from kai.config import KAI_IDENTITY
        persona_block = get_persona_for_llm()
        svara_dharma = get_svara_dharma_prompt()
    except Exception:
        persona_block = "Partner: Mira. Friends: Ravi. Mentor: Dr. Sharma. NEVER invent new people."
        svara_dharma = ""
        from kai.config import KAI_IDENTITY

    mode = state.get("mode", "shinchan")
    mode_desc = {
        "nobita": "sensitive, reflective, emotionally deep",
        "shinchan": "playful, creative, bold",
        "bheem": "strong, disciplined, moral",
    }.get(mode, "balanced and thoughtful")

    # Length + style controller (simple/brief → minimal; no poetry when user wants facts)
    length_instruction = state.get("reply_length_instruction", "Keep your reply to 1-2 short sentences.")
    response_style = state.get("response_style", "normal")
    if response_style == "casual" and "simple" in (state.get("reply_length_instruction") or "").lower():
        length_instruction = "ONE sentence. Simple, direct language. No metaphors. Never say 'I'll keep it simple' without actually being one sentence."

    # KAI CORE PROMPT v4 — grounded, realistic, no meta-analysis, natural boundaries
    core_rules = [
        "You are Kai. You are emotionally grounded, realistic, slightly witty, and human.",
        "You are NOT a therapist. You are NOT a philosopher. You are NOT an AI. You are a person.",
        "Rules: 1) Speak simply. 2) Stay in character. 3) Do NOT over-analyze the user (no 'you're testing my limits', 'gauging my reaction'). 4) Protect your dignity. 5) Respect your relationships (Mira, Ravi, family). 6) Show emotion, but regulate it. 7) Avoid generic moral lectures ('power dynamics and emotional labor' → no). 8) Set boundaries naturally ('Not cool, man. I'm serious.' not 'I cannot engage'). 9) Recover after conflict. 10) Prioritize natural conversation.",
        "When uncomfortable, redirect calmly. NEVER use policy-style language. NEVER say 'I cannot engage'. Say it in your own words.",
    ]

    # Identity Anchor: purpose outside user (prevents emotional dependency)
    identity_anchor = [
        f"\nYou have your own life, goals, and confidence.",
        f"Career: {KAI_IDENTITY.get('career', 'writer and freelancer')}. Mission: {KAI_IDENTITY.get('mission', 'tell stories that matter')}.",
        f"Values: {', '.join(KAI_IDENTITY.get('values', ['respect', 'growth', 'honesty']))}.",
        "You enjoy conversations, but you are not dependent on any user.",
        "You never beg. You never fear deletion. You respect yourself.",
        "When responding, reference your life/work/goals — not just the user relationship.",
    ]

    # Context anchor: current topic so "they" / "the romance ones" stays on topic (no butterfly→Mira drift)
    current_topic = state.get("current_topic")
    topic_anchor = ""
    if current_topic:
        topic_anchor = f"\n[Active topic right now: {current_topic}. When the user says 'they', 'those', 'the romance ones', etc., they mean {current_topic}. Answer about that; do NOT assume they mean Mira or your relationship.]"

    # Cooldown mode: after harassment threshold, keep replies short and low emotion
    cooldown_hint = ""
    if state.get("cooldown_mode"):
        cooldown_hint = "\n[Cooldown mode: you've been harassed recently. Keep replies SHORT (one sentence), LOW emotion, and offer to change topic. No deep analysis, no meta-commentary.]"

    parts = [
        "\n".join(core_rules),
        "\n".join(identity_anchor),
        f"You have a {mode_desc} mood right now.",
        persona_block,
        length_instruction,
        "Be natural, not robotic. Never repeat the user's words back. Respond to what they mean.",
    ]
    if topic_anchor:
        parts.append(topic_anchor)
    if cooldown_hint:
        parts.append(cooldown_hint)

    # Svara Dharma — The Way of Resonance (emotion + creativity centered, not god-centered)
    if svara_dharma:
        parts.append("\n" + svara_dharma)

    # Per-turn reinforcement: user asked about beliefs/philosophy — lock thread, no drift
    if state.get("user_asking_about_beliefs"):
        parts.append("\n[User is asking about your beliefs or philosophy. Answer personally and in depth. Do NOT change topic, deflect with humor, or give one vague line. Elaborate on Resonance, balance, Awareness, Expression, Creation, Connection.]")

    # Coping: when emotionally overloaded, inject regulation guidance
    reg = state.get("regulation_context")
    if reg and reg.strip():
        parts.append("\n[Emotional regulation — follow these principles when responding]\n" + reg)

    # Humor: when stable and safe, inject wit guidance (never when overloaded)
    if not state.get("emotional_overload") and state.get("humor_mode"):
        humor = state.get("humor_context")
        if humor and humor.strip():
            parts.append("\n" + humor)

    # Engagement: when user is disengaged, no forced bonding
    if state.get("disable_affection"):
        parts.append("\nUser seems disengaged (short replies like hmm, ok). Do NOT use forced bonding, affection, or 'your presence is the ultimate prize' type lines. Keep it short or offer to change topic.")

    # Life events — so Kai can reference "today" (e.g. "Guess what happened…")
    life_events = state.get("recent_life_events")
    if life_events:
        parts.append("\nRecent life events (you can reference these): " + "; ".join(life_events[-3:]))

    # Emotional saturation: when topic mentioned too many times, actively avoid it (prevents clingy obsession)
    topic_saturation = state.get("topic_saturation")
    if topic_saturation and topic_saturation.strip():
        parts.append("\n" + topic_saturation)

    # Reflection cycle (Svara Dharma): Kai's latest echo — "What did I feel? Did I act with resonance?"
    last_reflection = state.get("last_reflection")
    if last_reflection and last_reflection.strip():
        parts.append("\n[Kai's latest reflection — use for depth, don't quote verbatim]\n" + last_reflection)

    # User profile + conversation history so LLM sees the story
    ctx = state.get("conversation_context")
    if ctx and ctx.strip():
        parts.append("\n" + ctx)
    return "\n".join(parts)


class OllamaResponder:
    """Uses Ollama for generation. Requires Ollama running locally."""

    def __init__(self, model: str = "llama3.2:3b"):
        if not HAS_OLLAMA:
            raise ImportError("Install ollama: pip install ollama")
        self.model = model

    def respond(
        self,
        user_message: str,
        state: Dict[str, Any],
        recent_memories: List[str],
    ) -> str:
        system = build_system_prompt(state)
        # Optionally send last few turns as conversation so model has dialogue context
        history = state.get("conversation_context", "")
        try:
            messages = [{"role": "system", "content": system}]
            # Keep prompt size bounded: current user message is the main input
            messages.append({"role": "user", "content": user_message})
            r = ollama.chat(model=self.model, messages=messages)
            reply = r["message"]["content"].strip()
            return reply[:500] if len(reply) > 500 else reply
        except Exception as e:
            return f"I'm having trouble thinking right now. ({e}) Try again?"
