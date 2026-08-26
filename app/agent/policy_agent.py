from dataclasses import dataclass

from app.rag.retriever import Retriever
from app.rag.ranking import rank_chunks
from app.rag.evidence import analyze_evidence


@dataclass
class PolicyResponse:
    answer: str
    sources: list[str]
    handoff: bool = False
    conflict_detected: bool = False


class PolicyAgent:
    """
    Deterministic policy/RAG layer.

    Responsibilities:
    - retrieve relevant knowledge-base chunks
    - rank them
    - analyze evidence
    - detect conflicts
    - provide source references
    - avoid unsupported answers

    The LLM will be connected later.
    """

    def __init__(
        self,
        retriever: Retriever,
    ):
        self.retriever = retriever

    def answer(
        self,
        query: str,
        n_results: int = 8,
    ) -> PolicyResponse:

        retrieved = self.retriever.retrieve(
            query=query,
            n_results=n_results,
        )

        if not retrieved:
            return PolicyResponse(
                answer=(
                    "I don't have enough information "
                    "in the knowledge base to answer that reliably."
                ),
                sources=[],
                handoff=True,
            )

        ranked = rank_chunks(
            retrieved
        )

        evidence = analyze_evidence(
            ranked
        )

        sources = self._build_sources(
            evidence.chunks
        )

        if evidence.conflict_detected:
            return PolicyResponse(
                answer=(
                    "I found conflicting guidance in "
                    "two active official sources. I should "
                    "not choose one silently. Human confirmation "
                    "is recommended before giving a definitive answer."
                ),
                sources=sources,
                handoff=True,
                conflict_detected=True,
            )

        if not evidence.chunks:
            return PolicyResponse(
                answer=(
                    "I don't have enough reliable evidence "
                    "to answer that question."
                ),
                sources=sources,
                handoff=True,
            )

        best = evidence.chunks[0]

        answer = self._build_grounded_answer(
            best.text,
            best.source_file,
            best.heading,
        )

        return PolicyResponse(
            answer=answer,
            sources=sources,
            handoff=False,
            conflict_detected=False,
        )

    @staticmethod
    def _build_sources(
        chunks,
    ) -> list[str]:

        sources = []

        seen = set()

        for chunk in chunks:

            source = (
                f"{chunk.source_file} "
                f"— {chunk.heading}"
            )

            if source not in seen:
                sources.append(source)
                seen.add(source)

        return sources

    @staticmethod
    def _build_grounded_answer(
        text: str,
        source_file: str,
        heading: str,
    ) -> str:

        return (
            f"Based on the knowledge base, "
            f"the relevant guidance is:\n\n"
            f"{text}\n\n"
            f"Source: {source_file} — {heading}"
        )