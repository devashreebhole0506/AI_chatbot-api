# L1-06 — Secure and Configurable LLM Service

Run:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```
Set both `OPENAI_API_KEY` and a strong random `SERVICE_API_KEY`, then run:
```powershell
uvicorn app:app --reload
```
Test:
```bash
curl -X POST http://127.0.0.1:8000/generate -H "Content-Type: application/json" -H "X-API-Key: YOUR_SERVICE_API_KEY" -d "{\"prompt\":\"Explain API security\",\"temperature\":0.2}"
```
The app validates input, protects the generation endpoint with an API key, and rate-limits by client IP. The rate limiter is in-memory and suitable only for a single-process demo. Use a gateway or Redis-backed limiter, HTTPS, secret manager, and stronger identity/authorization for production.
