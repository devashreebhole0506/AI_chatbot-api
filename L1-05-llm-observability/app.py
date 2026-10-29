import json, logging, os, time, uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()
log_path = Path(os.getenv("LOG_FILE", "logs/llm.jsonl"))
log_path.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("llm_observability")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_path, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=key) if key and key != "replace_me" else None
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
app = FastAPI(title="LLM Observability Demo")

class Request(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)

def approximate_tokens(text: str) -> int:
    # Rough estimate only: English text averages around 4 characters per token.
    return max(1, len(text) // 4) if text else 0

@app.get("/health")
def health():
    return {"status":"ok", "llm_configured": client is not None}

@app.post("/generate")
def generate(body: Request):
    if client is None:
        raise HTTPException(status_code=503, detail="Set OPENAI_API_KEY")
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    status = "success"
    try:
        result = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":body.prompt}],
            temperature=0.2,
        )
        output = result.choices[0].message.content or ""
        usage = result.usage
        prompt_tokens = usage.prompt_tokens if usage else approximate_tokens(body.prompt)
        completion_tokens = usage.completion_tokens if usage else approximate_tokens(output)
        return {"request_id":request_id, "response":output,
                "latency_ms":round((time.perf_counter()-start)*1000, 2),
                "prompt_tokens":prompt_tokens, "completion_tokens":completion_tokens,
                "token_source":"provider" if usage else "approximate"}
    except Exception as exc:
        status = "error"
        raise HTTPException(status_code=502, detail=f"LLM provider request failed: {type(exc).__name__}")
    finally:
        # Do not log raw prompts/responses by default: they may contain sensitive data.
        logger.info(json.dumps({"request_id":request_id, "model":MODEL,
            "latency_ms":round((time.perf_counter()-start)*1000,2),
            "prompt_chars":len(body.prompt), "status":status,
            "timestamp":time.time()}))
