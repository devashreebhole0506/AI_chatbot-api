import os
from io import BytesIO
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

load_dotenv()
KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=KEY) if KEY and KEY != "replace_me" else None
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_FILE_BYTES = max(1, int(os.getenv("MAX_FILE_MB", "10"))) * 1024 * 1024
CHUNK_CHARS = max(1000, int(os.getenv("CHUNK_CHARS", "10000")))
app = FastAPI(title="Document Summarization Service")

def extract_text(filename: str, data: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    try:
        if suffix == "txt":
            return data.decode("utf-8", errors="replace")
        if suffix == "pdf":
            reader = PdfReader(BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if suffix == "docx":
            doc = Document(BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse document: {type(exc).__name__}")
    raise HTTPException(status_code=415, detail="Supported file types: .txt, .pdf, .docx")

def split_chunks(text: str):
    # Character-based chunking is simple and predictable; overlap preserves local context.
    overlap = 500
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + CHUNK_CHARS)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks

def summarize_chunk(text: str, style: str) -> str:
    style_prompts = {
        "concise":"Write a concise summary with only the main points.",
        "bullets":"Summarize as clear bullet points.",
        "executive":"Write an executive summary covering purpose, key findings, risks, and recommended actions.",
        "detailed":"Write a detailed structured summary with headings and important supporting details."
    }
    result = client.chat.completions.create(
        model=MODEL, temperature=0.2,
        messages=[
            {"role":"system","content":"Summarize only the supplied source. Do not invent facts."},
            {"role":"user","content":f"{style_prompts[style]}\n\nSOURCE:\n{text}"}
        ]
    )
    return result.choices[0].message.content or ""

@app.get("/health")
def health():
    return {"status":"ok", "llm_configured":client is not None}

@app.post("/summarize")
async def summarize(file: UploadFile = File(...), style: str = Form("concise")):
    if client is None:
        raise HTTPException(status_code=503, detail="Set OPENAI_API_KEY in .env")
    if style not in {"concise", "bullets", "executive", "detailed"}:
        raise HTTPException(status_code=422, detail="style must be concise, bullets, executive, or detailed")
    data = await file.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_BYTES // (1024*1024)} MB limit")
    text = extract_text(file.filename or "", data).strip()
    if not text:
        raise HTTPException(status_code=422, detail="No extractable text found in document")
    chunks = split_chunks(text)
    try:
        partials = [summarize_chunk(chunk, style) for chunk in chunks]
        if len(partials) == 1:
            final_summary = partials[0]
        else:
            final_summary = summarize_chunk("\n\n".join(partials), style)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Summarization provider failed: {type(exc).__name__}")
    return {"filename":file.filename, "style":style, "characters":len(text),
            "chunks_processed":len(chunks), "summary":final_summary}

