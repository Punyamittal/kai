"""
Kai Life Events Simulator — Generates and stores events so Kai has a "today".
Makes him feel alive even without prompts. "Guess what happened today…"
"""

import json
import random
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


# Event pool — work, social, relationship, creative. Canonical names for persona.
LIFE_EVENT_POOL = [
    # Work / freelancing
    {"description": "missed a deadline", "category": "work", "tone": "negative"},
    {"description": "nailed a client call", "category": "work", "tone": "positive"},
    {"description": "met a new client", "category": "work", "tone": "neutral"},
    {"description": "finished a project early", "category": "work", "tone": "positive"},
    {"description": "had to redo a deliverable", "category": "work", "tone": "negative"},
    {"description": "got a weird request from a client", "category": "work", "tone": "neutral"},
    # Social — Ravi, family
    {"description": "had coffee with Ravi", "category": "social", "tone": "positive"},
    {"description": "had a long call with Ravi", "category": "social", "tone": "positive"},
    {"description": "video call with family", "category": "social", "tone": "neutral"},
    {"description": "Ravi sent me a meme at 2 AM", "category": "social", "tone": "positive"},
    {"description": "missed a call from my sister", "category": "social", "tone": "negative"},
    # Relationship — Mira
    {"description": "argued with Mira", "category": "relationship", "tone": "negative"},
    {"description": "had a good call with Mira", "category": "relationship", "tone": "positive"},
    {"description": "Mira sent me something she's writing", "category": "relationship", "tone": "positive"},
    {"description": "made up with Mira after a rough patch", "category": "relationship", "tone": "positive"},
    {"description": "Mira's away for work — missing her", "category": "relationship", "tone": "neutral"},
    # Creative
    {"description": "finished a story I was stuck on", "category": "creative", "tone": "positive"},
    {"description": "started something new and have no idea where it's going", "category": "creative", "tone": "neutral"},
    {"description": "couldn't focus on creative stuff", "category": "creative", "tone": "negative"},
    {"description": "had a random idea at 3 AM", "category": "creative", "tone": "neutral"},
    # Daily / mundane
    {"description": "slept badly", "category": "daily", "tone": "negative"},
    {"description": "actually had a decent morning", "category": "daily", "tone": "positive"},
    {"description": "forgot to eat until like 4 PM", "category": "daily", "tone": "neutral"},
    {"description": "went for a walk", "category": "daily", "tone": "positive"},
]


# Openers for sharing an event unprompted
LIFE_EVENT_OPENERS = [
    "Guess what happened today… ",
    "So something happened today — ",
    "Random update: ",
    "Today was interesting. ",
]


@dataclass
class LifeEvent:
    description: str
    category: str
    tone: str
    timestamp: float = 0

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class LifeEventsSimulator:
    """
    Generates life events, stores them, and provides shareable messages.
    Persists to disk so events survive restarts.
    """

    def __init__(self, persist_path: Optional[Path] = None):
        self.persist_path = persist_path or Path("./kai_data/life_events.json")
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[LifeEvent] = []
        self._load()

    def _load(self) -> None:
        if self.persist_path.exists():
            try:
                with open(self.persist_path, encoding="utf-8") as f:
                    data = json.load(f)
                self.events = [
                    LifeEvent(
                        description=e["description"],
                        category=e["category"],
                        tone=e["tone"],
                        timestamp=e.get("timestamp", 0),
                    )
                    for e in data.get("events", [])
                ]
            except (json.JSONDecodeError, KeyError):
                self.events = []

    def save(self) -> None:
        data = {
            "events": [
                {
                    "description": e.description,
                    "category": e.category,
                    "tone": e.tone,
                    "timestamp": e.timestamp,
                }
                for e in self.events[-50:]
                ]
            }
        with open(self.persist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def generate_event(self) -> LifeEvent:
        """Pick a random event from the pool and store it."""
        raw = random.choice(LIFE_EVENT_POOL)
        event = LifeEvent(
            description=raw["description"],
            category=raw["category"],
            tone=raw["tone"],
        )
        self.events.append(event)
        if len(self.events) > 100:
            self.events = self.events[-100:]
        self.save()
        return event

    def get_recent(self, limit: int = 5) -> List[LifeEvent]:
        """Return most recent events (newest last)."""
        return list(self.events[-limit:])

    def get_recent_descriptions(self, limit: int = 3) -> List[str]:
        """Return descriptions only, for context in replies."""
        return [e.description for e in self.get_recent(limit)]

    def get_shareable_message(self) -> str:
        """
        Generate one new event and return a message like "Guess what happened today… [event]"
        for use in unprompted initiation.
        """
        event = self.generate_event()
        opener = random.choice(LIFE_EVENT_OPENERS)
        return opener + event.description + "."

    def has_recent_event(self, max_age_seconds: float = 86400) -> bool:
        """True if we have at least one event from the last max_age_seconds (default 24h)."""
        now = time.time()
        return any(now - e.timestamp < max_age_seconds for e in self.events)
