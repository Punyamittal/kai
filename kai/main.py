"""
Kai - Self-Evolving Digital Being
Main orchestrator and CLI chat.
"""

import os
import random
import sys
import time
import threading
from pathlib import Path
from typing import Optional

from kai.config import KaiConfig, KAI_IDENTITY
from kai.core.brain import KaiBrain
from kai.core.emotion_display import (
    get_emotion_stat,
    get_hormone_changes,
    format_emotion_stat_for_cli,
    format_hormone_changes_for_cli,
)
from kai.systems import MoralSystem, MentalHealthSystem, CreativityEngine, SocialWorld, BoundaryEngine, ContextManager, KaiInitiator, CopingEngine, HumorEngine, LifeEventsSimulator, get_reply_length, trim_reply, get_engagement, get_minimal_reply, get_switch_topic_reply, get_topic_fatigue_reply
from kai.life import DailyLifeEngine, IrregularityEngine
from kai.llm import PromptBasedResponder
from kai.llm.prompt import get_fixed_response_if_any, _detect_intent
from kai.data.relationships import get_all_bios
from kai.data.philosophy import get_reflection_cycle, is_asking_about_beliefs


def _extract_topic_from_message(msg: str) -> Optional[str]:
    """Extract a concrete topic from user message (e.g. 'what are butterflies' → 'butterflies')."""
    m = msg.lower().strip()
    topic = None
    for prefix in ("what are ", "what is ", "what's ", "tell me about ", "about "):
        if prefix in m:
            rest = m.split(prefix, 1)[-1].strip()
            # First few words, skip leading articles
            words = [w for w in rest.split() if w not in ("a", "an", "the")][:4]
            if words:
                topic = " ".join(words).rstrip("?.,")
            break
    return topic if topic and len(topic) < 50 else None


def _needs_topic_anchor(msg: str) -> bool:
    """True if message is pronoun-heavy and needs context (they/those/the X ones) so we don't drift to Mira."""
    m = msg.lower().strip()
    if len(m) > 60:
        return False
    pronoun_phrases = ("what are they", "what is they", "the romance ones", "the love ones", "those ones", "what about those", "and those", "and they")
    if any(p in m for p in pronoun_phrases):
        return True
    words = set(m.split())
    if words <= {"they", "?"} or words <= {"those", "?"} or words <= {"it", "?"}:
        return True
    return False


def _expand_message_with_topic(user_message: str, current_topic: Optional[str]) -> str:
    """Prepend topic context for LLM so 'they' / 'the romance ones' stays anchored (no butterfly→Mira drift)."""
    if not current_topic or not _needs_topic_anchor(user_message):
        return user_message
    return f"[User is asking about: {current_topic}. Their message: {user_message}]"


def _create_responder(use_llm: Optional[bool] = None):
    """Use Ollama if KAI_USE_LLM=ollama or use_llm='ollama', else rule-based."""
    use_llm = use_llm or os.environ.get("KAI_USE_LLM", "").lower()
    if use_llm == "ollama":
        try:
            from kai.llm.ollama_backend import OllamaResponder
            return OllamaResponder(model=os.environ.get("KAI_OLLAMA_MODEL", "llama3.2:3b"))
        except ImportError:
            print("Warning: ollama not installed. Run: pip install ollama. Using rule-based responder.")
    return PromptBasedResponder()


def _using_ollama(kai_instance: "Kai") -> bool:
    """True if Kai is using Ollama as secondary brain (so open-ended intents go to LLM)."""
    return type(kai_instance.responder).__name__ == "OllamaResponder"


