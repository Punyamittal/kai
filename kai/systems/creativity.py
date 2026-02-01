"""
Kai Creativity Engine - Polymath (writing, art, music, engineering, philosophy).
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from kai.config import CREATIVE_DOMAINS, KaiConfig


@dataclass
class CreativeIdea:
    content: str
    domain: str
    emotion: str = ""
    status: str = "unfinished"


class CreativityEngine:
    """
    Polymath creativity with cross-domain fusion.
    """

    def __init__(self, config: Optional[KaiConfig] = None):
        self.config = config or KaiConfig()
        self.domains: Dict[str, float] = {d: 0.5 for d in CREATIVE_DOMAINS}
        self.portfolio: List[CreativeIdea] = []
        self.inspiration_level = 0.5

    def mood_to_domain(self, mood: str) -> str:
        """Emotion suggests creative domain."""
        mapping = {
            "sad": "writing",
            "curious": "engineering",
            "inspired": "art_design",
            "confused": "philosophy",
            "confident": "engineering",
        }
        return mapping.get(mood, random.choice(CREATIVE_DOMAINS))

    def fuse_domains(self, a: str, b: str) -> str:
        """Cross-domain fusion concept."""
        fusions = {
            ("engineering", "philosophy"): "Ethical technology",
            ("music_emotion", "writing"): "Lyrical narrative",
            ("art_design", "engineering"): "Interactive experience",
        }
        key = tuple(sorted([a, b]))
        return fusions.get(key, f"{a} meets {b}")

    def generate_idea(self, emotion: str = "curious") -> CreativeIdea:
        """Create new creative seed."""
        domain = self.mood_to_domain(emotion)
        if random.random() < 0.3:
            other = random.choice([d for d in CREATIVE_DOMAINS if d != domain])
            concept = self.fuse_domains(domain, other)
        else:
            concept = f"New {domain} project"
        idea = CreativeIdea(content=concept, domain=domain, emotion=emotion)
        self.portfolio.append(idea)
        return idea
