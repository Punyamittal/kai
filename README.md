
# 🤖 Kai — Emotion-Aware AI Companion System

Kai is an experimental AI agent designed to simulate emotional continuity,
social relationships, adaptive personality, and human-like imperfection.

It combines:
- Emotion + hormone simulation
- Memory systems
- Boundary defense
- Relationship modeling
- Optional LLM reasoning
- Long-term personality evolution

The goal is to explore emotionally coherent artificial characters.

---

# 📐 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────────────┐
│ KAI SYSTEM                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ User Input                                                              │
│ ↓                                                                       │
│ ┌─────────────┐                                                         │                                                       
│ │ main.py │ ← Orchestrator (entry point)                                │
│ └──────┬──────┘                                                         │
│                             ↓                                           │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ PROCESSING PIPELINE                                                 │ │
│ │                                                                     │ │
│ │ 1. Event Detection → insult/praise/apology/info/etc.                │ │
│ │ 2. Intent Detection → greeting/question/farewell/etc.               │ │
│ │ 3. Topic Tracker → anchors pronouns to current topic                │ │
│ │ 4. Style Controller → simple/casual/normal/deep                     │ │
│ │ 5. Boundary Check → defense/cooldown/disengage                      │ │
│ │ 6. Response Router → rule-based OR Ollama LLM                       │ │
│ │ 7. Loop Breaker → prevents repetition                               │ │
│ │ 8. Emotion Regulator → enforces emotional floor                     │ │
│ │                                                                     │ │
│ └──────────────────────────────────────────────────────────────────┘    │
│                                       ↓                                 │
│                                 Response + Emotion Stats                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```
yaml
Copy code

---

# 📂 Module Structure

## 1️⃣ Core Layer (`kai/core/`)

| Module | Purpose |
|--------|----------|
| brain.py | Central cognitive controller |
| emotions.py | Hormone simulation + regulation |
| memory.py | STM/LTM + emotional recall |
| emotion_display.py | CLI emotion formatter |

---

## 2️⃣ Systems Layer (`kai/systems/`)

| Module | Purpose |
|--------|----------|
| boundary.py | Abuse detection + defense |
| social_world.py | Relationships |
| context_manager.py | Session persistence |
| coping.py | Self-regulation |
| humor.py | Wit activation |
| engagement.py | User engagement |
| reply_length.py | Style control |
| mental_health.py | Stress/hope/loneliness |
| life_events.py | Random life simulation |
| initiator.py | Proactive messages |
| creativity.py | Creative modes |
| moral.py | Ethical reasoning |

---

## 3️⃣ LLM Layer (`kai/llm/`)

| Module | Purpose |
|--------|----------|
| prompt.py | Rule-based responder |
| ollama_backend.py | Local LLM |
| transformers_backend.py | Transformers backend |

---

## 4️⃣ Data Layer (`kai/data/`)

| Module | Purpose |
|--------|----------|
| relationships.py | Character bios |
| persona.py | Canonical facts |
| philosophy.py | Svara Dharma |
| persona.json | Static identity |

---

## 5️⃣ Life Layer (`kai/life/`)

| Module | Purpose |
|--------|----------|
| daily.py | Daily simulation |
| irregularity.py | Random day types |

---

## 6️⃣ Personality Layer (`kai/personality/`)

| Module | Purpose |
|--------|----------|
| engine.py | Personality modes |

Modes:
- Nobita → Sensitive
- Shinchan → Playful
- Bheem → Strong

---

# 🔄 Chat Workflow (Per Message)

Example Input:
User: "bastard"

yaml
Copy code

---

## Step 1 — Event Detection

msg → detect insult → event_type="insult"
boundary.record_abuse()

yaml
Copy code

---

## Step 2 — Emotion Update

brain.perceive()
→ emotions.process_event("insult", 0.6)

cortisol ↑
amygdala ↑
anger ↑
testosterone ↓

yaml
Copy code

---

## Step 3 — Emotion Regulator

emotions.regulate()

• decay × 0.95
• anger cooldown
• sadness recovery
• enforce emotion floor

yaml
Copy code

---

## Step 4 — Intent Detection

_detect_intent("bastard") → "insult"
Protected intent

yaml
Copy code

---

## Step 5 — Boundary Check

if abuse_count >= threshold:
defense_response
if cooldown:
disengage

yaml
Copy code

---

## Step 6 — Response Generation

### A) Rule-Based

"Hey, that wasn't cool."
"Bruh 😅 rude."

shell
Copy code

### B) LLM

build_system_prompt()
→ Ollama call

yaml
Copy code

---

## Step 7 — Loop Breaker

if repeated 3x:
break loop
trim length

yaml
Copy code

---

## Step 8 — Persist + Return

context.append()
return response + emotions

yaml
Copy code

---

# 🌊 Key Data Flows

## Emotion Flow

Event
↓
process_event()
↓
Hormones
↓
Emotion Vector
↓
Memory Tagging
↓
Tone Control

Copy code
{ joy, sadness, anger, fear, love, hope, loneliness }

yaml
Copy code

---

## Response Routing

# 🔀 Response Routing Logic
```
User Message
↓
_detect_intent()
↓
┌───────────────┬───────────────┐
│ Protected     │ Open-Ended    │
│ Intent        │ Intent        │
├───────────────┼───────────────┤
│ Rule-Based    │ LLM           │
│ Engine        │ (Ollama)      │
└───────────────┴───────────────┘
```
yaml
Copy code

---

# 🛡️ Boundary Escalation

Insult 1 → Assertive response
Insult 2 → Warning
Insult 3 → Defense Mode
Insult 4 → Cooldown
Insult 5 → Disengage

Positive streak → Recovery

makefile
Copy code

---

# ⚙️ Configuration

## Identity Anchor (`config.py`)

```python
KAI_IDENTITY = {
    "name": "Kai",
    "location": "Toronto",
    "partner": "Mira",
    "friend": "Ravi",
    "career": "writer and freelancer",
    "mission": "tell stories that matter",
    "values": ["respect", "growth", "honesty", "autonomy"]
}
Emotion Floor (config.py)
python
Copy code
EMOTION_FLOOR = {
    "hope": 0.25,
    "joy": 0.15,
    "dopamine": 0.2,
    "serotonin": 0.25,
    "testosterone": 0.2
}
Prevents emotional collapse.
```
▶️ Running Kai
Without LLM (Rule-Based Only)
bash
Copy code
python -m kai.main
With Ollama (Secondary Brain)
powershell
Copy code
$env:KAI_USE_LLM="ollama"
python -m kai.main
🧠 System Architecture Overview
css

```md
# 🧠 System Architecture Overview

