# L1-03 — n8n Workflow with LLM Integration

## Import and configure
1. Start n8n and choose **Import from File**; select `workflow.json`.
2. Configure the environment variable `OPENAI_API_KEY` in the n8n runtime. For Docker, pass it via `-e OPENAI_API_KEY=...`; never hard-code the secret into the workflow.
3. Activate the workflow and copy the production webhook URL.

## Test
Send a POST request:
```bash
curl -X POST http://localhost:5678/webhook/os3-llm \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain RAG in two sentences"}'
```
The flow is Webhook Trigger → Call OpenAI (HTTP Request) → Normalize Response (Code). If your n8n version changes HTTP Request node fields, open the node and verify its raw JSON body configuration. Keep the workflow inactive while testing with the test webhook URL if preferred.
