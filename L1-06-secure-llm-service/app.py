import os, time
from collections import defaultdict, deque
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request as FastAPIRequest
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_API_KEY", "")
PROVIDER_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=PROVIDER_KEY) if PROVIDER_KEY and PROVIDER_KEY != "replace_me" else None
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
LIMIT = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "10")))
WINDOW = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
hits = defaultdict(deque)
app = FastAPI(title="Secure Configurable LLM Service")

class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)

@app.get("/health")
def health():
    return {"status":"ok", "provider_configured":client is not None}

@app.middleware("http")
async def rate_limit(request: FastAPIRequest, call_next):
    if request.url.path in {"/health", "/docs", "/openapi.json"}:
        return await call_next(request)
    # Demo only: in-memory IP-based limit. Use Redis/API gateway in multi-worker production.
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    queue = hits[ip]
    while queue and now - queue[0] > WINDOW:
        queue.popleft()
    if len(queue) >= LIMIT:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=429, content={"detail":"Rate limit exceeded"})
    queue.append(now)
    return await call_next(request)

@app.post("/generate")
def generate(body: GenerateRequest, x_api_key: str | None = Header(default=None)):
    if not SERVICE_KEY or SERVICE_KEY == "change_this_to_a_long_random_secret":
        raise HTTPException(status_code=503, detail="Configure a strong SERVICE_API_KEY in .env")
    if x_api_key is None or not __import__("hmac").compare_digest(x_api_key, SERVICE_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    if client is None:
        raise HTTPException(status_code=503, detail="Configure OPENAI_API_KEY in .env")
    try:
        result = client.chat.completions.create(
            model=MODEL, temperature=body.temperature,
            messages=[{"role":"system","content":"You are a helpful assistant."},
                      {"role":"user","content":body.prompt}],
        )
        return {"response":result.choices[0].message.content or "", "model":MODEL}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider request failed: {type(exc).__name__}")
