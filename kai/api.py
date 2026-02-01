"""
Kai FastAPI - Chat and status endpoints.
"""

import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from kai.main import Kai

app = FastAPI(title="Kai API", description="Self-Evolving Digital Being")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve static chat UI
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

kai = Kai()
_initiator_stop = threading.Event()


def _api_initiator_loop():
    """Background: Kai reaches out unprompted. Runs every 90 seconds."""
    while not _initiator_stop.wait(90):
        try:
            entry = kai.initiator.check_and_maybe_initiate(kai)
            if entry:
                kai.context.append_turn("[Kai reached out]", entry["message"], entry.get("emotion_stat", {}))
                kai.context.save()
        except Exception:
            pass


@app.on_event("startup")
def start_initiator():
    t = threading.Thread(target=_api_initiator_loop, daemon=True)
    t.start()


@app.on_event("shutdown")
def stop_initiator():
    _initiator_stop.set()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    emotion_stat: dict
    hormone_changes: list


@app.get("/")
def root():
    index = Path(__file__).parent.parent / "static" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"name": "Kai", "status": "alive", "message": "Hey. I'm Kai. Nice to meet you."}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = kai.chat(req.message)
    return ChatResponse(
        response=result["response"],
        emotion_stat=result["emotion_stat"],
        hormone_changes=result["hormone_changes"],
    )


@app.get("/status")
def status():
    return kai.get_status()


@app.get("/inbox")
def inbox():
    """Kai's unprompted messages. Poll this to get messages Kai sent on his own. Returns and clears."""
    msgs = kai.initiator.get_pending()
    return {"messages": [{"message": m["message"], "emotion_stat": m.get("emotion_stat", {})} for m in msgs]}


@app.get("/relationships")
def relationships():
    """Kai's relationships — full biographies and backstories."""
    from kai.data.relationships import get_all_bios, to_dict
    return {
        k: to_dict(v) for k, v in get_all_bios().items()
    }


@app.get("/health")
def health():
    return {"ok": True}
