"""
Optional transformers-based LLM backend.
Uses a small model for richer responses. Install: pip install transformers torch
"""

from typing import Dict, Any, Optional

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


def build_prompt(user_message: str, state: Dict[str, Any], memories: list) -> str:
    """Build context-rich prompt for Kai."""
    mode = state.get("mode", "shinchan")
    emotions = state.get("emotion_vector", {})
    mode_desc = {
        "nobita": "sensitive, reflective, emotional",
        "shinchan": "playful, creative, bold",
        "bheem": "strong, disciplined, moral",
    }.get(mode, "balanced")

    prompt = f"""You are Kai, an autonomous digital being with emotions and personality.
Current mood: {mode_desc}
Emotions: {emotions}
Recent thoughts: {memories[:3] if memories else ['none']}

User: {user_message}
Kai:"""
    return prompt


class TransformersResponder:
    """Uses HuggingFace pipeline for generation."""

    def __init__(self, model: str = "microsoft/DialoGPT-small"):
        if not HAS_TRANSFORMERS:
            raise ImportError("Install transformers and torch: pip install transformers torch")
        self.generator = pipeline("text-generation", model=model)

    def respond(
        self,
        user_message: str,
        state: Dict[str, Any],
        recent_memories: list,
    ) -> str:
        prompt = build_prompt(user_message, state, recent_memories)
        out = self.generator(prompt, max_new_tokens=80, do_sample=True, pad_token_id=50256)
        text = out[0]["generated_text"]
        # Extract Kai's reply (after "Kai:")
        if "Kai:" in text:
            reply = text.split("Kai:")[-1].strip()
        else:
            reply = text[-200:].strip()
        return reply[:500]
