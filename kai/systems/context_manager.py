"""
Kai Context Manager — Conversation history + user profile, persisted.
So Kai uses history and survives restarts (no amnesia).
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class UserProfile:
    """Persisted summary of user behavior across sessions."""
    boundary_violations: int = 0   # total insults/abuse
    apologies: int = 0
    trust_level: float = 0.7
    pattern_harassment: bool = False  # same insult repeated many times

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "UserProfile":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ContextManager:
    """
    - Conversation history: last N turns (user, kai, emotion_stat), persisted.
    - User profile: boundary_violations, apologies, trust_level, persisted.
    Load on startup, save after each turn. So context survives restart.
    """

    def __init__(self, persist_path: Optional[Path] = None, max_history: int = 30):
        self.persist_path = persist_path or Path("./kai_data")
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history

        self.history: List[Dict[str, Any]] = []  # [{user, kai, emotion_stat}, ...]
        self.user_profile = UserProfile()

        self._load()

    def _load(self) -> None:
        """Load conversation history and user profile from disk."""
        conv_path = self.persist_path / "conversation.json"
        if conv_path.exists():
            try:
                with open(conv_path) as f:
                    data = json.load(f)
                self.history = data.get("history", [])[-self.max_history:]
            except Exception:
                self.history = []

        profile_path = self.persist_path / "user_profile.json"
        if profile_path.exists():
            try:
                with open(profile_path) as f:
                    data = json.load(f)
                self.user_profile = UserProfile.from_dict(data)
            except Exception:
                pass

    def save(self) -> None:
        """Persist history and user profile."""
        conv_path = self.persist_path / "conversation.json"
        with open(conv_path, "w") as f:
            json.dump({"history": self.history[-self.max_history:]}, f, indent=2)

        profile_path = self.persist_path / "user_profile.json"
        with open(profile_path, "w") as f:
            json.dump(self.user_profile.to_dict(), f, indent=2)

    def append_turn(self, user: str, kai: str, emotion_stat: Dict[str, Any]) -> None:
        """Add one turn; keep last max_history."""
        self.history.append({
            "user": user,
            "kai": kai,
            "emotion_stat": emotion_stat,
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.save()

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Last n turns for LLM context."""
        return self.history[-n:] if self.history else []

    def get_context_for_llm(self, n: int = 10) -> str:
        """Formatted string: recent conversation + user profile summary."""
        lines = []
        profile = self.user_profile
        lines.append(
            f"User profile: boundary_violations={profile.boundary_violations}, "
            f"apologies={profile.apologies}, trust_level={round(profile.trust_level, 2)}."
        )
        if profile.pattern_harassment:
            lines.append("Pattern: user has repeated same insults (harassment).")
        lines.append("")
        lines.append("Recent conversation:")
        for i, turn in enumerate(self.get_recent(n), 1):
            lines.append(f"  {i}. User: {turn['user'][:200]}")
            lines.append(f"     Kai: {turn['kai'][:200]}")
        return "\n".join(lines)

    def update_profile(
        self,
        boundary_violations: Optional[int] = None,
        apologies: Optional[int] = None,
        trust_level: Optional[float] = None,
        pattern_harassment: Optional[bool] = None,
    ) -> None:
        """Update user profile and save."""
        if boundary_violations is not None:
            self.user_profile.boundary_violations = boundary_violations
        if apologies is not None:
            self.user_profile.apologies = apologies
        if trust_level is not None:
            self.user_profile.trust_level = max(0, min(1, trust_level))
        if pattern_harassment is not None:
            self.user_profile.pattern_harassment = pattern_harassment
        self.save()