┌──────────┐
│ Input    │
└────┬─────┘
↓
┌──────────┐
│ Brain    │
└────┬─────┘
     ↓
┌──────────┐
│ Emotion  │
└────┬─────┘
     ↓
┌──────────┐
│ Memory   │
└────┬─────┘
     ↓
┌──────────┐
│ Boundary │
└────┬─────┘
     ↓
┌──────────┐
│ Response │
└──────────┘
```
🧬 What Makes Kai Different
Kai maintains:

✅ Emotional Continuity
✅ Persistent Memory
✅ Boundaries & Self-Respect
✅ Autonomous Identity
✅ Personality Modes
✅ Moral Reasoning
✅ Irregular Life Simulation

Unlike standard chatbots, Kai is not stateless.

He evolves.

🚀 Vision
This architecture enables:

Digital characters

Emotional agents

Virtual companions

Research on AI psychology

Long-term AI identity

Future:

Web UI

Animated avatar

Multi-agent homes

Voice

RL adaptation

Emotion dashboard

👨‍💻 Author
Punya Mittal
B.Tech CSE (AI) — VIT

GitHub: https://github.com/Punyamittal
LinkedIn: https://www.linkedin.com/in/punya-mittal-a1122520b

📜 License
MIT License

Free to use with attribution.

yaml
Copy code

---

If you want, next I can help you make:

✅ Internship Pitch  
✅ OpenAI Email  
✅ Research Paper Format  
✅ Demo Video Script  

Just say the word 😄🔥
