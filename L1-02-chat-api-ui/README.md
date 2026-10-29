# L1-02 — Chat API and Web UI

## Run
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Add OPENAI_API_KEY to .env
uvicorn app:app --reload
```
Open http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs.
- `GET /health`: health/configuration check.
- `POST /chat`: JSON body `{"session_id": null, "message": "Hello"}`.
Session history is persisted as JSON under `data/`. This is suitable for a local demo; use a database and authenticated session ownership for production.