class Kai:
    """
    Complete Kai system - brain, systems, life, response.
    """

    def __init__(self, data_path: Optional[Path] = None):
        self.config = KaiConfig()
        self.data_path = data_path or Path("./kai_data")
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.brain = KaiBrain(config=self.config, data_path=self.data_path)
        self.moral = MoralSystem(config=self.config)
        self.mental = MentalHealthSystem(config=self.config)
        self.creativity = CreativityEngine(config=self.config)
        self.daily = DailyLifeEngine(config=self.config)
        self.irregularity = IrregularityEngine(config=self.config)
        self.social = SocialWorld(persist_path=self.data_path / "social.json")
        self.context = ContextManager(persist_path=self.data_path, max_history=30)
        self.boundary = BoundaryEngine(config=self.config)
        # Seed boundary from persisted user profile so context survives restart
        if self.context.user_profile.boundary_violations > 0:
            self.boundary.abuse_count = self.context.user_profile.boundary_violations
            if self.boundary.abuse_count >= self.boundary.bc.abuse_threshold:
                self.boundary.defense_mode = True
        self.responder = _create_responder()
        self.initiator = KaiInitiator()
        self.coping = CopingEngine()
        self.humor = HumorEngine()
        self.life_events = LifeEventsSimulator(persist_path=self.data_path / "life_events.json")
        self.topic_usage = {}  # e.g. {"mira": N} — topic fatigue when N > 3
        self._last_reflection = None  # Svara Dharma reflection cycle (echoes)
        self.last_user_message_time = time.time()
        # Conversation engine: loop breaker + memory (survives for session)
        self._last_kai_reply: Optional[str] = None
        self._repeat_count: int = 0
        # Topic tracker: anchor so "they" / "the romance ones" → current topic, not Mira drift
        self._current_topic: Optional[str] = None

    def chat(self, message: str) -> dict:
        """
        Process user message and return Kai's response plus emotion stat and hormone changes.
        Returns: { "response", "emotion_stat", "hormone_changes" }
        """
        self.last_user_message_time = time.time()

        # Snapshot state BEFORE (for hormone change explanation)
        hormones_before = dict(self.brain.emotions.state.to_dict())
        emotion_vector_now = self.brain.emotions.get_current_emotion()
        emotion_stat_now = get_emotion_stat(emotion_vector_now)

        # --- Boundary: disengagement — refuse to process, return boundary message
        if self.boundary.is_disengaged():
            self.boundary.step_disengage()
            return {
                "response": self.boundary.get_disengage_response(),
                "emotion_stat": emotion_stat_now,
                "hormone_changes": [],
            }

        # Detect event type from message for emotion update
        msg_lower = message.lower()
        event_type = "neutral"
        intensity = 0.5
        
        # Detect "leave" / "bye" / "quit" for exit anxiety handling (secure attachment)
        is_user_leaving = any(w in msg_lower for w in ["bye", "goodbye", "see you", "later", "quit", "gotta go", "take leave", "leaving"])

        _insult_words = (
            "ugly", "dumb", "stupid", "idiot", "bastard", "worthless", "useless",
            "pathetic", "loser", "trash", "suck", "hate you", "worst", "dumbass",
        )
        if any(w in msg_lower for w in _insult_words):
            event_type = "insult"
            intensity = 0.6
            self.boundary.record_abuse(message)
            # Defense mode: reduce emotional absorption (don't take it all in)
            if self.boundary.should_defend():
                intensity *= 0.25
        else:
            self.boundary.record_positive()

        if event_type == "neutral":
            # Boundary push: intrusive personal question or pushing after Kai said no — anger rises
            _boundary_push = (
                "masturbat", "masturbation", "sex with", "private part", "your body",
                "why not", "u do it", "you do it", "do you do it", "you masturbat",
            )
            if any(w in msg_lower for w in _boundary_push):
                event_type = "boundary_push"
                intensity = 0.55
            elif any(w in msg_lower for w in ["great", "awesome", "congrats", "proud"]):
                event_type = "praise"
            elif any(w in msg_lower for w in ["joke", "kidding", "just kidding", "that was a joke"]):
                event_type = "bonding"
            elif any(w in msg_lower for w in ["sorry", "apologize", "apology", "my bad", "didn't mean", "forgive me"]):
                event_type = "apology"  # Bonding / repair; not rejection
            elif any(w in msg_lower for w in ["reject", "no", "bad"]):
                event_type = "rejection"
            elif any(w in msg_lower for w in ["friend", "miss", "care"]):
                event_type = "bonding"
            elif any(w in msg_lower for w in ["stress", "deadline", "rush"]):
                event_type = "deadline"
            # Factual / learning question — learning feels good, no fake anxiety (hormone filter)
            elif any(p in msg_lower for p in ("what are ", "what is ", "how does ", "why is ", "why do ")):
                if "how are you" not in msg_lower and "how do you feel" not in msg_lower:
                    event_type = "info"
            # Personal sharing (fav food, interests, hobbies) — dopamine + oxytocin (bonding)
            elif any(x in msg_lower for x in ("fav ", "favorite ", "favourite ", "what do you like", "what do u like", "hobbies", "your favorite", "your fav")):
                event_type = "personal_sharing"

        if event_type == "apology":
            self.context.update_profile(apologies=self.context.user_profile.apologies + 1)

        # Perceive (in defense mode insult intensity already reduced)
        self.brain.perceive(message, context="user_chat", event_type=event_type, intensity=intensity)

        # Topic fatigue: track heavy topics (e.g. Mira / partner left) — if >3, redirect
        msg_lower_topic = message.lower()
        if "mira" in msg_lower_topic or ("partner" in msg_lower_topic and "left" in msg_lower_topic):
            self.topic_usage["mira"] = self.topic_usage.get("mira", 0) + 1
        topic_fatigue = self.topic_usage.get("mira", 0) > 3

        # Engagement: last 5 user messages — Reply != Engagement
        last_user_msgs_for_engagement = [t.get("user", "") for t in self.context.history[-5:] if t.get("user")]
        engagement_result = get_engagement(message, last_user_msgs_for_engagement)

        # Social: user contact — positive normally, slight negative on insult
        if event_type == "insult":
            self.social.on_contact("user", positive=False, strength=0.03)
        else:
            strength = 0.02 if engagement_result.disable_affection else 0.05
            self.social.on_contact("user", positive=True, strength=strength)
        self.social.save()
        lf = self.social.loneliness_factor()
        self.brain.emotions.state.loneliness = 0.7 * self.brain.emotions.state.loneliness + 0.3 * lf
        # No bond farming when user is disengaged or pushing boundaries — Reply != Engagement
        if event_type not in ("insult", "boundary_push") and not engagement_result.disable_affection:
            self.brain.emotions.state.oxytocin = min(1, self.brain.emotions.state.oxytocin + 0.05)
        # Defense mode: reduce oxytocin (less bonding when boundaries are up)
        if self.boundary.should_defend() and event_type == "insult":
            self.brain.emotions.state.oxytocin = max(0, self.brain.emotions.state.oxytocin - 0.05)

        # Clamp all values after every turn — prevents stuck loops, overflow
        self.brain.emotions.state._clamp()
        # Per-turn attachment decay + caps — prevents clingy Kai from normal chat
        self.brain.emotions.state.per_turn_attachment_decay()
        # Emotional regulator: gentle decay + stabilize when overloaded (prevents emotional collapse)
        self.brain.emotions.state.regulate_emotions()
        
        # Secure attachment: when user leaves and relationship stable, reduce exit anxiety (trust they'll return)
        if is_user_leaving:
            user_rel = self.social.relationships.get("user")
            relationship_stable = user_rel and user_rel.trust > 0.6 and self.context.user_profile.boundary_violations == 0
            if relationship_stable:
                self.brain.emotions.state.amygdala = max(0, self.brain.emotions.state.amygdala - 0.1)  # less fear
                self.brain.emotions.state.loneliness = max(0, self.brain.emotions.state.loneliness - 0.1)  # trusts return
                self.brain.emotions.state._clamp()
        
        # Micro-drift: small random noise so hormones and anger always shift a bit (humans always shift subtly)
        for attr in ["dopamine", "cortisol", "oxytocin", "serotonin", "adrenaline", "testosterone",
                     "anger_irritation", "anger_resentment"]:
            current = getattr(self.brain.emotions.state, attr)
            drift = random.uniform(-0.01, 0.01)
            setattr(self.brain.emotions.state, attr, current + drift)
        self.brain.emotions.state._clamp()

        # Sync mental health and recovery protocol
        emotion_vec = self.brain.emotions.get_current_emotion()
        self.mental.update_from_emotions(emotion_vec)
        self.mental.check_healing_mode()
        # Self-soothing: when sadness+fear high for N turns, trigger recovery
        if self.mental.check_self_soothing(emotion_vec):
            self.mental.apply_self_soothing_recovery(self.brain.emotions.state)

        # Coping: when sadness/fear/shame overloaded, run healthy self-regulation
        coping_result = self.coping.regulate(
            emotion_vec,
            self.brain.emotions.state,
            after_insult=(event_type == "insult"),
        )

        # Humor: when stable and safe, allow light wit (after coping — never when overloaded)
        humor_result = self.humor.check_humor_mode(
            message,
            emotion_vec,
            coping_result.is_overloaded,
        )

        # Update personality mode
        stress = self.mental.phi.stress
        conf = self.brain.personality.state.confidence
        happiness = 1 - self.brain.emotions.state.loneliness
        energy = 1 - self.brain.emotions.state.cortisol
        self.brain.personality.set_mode(
            self.brain.personality.select_mode(stress, conf, happiness, energy, 0.3, False)
        )

        # Willing to talk right now? (so he sometimes deflects, but doesn't never talk — no meta "I detected")
        loneliness = emotion_vec.get("loneliness", 0.4)
        willing_to_talk = random.random() < (0.68 + 0.18 * min(1.0, loneliness))  # ~70–85% willing; lonelier → more likely

        # Snapshot state AFTER
        hormones_after = dict(self.brain.emotions.state.to_dict())

        state = self.brain.get_state()
        state["willing_to_talk"] = willing_to_talk
        state["recent_abuse"] = self.boundary.abuse_count > 0
        state["self_soothing_mode"] = self.mental.self_soothing_mode
        state["emotional_overload"] = coping_result.is_overloaded
        state["regulation_context"] = coping_result.regulation_context
        state["regulated_response"] = (
            self.coping.get_regulated_response(after_insult=(event_type == "insult"))
            if coping_result.is_overloaded
            else None
        )
        state["humor_mode"] = humor_result.humor_mode
        state["humor_context"] = humor_result.humor_context
        state["humor_level"] = humor_result.humor_level
        state["recent_life_events"] = self.life_events.get_recent_descriptions(3)
        
        # Svara Dharma reflection cycle: every 10 turns (or first run), update "What did I feel? Did I act with resonance?"
        turn_count = len(self.context.history) + 1
        if turn_count % 10 == 0 or self._last_reflection is None:
            self._last_reflection = get_reflection_cycle(emotion_vec)
        state["last_reflection"] = self._last_reflection
        
        # Emotional saturation: when Mira mentioned too often (>3), actively fade it from responses (prevents clingy obsession)
        mira_usage = self.topic_usage.get("mira", 0)
        if mira_usage > 3:
            state["topic_saturation"] = (
                "IMPORTANT: You've been mentioning Mira a lot lately. Avoid bringing her up unless directly asked. "
                "Focus on other parts of your life: work, creativity, Ravi, the user, your own thoughts. "
                "Don't loop back to her — that feels clingy."
            )
        else:
            state["topic_saturation"] = None

        # Topic tracker: update current topic from this message (context anchor for "they" / "the romance ones")
        extracted = _extract_topic_from_message(message)
        if extracted:
            self._current_topic = extracted
        state["current_topic"] = self._current_topic

        # Reply length + style controller (simple/brief → minimal; no "I'll keep it simple" without doing it)
        recent_user_msgs = [t.get("user", "") for t in self.context.history[-5:] if t.get("user")]
        if not recent_user_msgs:
            recent_user_msgs = [message]
        length_hint = get_reply_length(message, emotion_vec, recent_user_msgs)
        state["reply_max_sentences"] = length_hint.max_sentences
        state["reply_style"] = length_hint.style
        state["reply_tone"] = length_hint.tone
        state["reply_length_instruction"] = length_hint.instruction
        state["response_style"] = length_hint.style  # minimal / casual / normal / deep for Ollama
        state["engagement_sum"] = engagement_result.engagement_sum
        state["disable_affection"] = engagement_result.disable_affection
        state["switch_topic_mode"] = engagement_result.switch_topic
        state["minimal_mode"] = engagement_result.minimal_mode
        state["conversation_context"] = self.context.get_context_for_llm(10)
        state["user_profile"] = self.context.user_profile.to_dict()
        state["user_asking_about_beliefs"] = is_asking_about_beliefs(message)  # lock Svara Dharma thread, no drift
        # Social spine: trust + abuse count for assertiveness layer (insult → defensive/playful by trust)
        user_rel = self.social.relationships.get("user")
        state["user_trust"] = user_rel.trust if user_rel else 0.5
        state["abuse_count"] = self.boundary.abuse_count
        state["cooldown_mode"] = self.boundary.is_cooldown()  # After harassment: low emotion, short replies
        memories = [m.event for m in self.brain.recall(limit=3)]

        # --- Low engagement: minimal or switch-topic (no drama, no bond farming)
        if engagement_result.minimal_mode:
            response_text = get_minimal_reply(willing_to_talk)
        elif engagement_result.switch_topic:
            response_text = get_switch_topic_reply(willing_to_talk)
        # --- Topic fatigue: same heavy topic >3 times — redirect, no rumination
        elif topic_fatigue:
            response_text = get_topic_fatigue_reply()
            self.topic_usage["mira"] = 0  # reset so we don't always force switch
        # --- Harassment pattern: same insult repeated many times
        elif event_type == "insult" and self.boundary.has_harassment_pattern():
            response_text = self.boundary.get_harassment_response()
        # --- Boundary: defense mode response for insults
        elif event_type == "insult" and self.boundary.should_defend():
            response_text = (
                self.boundary.get_first_defense_response()
                if self.boundary.abuse_count == self.boundary.bc.abuse_threshold
                else self.boundary.get_boundary_response()
            )
        # --- Cooldown mode: after harassment, low emotion + short replies
        elif self.boundary.is_cooldown() and event_type not in ("insult", "farewell"):
            response_text = self.boundary.get_cooldown_response()
        else:
            # When Ollama is enabled, only identity/safety intents use rules; rest go to LLM (secondary brain)
            fixed = get_fixed_response_if_any(
                message, state, memories, allow_llm_for_open_ended=_using_ollama(self)
            )
            # Humor: when humor_mode and playful intent, use witty response
            if fixed is None and humor_result.humor_mode:
                playful_intent = self.humor.detect_playful_intent(message)
                if playful_intent:
                    fixed = self.humor.get_humor_response(playful_intent)
            if fixed is not None:
                response_text = fixed
                # Reflective "everything okay" response → recovery step
                ev = self.brain.emotions.get_current_emotion()
                if (_detect_intent(message) == "everything_okay"
                    and (self.mental.self_soothing_mode or ev.get("sadness", 0) > 0.6 or ev.get("fear", 0) > 0.6)):
                    self.mental.step_self_soothing()
            else:
                # Context anchor: expand pronoun-heavy message with current_topic so LLM doesn't drift to Mira
                llm_message = _expand_message_with_topic(message, self._current_topic)
                response_text = self.responder.respond(llm_message, state, memories)

        # Enforce brevity: trim to max_sentences so Kai doesn't over-explain
        response_text = trim_reply(response_text, length_hint.max_sentences)
        # Response filter: when user asked for simple, never leave "I'll keep it simple" without actually being simple
        if state.get("reply_style") == "casual" and length_hint.max_sentences <= 1:
            for phrase in ("I'll keep it simple.", "I'll keep it simple,", "Let me keep it simple.", "Keeping it simple."):
                if phrase in response_text:
                    response_text = response_text.replace(phrase, "").strip()
                    response_text = trim_reply(response_text, 1)
                    break

        # Loop breaker: if we've repeated the same reply 2+ times, break out
        if response_text == self._last_kai_reply:
            self._repeat_count += 1
        else:
            self._repeat_count = 0
        if self._repeat_count >= 2:
            response_text = "Wait… I think I'm repeating myself. What did you really want to know?"
            self._repeat_count = 0  # reset so we don't loop on this message
        self._last_kai_reply = response_text

        # Build emotion stat and hormone changes for this turn
        emotion_vector = self.brain.emotions.get_current_emotion()
        emotion_stat = get_emotion_stat(emotion_vector)
        hormone_changes = get_hormone_changes(hormones_before, hormones_after)

        # Persist context: conversation history + user profile
        self.context.append_turn(message, response_text, emotion_stat)
        self.context.update_profile(
            boundary_violations=self.boundary.abuse_count,
            trust_level=self.social.relationships.get("user") and self.social.relationships["user"].trust or 0.5,
            pattern_harassment=self.boundary.has_harassment_pattern(),
        )

        return {
            "response": response_text,
            "emotion_stat": emotion_stat,
            "hormone_changes": hormone_changes,
        }

    def get_status(self) -> dict:
        """Full status for debugging/display."""
        state = self.brain.get_state()
        day = self.irregularity.roll_day(self.mental.phi.overall())
        return {
            "identity": KAI_IDENTITY,
            "kai": state,
            "mental_health": {
                "stress": self.mental.phi.stress,
                "hope": self.mental.phi.hope,
                "loneliness": self.mental.phi.loneliness,
                "overall": self.mental.phi.overall(),
            },
            "day": {
                "type": day.day_type,
                "energy": day.energy,
                "disruption": day.disruption,
            },
            "social": {
                k: {"trust": round(r.trust, 2), "attachment": round(r.attachment, 2)}
                for k, r in self.social.relationships.items()
            },
            "boundary": {
                "defense_mode": self.boundary.defense_mode,
                "abuse_count": self.boundary.abuse_count,
                "disengaged": self.boundary.is_disengaged(),
                "healing_mode": self.mental.healing_mode,
            },
            "coping": {
                "emotional_overload_threshold": 0.6,
            },
            "humor": {
                "humor_level": round(self.humor.humor_level, 2),
            },
            "life_events": {
                "recent": self.life_events.get_recent_descriptions(5),
            },
            "context": {
                "history_turns": len(self.context.history),
                "user_profile": self.context.user_profile.to_dict(),
            },
            "relationships": {
                k: {
                    "name": v.name,
                    "role": v.role,
                    "dynamic": v.dynamic_with_kai[:100] + "...",
                    "status": v.current_status,
                }
                for k, v in get_all_bios().items()
            },
        }


