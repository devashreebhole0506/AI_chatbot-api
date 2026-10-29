import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
if not key or key == "replace_me":
    raise SystemExit("Set OPENAI_API_KEY in .env")
client = OpenAI(api_key=key)
MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
MAX_BUFFER = max(2, int(os.getenv("MAX_BUFFER_MESSAGES", "8")))
SUMMARY_EVERY = max(1, int(os.getenv("SUMMARY_EVERY_TURNS", "4")))

class ConversationMemory:
    """Keeps a rolling summary plus a short recent-message buffer."""
    def __init__(self):
        self.summary = ""
        self.buffer = []
        self.turns_since_summary = 0

    def add(self, role, content):
        self.buffer.append({"role": role, "content": content})
        self.buffer = self.buffer[-MAX_BUFFER:]

    def update_summary(self):
        if not self.buffer:
            return
        prompt = (
            "Update the conversation memory summary. Preserve stable user preferences, "
            "goals, important facts, decisions, and unresolved questions. Do not invent facts.\\n"
            f"Existing summary:\\n{self.summary or '(empty)'}\\n"
            f"Recent conversation:\\n{self.buffer}"
        )
        result = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":"Create a compact factual memory summary."},
                      {"role":"user","content":prompt}],
            temperature=0,
        )
        self.summary = result.choices[0].message.content or self.summary
        self.turns_since_summary = 0

memory = ConversationMemory()

def ask(text):
    text = text.strip()
    if not text:
        raise ValueError("Message cannot be empty")
    messages = [{"role":"system","content":
        "You are a helpful assistant. Use the supplied memory only when relevant. "
        "If a fact is absent from memory, do not pretend to remember it.\\n"
        f"Long-term summary: {memory.summary or '(none yet)'}"}]
    messages += memory.buffer
    messages.append({"role":"user","content":text})
    result = client.chat.completions.create(model=MODEL, messages=messages, temperature=0.3)
    answer = result.choices[0].message.content or ""
    memory.add("user", text)
    memory.add("assistant", answer)
    memory.turns_since_summary += 1
    if memory.turns_since_summary >= SUMMARY_EVERY or len(memory.buffer) >= MAX_BUFFER:
        try:
            memory.update_summary()
        except Exception as exc:
            print(f"[warning] Summary update failed; keeping recent buffer: {exc}")
    return answer

if __name__ == "__main__":
    print("Memory chat. /exit to quit.")
    while True:
        q = input("You: ")
        if q.strip().lower() == "/exit":
            break
        try:
            print("Assistant:", ask(q))
        except Exception as exc:
            print("Error:", exc)
