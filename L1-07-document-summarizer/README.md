# L1-07 — Document Summarization Service

## Run
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Add OPENAI_API_KEY
uvicorn app:app --reload
```
Open http://127.0.0.1:8000/docs and try `POST /summarize`. Upload a `.pdf`, `.txt`, or `.docx` file and choose one style: `concise`, `bullets`, `executive`, or `detailed`.

Implementation includes file size validation, extraction, overlapping chunking, map-reduce summarization, configurable styles, and HTTP error responses. Scanned PDFs may need OCR, which this version does not include. Character-based chunks are a simple baseline; a production system should use token-aware chunking and async/background processing for large files.