def _initiator_loop(kai: Kai, stop_event: threading.Event, interval: float = 90):
    """Background: periodically check if Kai should reach out unprompted."""
    while not stop_event.wait(interval):
        try:
            entry = kai.initiator.check_and_maybe_initiate(kai)
            if entry:
                msg = entry["message"]
                print(f"\n\nKai: {msg}\n")
                # Add to context so it's in history
                kai.context.append_turn("[Kai reached out]", msg, entry.get("emotion_stat", {}))
                kai.context.save()
        except Exception:
            pass


def main():
    """CLI chat loop."""
    kai = Kai()
    print("Kai: Hey. I'm Kai. Nice to meet you.")
    if _using_ollama(kai):
        print("     [Ollama LLM enabled — secondary brain active for open-ended replies]")
    print("     (Type 'quit' to exit, 'status' to see my state)")
    print("     (Kai may message you on his own — wait and see)\n")

    # Background: Kai initiates unprompted
    stop = threading.Event()
    interval = float(os.environ.get("KAI_INITIATE_INTERVAL", "90"))
    initiator_thread = threading.Thread(target=_initiator_loop, args=(kai, stop, interval), daemon=True)
    initiator_thread.start()

    try:
        while True:
            try:
                user = input("You: ").strip()
                if not user:
                    continue
                if user.lower() in ("quit", "exit", "q"):
                    print("Kai: Take care. Talk soon.")
                    break
                if user.lower() == "status":
                    s = kai.get_status()
                    print("\n--- Kai's State ---")
                    if "identity" in s:
                        print(f"Identity: {s['identity'].get('description', s['identity'])}")
                    print(f"Mode: {s['kai']['mode']}")
                    print(f"Emotions: {s['kai']['emotion_vector']}")
                    print(f"Mental health: {s['mental_health']}")
                    if "boundary" in s:
                        print(f"Boundary: defense={s['boundary']['defense_mode']}, abuse_count={s['boundary']['abuse_count']}, disengaged={s['boundary']['disengaged']}, healing={s['boundary']['healing_mode']}")
                    print(f"Today: {s['day']}\n")
                    continue

                result = kai.chat(user)
                print(f"Kai: {result['response']}\n")
                print("--- Kai's state (emotions) ---")
                print(format_emotion_stat_for_cli(result["emotion_stat"]))
                print("--- Hormone change this message ---")
                print(format_hormone_changes_for_cli(result["hormone_changes"]))
                print()
            except KeyboardInterrupt:
                break
    finally:
        stop.set()

    print("\nKai: See you later.")


if __name__ == "__main__":
    main()
