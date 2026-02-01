"""Kai data — relationships, lore, biographies, persona, philosophy."""

from .persona import get_persona, get_persona_for_llm
from .philosophy import get_svara_dharma_prompt, get_reflection_cycle, get_svara_dharma_anchor, is_asking_about_beliefs, CORE_BELIEF_HOOK
from .relationships import (
    get_all_bios,
    get_bio,
    get_context_summary,
    FAMILY,
    FRIEND,
    PARTNER,
    MENTOR,
    USER,
)

__all__ = [
    "get_persona",
    "get_persona_for_llm",
    "get_svara_dharma_prompt",
    "get_reflection_cycle",
    "get_svara_dharma_anchor",
    "is_asking_about_beliefs",
    "CORE_BELIEF_HOOK",
    "get_all_bios",
    "get_bio",
    "get_context_summary",
    "FAMILY",
    "FRIEND",
    "PARTNER",
    "MENTOR",
    "USER",
]
