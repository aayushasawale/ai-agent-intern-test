from pathlib import Path

from app.rag.loader import load_knowledge_base
from app.rag.chunker import chunk_documents
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.agent.support_agent import SupportAgent


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"
CHROMA_DB = PROJECT_ROOT / "chroma_db"


def build_agent():
    """Build the support agent using the real knowledge base."""

    print("Loading knowledge base...")

    documents = load_knowledge_base(KNOWLEDGE_BASE)
    chunks = chunk_documents(documents)

    print(f"Loaded {len(documents)} documents.")
    print(f"Created {len(chunks)} document chunks.")

    store = VectorStore(
        persist_directory=CHROMA_DB
    )

    # Add the knowledge-base chunks to the vector store.
    store.add_chunks(chunks)

    retriever = Retriever(store)

    return SupportAgent(retriever)


def main():
    print("=" * 60)
    print("        AI SUPPORT AGENT — DEMO")
    print("=" * 60)

    agent = build_agent()

    print("\nAgent ready.")
    print("Type your question below.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            print("\nDemo ended.")
            break

        if not question:
            continue

        try:
            response = agent.answer(question)

            print("\nAgent:")

            if isinstance(response, dict):
                answer = response.get("answer")

                if hasattr(answer, "answer"):
                    print(answer.answer)
                else:
                    print(answer)
            else:
                print(response)

            print()

        except Exception as exc:
            print(f"\nAgent error: {exc}\n")


if __name__ == "__main__":
    main()