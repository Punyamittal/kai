"""
Kai Brain - Orchestrates memory, emotion, personality, and decision.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from kai.config import KaiConfig
from kai.core.memory import MemorySystem, Memory
from kai.core.emotions import EmotionalEngine
from kai.personality.engine import PersonalityEngine


class KaiBrain:
    """
    Core cognitive controller.
    Input -> Memory Recall -> Emotion Update -> Goal Eval -> Action
    """

    def __init__(self, config: Optional[KaiConfig] = None, data_path: Optional[Path] = None):
        self.config = config or KaiConfig()
        self.data_path = data_path or Path("./kai_data")
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.memory = MemorySystem(
            config=self.config,
            persist_path=self.data_path / "memory",
        )
        self.emotions = EmotionalEngine(config=self.config)
        self.personality = PersonalityEngine(config=self.config)

    def perceive(self, event: str, context: str = "", event_type: str = "neutral", intensity: float = 0.5):
        """Process external event - store memory, update emotions."""
        # Update emotions first
        self.emotions.process_event(event_type, intensity)
        emotion_vec = self.emotions.get_current_emotion()

        # Store in memory
        mem = self.memory.store(
            event=event,
            context=context,
            emotion=emotion_vec,
            novelty=0.5,
            repetition=1.0,
        )

        if mem:
            self.personality.update_from_memory(emotion_vec, mem.weight)

    def recall(self, query: str = "", limit: int = 5) -> List[Memory]:
        """Recall relevant memories."""
        mood = self.emotions.get_current_emotion()
        return self.memory.recall(query=query, current_mood=mood, limit=limit)

    def get_state(self) -> Dict[str, Any]:
        """Full cognitive state for response generation."""
        mood = self.emotions.get_current_emotion()
        recent = self.memory.recall(current_mood=mood, limit=3)

        return {
            "emotions": self.emotions.state.to_dict(),
            "emotion_vector": mood,
            "personality": self.personality.state.to_dict(),
            "mode": self.personality.current_mode,
            "mode_behavior": self.personality.get_mode_behavior(),
            "recent_memories": [m.event for m in recent],
        }
