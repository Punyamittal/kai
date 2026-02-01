# Kai — A Self-Evolving Digital Being

An autonomous digital being with emotions, memory, morality, creativity, and personality — designed to live, learn, and grow.

Inspired by Kai Hiwatari (Beyblade): independent, emotionally deep, disciplined, growing through hardship.

## Features

- **Memory System**: Short-term, long-term, conscious, subconscious (emotion-weighted)
- **Emotional Engine**: Hormones (dopamine, cortisol, oxytocin, etc.) + amygdala, hippocampus simulation
- **Personality Modes**: Nobita (sensitive), Shinchan (playful), Bheem (strong) fusion
- **Moral System**: Harm minimization, compassion override, guilt/remorse
- **Mental Health**: Trauma processing, reflection, rest mode, support network
- **Creativity**: Polymath (writing, art, music, engineering, philosophy)
- **Daily Life**: Sleep, work, social, create, rest with irregularities
- **Social World**: Relationships, trust, attachment simulation

## Quick Start

```bash
# Install
pip install -r requirements.txt

# CLI chat
python -m kai.main

# Web UI + API
uvicorn kai.api:app --reload --host 0.0.0.0 --port 8000
# Open http://localhost:8000
```

## Usage

**CLI:**
- Type messages to chat
- `status` — see Kai's emotional state, mode, day type
- `quit` — exit

**API:**
- `GET /` — Chat UI
- `POST /chat` — `{"message": "Hi"}` → `{"response": "..."}`
- `GET /status` — Full state (emotions, mode, mental health)
- `GET /health` — Health check

## Architecture

```
kai/
├── core/           # Brain, memory, emotions
├── personality/    # Traits, modes (Nobita/Shinchan/Bheem)
├── systems/        # Moral, mental health, creativity
├── life/           # Daily routine, irregularity
├── llm/            # Response (prompt-based, optional transformers)
└── api.py          # FastAPI
```

## Blueprint

See [MASTER_PROMPT.md](MASTER_PROMPT.md) for full specification.

## License

MIT
# kai
