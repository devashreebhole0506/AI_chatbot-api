# L1-01 — LangChain-Based Chatbot

## What it demonstrates
LangChain prompt templates, an LLM integration, multi-turn conversation history, a clear system prompt, environment configuration, and error handling.

## Run
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add OPENAI_API_KEY
python chatbot.py
```
Type `/exit` to stop. History is kept in memory for the current process and is limited to the latest 20 messages.
