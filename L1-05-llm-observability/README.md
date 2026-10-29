# L1-05 — LLM Observability and Logging

Run:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Add OPENAI_API_KEY
uvicorn app:app --reload
```
POST `/generate` with `{"prompt":"Explain embeddings briefly"}`. Logs are newline-delimited JSON at `logs/llm.jsonl`; response includes latency and token usage. Provider token counts are used when returned; otherwise the estimate is explicitly labeled approximate. Raw prompt/response content is not logged by default to reduce privacy risk.
