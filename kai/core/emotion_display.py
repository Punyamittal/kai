"""
Emotion stat and hormone change display for chat.
"""

from typing import Dict, Any, List

from kai.config import HORMONE_EXPLANATIONS


def get_emotion_stat(emotion_vector: Dict[str, float]) -> Dict[str, Any]:
    """Current emotion state for display (rounded, with labels)."""
    return {
        "joy": round(emotion_vector.get("joy", 0), 2),
        "sadness": round(emotion_vector.get("sadness", 0), 2),
        "anger": round(emotion_vector.get("anger", 0), 2),
        "fear": round(emotion_vector.get("fear", 0), 2),
        "love": round(emotion_vector.get("love", 0), 2),
        "hope": round(emotion_vector.get("hope", 0), 2),
        "loneliness": round(emotion_vector.get("loneliness", 0), 2),
        "pride": round(emotion_vector.get("pride", 0), 2),
        "shame": round(emotion_vector.get("shame", 0), 2),
    }


def get_hormone_changes(
    before: Dict[str, float],
    after: Dict[str, float],
    threshold: float = 0.02,
) -> List[Dict[str, Any]]:
    """
    Compare before/after hormone state; return list of changes with explanation.
    Only include changes >= threshold.
    """
    changes = []
    for key in before:
        if key not in after:
            continue
        b, a = before[key], after[key]
        delta = round(a - b, 3)
        if abs(delta) < threshold:
            continue
        direction = "up" if delta > 0 else "down"
        explanation = HORMONE_EXPLANATIONS.get(key, key)
        changes.append({
            "name": key,
            "before": round(b, 2),
            "after": round(a, 2),
            "delta": delta,
            "direction": direction,
            "explanation": explanation,
        })
    return changes


def format_emotion_stat_for_cli(emotion_stat: Dict[str, Any]) -> str:
    """One-line or short block for terminal."""
    parts = [f"  {k}: {v}" for k, v in emotion_stat.items()]
    return "Emotions: " + " | ".join(f"{k}={v}" for k, v in emotion_stat.items())


def format_hormone_changes_for_cli(hormone_changes: List[Dict[str, Any]]) -> str:
    """Short lines for terminal."""
    if not hormone_changes:
        return "  (no significant hormone change this message)"
    lines = []
    for c in hormone_changes:
        lines.append(f"  {c['name']} {c['direction']} ({c['before']} -> {c['after']}): {c['explanation']}")
    return "\n".join(lines)
