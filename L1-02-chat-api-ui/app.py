import json, os, time, uuid
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()
app = FastAPI(title="OS3 Chat API", version="1.0.0")
DATA_DIR = Path(os.getenv("CHAT_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=4000)

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    history: list[dict]

def path_for(session_id: str) -> Path:
    # UUID-only session identifiers avoid path traversal.
    try:
        safe_id = str(uuid.UUID(session_id))
    except Exception:
        raise HTTPException(status_code=400, detail="session_id must be a UUID")
    return DATA_DIR / f"{safe_id}.json"

def load_history(session_id: str):
    path = path_for(session_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored session history is corrupt")

def save_history(session_id: str, history):
    path_for(session_id).write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": client is not None}

@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    if client is None:
        raise HTTPException(status_code=503, detail="LLM not configured; set OPENAI_API_KEY")
    session_id = body.session_id or str(uuid.uuid4())
    history = load_history(session_id)
    history.append({"role": "user", "content": body.message})
    try:
        result = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "You are a helpful assistant."}] + history[-20:],
            temperature=0.3,
        )
        reply = result.choices[0].message.content or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider request failed: {type(exc).__name__}")
    history.append({"role": "assistant", "content": reply})
    history = history[-40:]
    save_history(session_id, history)
    return ChatResponse(session_id=session_id, reply=reply, history=history)

@app.get("/")
def index():
    return FileResponse("static/index.html")
