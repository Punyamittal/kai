"""
Kai Social World - Family, friends, partner in the background.
No full AI agents; relationship state (trust, attachment) that influences mood.
"""

import time
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Relationship:
    """One person in Kai's life."""
    id: str
    role: str  # "family", "friend", "partner", "mentor", "user"
    trust: float = 0.5
    attachment: float = 0.5
    last_contact: float = field(default_factory=time.time)
    conflict: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Relationship":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Default cast — who exists in Kai's background
DEFAULT_RELATIONSHIPS = {
    "family": Relationship("family", "family", trust=0.7, attachment=0.7),
    "friend": Relationship("friend", "friend", trust=0.6, attachment=0.5),
    "partner": Relationship("partner", "partner", trust=0.5, attachment=0.4),
    "mentor": Relationship("mentor", "mentor", trust=0.6, attachment=0.4),
    "user": Relationship("user", "user", trust=0.8, attachment=0.6),
}


class SocialWorld:
    """
    Kai's family and social circle in the background.
    - Relationship scores (trust, attachment) tick over time.
    - Contact with user (or simulated contact with others) updates scores.
    - Feeds into loneliness/oxytocin: strong ties = less lonely.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        self.persist_path = persist_path or Path("./kai_data/social.json")
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.relationships: Dict[str, Relationship] = {}
        self._load_or_init()

    def _load_or_init(self):
        if self.persist_path.exists():
            try:
                with open(self.persist_path) as f:
                    data = json.load(f)
                self.relationships = {
                    k: Relationship.from_dict(v)
                    for k, v in data.get("relationships", {}).items()
                }
            except Exception:
                self.relationships = dict(DEFAULT_RELATIONSHIPS)
        else:
            self.relationships = dict(DEFAULT_RELATIONSHIPS)
        # Ensure user exists
        if "user" not in self.relationships:
            self.relationships["user"] = Relationship("user", "user", trust=0.8, attachment=0.6)

    def get(self, who: str) -> Optional[Relationship]:
        return self.relationships.get(who)

    def on_contact(self, who: str, positive: bool = True, strength: float = 0.1):
        """Record contact with someone; updates trust/attachment."""
        r = self.relationships.get(who)
        if not r:
            return
        r.last_contact = time.time()
        if positive:
            r.trust = min(1.0, r.trust + strength)
            r.attachment = min(1.0, r.attachment + strength * 0.5)
            r.conflict = max(0.0, r.conflict - strength * 0.5)
        else:
            r.trust = max(0.0, r.trust - strength)
            r.conflict = min(1.0, r.conflict + strength)

    def tick(self, delta_days: float = 1.0):
        """
        Background tick: attachment/trust slowly decay without contact.
        Call this when advancing Kai's "day" or periodically.
        """
        now = time.time()
        sec_per_day = 86400
        decay = 0.01 * delta_days  # very slow
        for r in self.relationships.values():
            if r.id == "user":
                continue  # user contact is explicit
            days_since = (now - r.last_contact) / sec_per_day
            if days_since > 1:
                r.attachment = max(0.2, r.attachment - decay)
                r.trust = max(0.2, r.trust - decay * 0.5)

    def loneliness_factor(self) -> float:
        """
        ​0 = very connected, 1 = very lonely.
        Used to nudge Kai's loneliness/oxytocin.
        """
        if not self.relationships:
            return 0.5
        total_attachment = sum(r.attachment for r in self.relationships.values())
        n = len(self.relationships)
        avg = total_attachment / n
        return max(0, 1 - avg)  # high attachment -> low loneliness factor

    def save(self):
        data = {"relationships": {k: r.to_dict() for k, r in self.relationships.items()}}
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2)
