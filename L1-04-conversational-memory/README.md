# L1-04 — Conversational Memory Management

Uses a rolling summary for older context and a bounded buffer for recent turns. The summary is updated every configured number of turns or when the buffer reaches its limit.

Run with the same virtual-environment steps as other projects, then:
```powershell
pip install -r requirements.txt
copy .env.example .env
# Add API key
python memory_chat.py
```

Trade-off: the buffer is exact but consumes context tokens; the summary is compact but may omit details. This demo stores memory in process RAM only, so it resets when restarted. For persistence, store summaries and messages in a database keyed by authenticated user/session.
