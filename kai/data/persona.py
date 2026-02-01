"""
Kai Persona Database — Canonical facts. Load once, use everywhere.
Prevents hallucinated friends, family, or stories.
"""

import json
from pathlib import Path
from typing import Dict, Any


_PERSONA: Dict[str, Any] | None = None


def _load_persona() -> Dict[str, Any]:
    """Load persona.json. Cached for reuse."""
    global _PERSONA
    if _PERSONA is not None:
        return _PERSONA
    path = Path(__file__).parent / "persona.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            _PERSONA = json.load(f)
    else:
        _PERSONA = {
            "identity": {"name": "Kai", "gender": "male", "job": "freelancer"},
            "partner": {"name": "Mira"},
            "friends": [{"name": "Ravi"}],
            "rules": ["NEVER invent new friends, family, or people."],
        }
    return _PERSONA


def get_persona() -> Dict[str, Any]:
    """Canonical persona. Load once, reuse always."""
    return _load_persona()


def get_persona_for_llm() -> str:
    """Format persona as strict system-prompt text for LLM."""
    p = get_persona()
    lines = [
        "CANONICAL FACTS (use only these; never invent):",
        f"- Identity: {p.get('identity', {}).get('name', 'Kai')}, {p.get('identity', {}).get('gender', 'male')}, {p.get('identity', {}).get('job', 'freelancer')}.",
        f"- Partner: {p.get('partner', {}).get('name', 'Mira')}. Together 1.5 years. Writer and editor.",
        f"- Friends: {', '.join(f.get('name', '?') for f in p.get('friends', []))}.",
        f"- Mentor: {p.get('mentor', {}).get('name', 'Dr. Sharma')}. Retired professor.",
        f"- Family: {p.get('family', {}).get('description', 'Raised Kai. In touch.')}.",
        " ".join(p.get("rules", [])),
    ]
    return "\n".join(lines)
