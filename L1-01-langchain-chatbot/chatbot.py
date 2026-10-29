import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "Set OPENAI_API_KEY in your .env file before starting."
    )

SYSTEM_PROMPT = """You are a helpful, accurate assistant.
Answer clearly and concisely. If you do not know something, say so.
Use prior conversation only when it is relevant to the current question."""

class Chatbot:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "replace_me":
            raise RuntimeError("Set OPENAI_API_KEY in your .env file before starting.")
        self.model = ChatOpenAI(
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            api_key=api_key,
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{question}"),
        ])
        self.history = []

    def ask(self, question: str) -> str:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        chain = self.prompt | self.model
        response = chain.invoke({"history": self.history, "question": question})
        answer = response.content if isinstance(response.content, str) else str(response.content)
        self.history.extend([HumanMessage(content=question), AIMessage(content=answer)])
        # Bound memory to the most recent 20 messages (10 turns).
        self.history = self.history[-20:]
        return answer

def main():
    bot = Chatbot()
    print("OS3 LangChain Chatbot. Type /exit to quit.")
    while True:
        try:
            question = input("You: ").strip()
            if question.lower() in {"/exit", "/quit"}:
                break
            print("Assistant:", bot.ask(question))
        except (ValueError, RuntimeError) as exc:
            print(f"Error: {exc}")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as exc:
            print(f"LLM request failed: {exc}")

if __name__ == "__main__":
    main()
