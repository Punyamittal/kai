# Kai — LLM Brain & Memory Setup Guide

What to download and install for the **first real LLM brain** and **vector memory**.

---

## Current State (No Extra Downloads)

Right now Kai runs with:
- **Brain**: Rule-based responder (no LLM)
- **Memory**: JSON files (`kai_data/memory/`)

Everything works with just:
```bash
pip install python-dotenv pydantic fastapi uvicorn numpy
```

---

## Option 1: Add LLM Brain (Recommended — Ollama)

Easiest way to give Kai real reasoning. No API keys, runs locally.

### Step 1 — Install Ollama
1. Download: https://ollama.com/download  
2. Install (Windows/Mac/Linux)  
3. Open terminal: `ollama --version` to confirm

### Step 2 — Pull a Model
```bash
# Small & fast (~2GB download)
ollama pull llama3.2:3b

# Or better quality (~4GB)
ollama pull mistral

# Or tiny for weak PCs (~1GB)
ollama pull phi3:mini
```

### Step 3 — Install Python Package
```bash
pip install ollama
```

### Step 4 — Run Kai with Ollama
```bash
# Windows PowerShell
$env:KAI_USE_LLM="ollama"
python -m kai.main

# Or use a different model
$env:KAI_USE_LLM="ollama"
$env:KAI_OLLAMA_MODEL="mistral"
python -m kai.main
```

```bash
# Linux/Mac
KAI_USE_LLM=ollama python -m kai.main
```

First run: model loads; later runs are fast.

**Approx. download size**: 1–4 GB depending on model

---

## Option 2: Add LLM Brain (HuggingFace Transformers)

Runs fully in Python. Downloads model on first run.

### Install
```bash
pip install transformers torch accelerate
```

### Models (auto-downloaded on first use)
| Model | Size | RAM | Quality |
|-------|------|-----|---------|
| `microsoft/DialoGPT-small` | ~500MB | 4GB | Basic chat |
| `microsoft/phi-2` | ~5GB | 8GB | Better |
| `TinyLlama/TinyLlama-1.1B` | ~2GB | 6GB | Good balance |

### Use
- Kai has `kai/llm/transformers_backend.py`; switch `main.py` to use it.
- First run downloads the model; after that it uses cache.

---

## Option 3: Add Vector Memory (ChromaDB + Embeddings)

For **semantic recall** (find memories by meaning, not just keywords).

### Install
```bash
pip install chromadb sentence-transformers
```

### Downloads (first run)
- `sentence-transformers` pulls a model (~100–400MB), e.g. `all-MiniLM-L6-v2`
- Stored in `~/.cache/huggingface/`

### Use
- Replace JSON memory with ChromaDB-backed memory in `kai/core/memory.py`
- Enables: "Recall things we talked about work" → finds relevant past conversations

---

## Minimal Setup for "First LLM Brain + Memory"

**Recommended combo for getting started:**

| Component | Choice | Download |
|-----------|--------|----------|
| **LLM Brain** | Ollama + `llama3.2:3b` | Ollama app + ~2GB model |
| **Memory** | Keep JSON (current) | None |

**Commands:**
```bash
# 1. Install Ollama from ollama.com

# 2. Pull model
ollama pull llama3.2:3b

# 3. Install Python deps
pip install ollama

# 4. Run Kai (after Ollama backend is wired in)
python -m kai.main
```

**With vector memory:**
```bash
pip install chromadb sentence-transformers
# First run will download ~400MB for embeddings
```

---

## Summary Table

| What | Required? | Download Size |
|------|-----------|---------------|
| Core (pydantic, fastapi, etc.) | Yes | ~50MB |
| Ollama (LLM) | Optional | App + 1–4GB model |
| Transformers (LLM) | Optional | 0.5–5GB model |
| ChromaDB | Optional | ~10MB |
| sentence-transformers | Optional | ~400MB |

**Minimum to run Kai today**: Core packages only (~50MB)  
**For real LLM**: Add Ollama + one model (~2GB)  
**For semantic memory**: Add chromadb + sentence-transformers (~400MB)
