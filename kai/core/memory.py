"""
Kai Memory System - Human-like layered memory with emotion-weighted encoding.
STM -> LTM -> Conscious / Subconscious
"""

import time
import json
import hashlib
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

from kai.config import (
    EMOTIONS,
    MEMORY_WEIGHT_FORGET,
    MEMORY_WEIGHT_SHORT_TERM,
    MEMORY_WEIGHT_LONG_TERM,
    MEMORY_WEIGHT_IDENTITY,
    MEMORY_WEIGHT_TRAUMA,
    KaiConfig,
)


@dataclass
class Memory:
    """Single memory with emotion vector."""
    id: str
    event: str
    context: str = ""
    timestamp: float = field(default_factory=time.time)
    emotion: Dict[str, float] = field(default_factory=dict)
    weight: float = 0.0
    layer: str = "stm"  # stm, ltm, conscious, subconscious
    lesson: str = ""
    recalled_count: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["emotion"] = {k: float(v) for k, v in (self.emotion or {}).items()}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Memory":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ShortTermMemory:
    """Working memory - limited capacity, fast decay."""

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.memories: List[Memory] = []

    def add(self, memory: Memory):
        self.memories.append(memory)
        while len(self.memories) > self.capacity:
            self.memories.pop(0)

    def get_recent(self, n: int = 3) -> List[Memory]:
        return self.memories[-n:]

    def clear(self):
        self.memories.clear()


class MemorySystem:
    """
    Emotion-weighted memory system with 4 layers:
    - Short-term (STM): Current context
    - Long-term (LTM): Life events
    - Conscious: Identity, self-narrative
    - Subconscious: Trauma, hidden influence
    """

    def __init__(self, config: Optional[KaiConfig] = None, persist_path: Optional[Path] = None):
        self.config = config or KaiConfig()
        self.persist_path = persist_path or Path("./kai_memory")
        self.persist_path.mkdir(parents=True, exist_ok=True)

        self.stm = ShortTermMemory(capacity=self.config.stm_capacity)
        self.ltm: List[Memory] = []
        self.conscious: List[Memory] = []
        self.subconscious: List[Memory] = []

        self._load()

    def _compute_weight(
        self,
        emotion: Dict[str, float],
        novelty: float = 0.5,
        repetition: float = 1.0
    ) -> float:
        """Compute memory importance from emotion vector."""
        if not emotion:
            return 0.0
        max_emotion = max(emotion.values()) if emotion else 0
        avg_emotion = sum(emotion.values()) / len(emotion) if emotion else 0
        weight = (
            0.3 * max_emotion +
            0.3 * avg_emotion +
            0.2 * novelty +
            0.2 * min(repetition, 1.0)
        )
        return min(1.0, weight)

    def _emotion_vector(self, emotion: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Ensure emotion has all dimensions."""
        base = {e: 0.0 for e in EMOTIONS}
        if emotion:
            for k, v in emotion.items():
                if k in base:
                    base[k] = min(1.0, max(0.0, float(v)))
        return base

    def _assign_layer(self, weight: float, emotion: Dict[str, float]) -> str:
        """Decide which layer based on weight and emotion."""
        fear_shame = (emotion.get("fear", 0) + emotion.get("shame", 0)) / 2
        if weight >= MEMORY_WEIGHT_TRAUMA and fear_shame > 0.6:
            return "subconscious"
        if weight >= MEMORY_WEIGHT_IDENTITY:
            return "conscious"
        if weight >= MEMORY_WEIGHT_LONG_TERM:
            return "ltm"
        if weight >= MEMORY_WEIGHT_SHORT_TERM:
            return "stm"
        return "forget"

    def store(
        self,
        event: str,
        context: str = "",
        emotion: Optional[Dict[str, float]] = None,
        novelty: float = 0.5,
        repetition: float = 1.0,
    ) -> Optional[Memory]:
        """Store experience with emotion-weighted encoding."""
        emotion_vec = self._emotion_vector(emotion)
        weight = self._compute_weight(emotion_vec, novelty, repetition)

        if weight < MEMORY_WEIGHT_FORGET:
            return None

        mem_id = hashlib.sha256(
            f"{event}{time.time()}".encode()
        ).hexdigest()[:16]

        memory = Memory(
            id=mem_id,
            event=event,
            context=context,
            emotion=emotion_vec,
            weight=weight,
            layer="stm",
            timestamp=time.time(),
        )

        layer = self._assign_layer(weight, emotion_vec)
        memory.layer = layer

        if layer == "forget":
            return None

        self.stm.add(memory)

        if layer == "ltm":
            self.ltm.append(memory)
            self._trim_ltm()
        elif layer == "conscious":
            self.conscious.append(memory)
            self._trim_conscious()
        elif layer == "subconscious":
            self.subconscious.append(memory)

        self._save()
        return memory

    def _trim_ltm(self, max_size: int = 1000):
        """Keep LTM bounded, remove lowest weight."""
        if len(self.ltm) > max_size:
            self.ltm.sort(key=lambda m: m.weight, reverse=True)
            self.ltm = self.ltm[:max_size]

    def _trim_conscious(self, max_size: int = 100):
        if len(self.conscious) > max_size:
            self.conscious = self.conscious[-max_size:]

    def recall(
        self,
        query: str = "",
        current_mood: Optional[Dict[str, float]] = None,
        layer: Optional[str] = None,
        limit: int = 5,
    ) -> List[Memory]:
        """Recall memories - mood-congruent bias."""
        candidates = []

        if layer == "stm" or layer is None:
            candidates.extend(self.stm.get_recent(limit))
        if layer == "ltm" or layer is None:
            candidates.extend(self.ltm[-limit * 2:])
        if layer == "conscious" or layer is None:
            candidates.extend(self.conscious[-limit:])
        if layer == "subconscious":
            candidates.extend(self.subconscious[-limit:])

        # Boost recall by recency and weight
        scored = []
        for m in candidates:
            score = m.weight * (1 + 0.1 * m.recalled_count)
            # Mood-congruent: similar emotions recalled easier
            if current_mood and m.emotion:
                similarity = sum(
                    current_mood.get(k, 0) * m.emotion.get(k, 0)
                    for k in set(current_mood) & set(m.emotion)
                )
                score *= 1 + 0.2 * similarity
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        result = [m for _, m in scored[:limit]]

        for m in result:
            m.recalled_count += 1

        return result

    def consolidate(self, decay_rate: float = 0.01):
        """Sleep-like consolidation - decay, reclassify."""
        now = time.time()
        for mem in self.ltm:
            age = now - mem.timestamp
            mem.weight *= math.exp(-decay_rate * age / 86400)
        self._trim_ltm()
        self._save()

    def _save(self):
        """Persist to disk."""
        data = {
            "ltm": [m.to_dict() for m in self.ltm],
            "conscious": [m.to_dict() for m in self.conscious],
            "subconscious": [m.to_dict() for m in self.subconscious],
        }
        path = self.persist_path / "memory.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from disk."""
        path = self.persist_path / "memory.json"
        if not path.exists():
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self.ltm = [Memory.from_dict(m) for m in data.get("ltm", [])]
            self.conscious = [Memory.from_dict(m) for m in data.get("conscious", [])]
            self.subconscious = [Memory.from_dict(m) for m in data.get("subconscious", [])]
        except Exception:
            pass
