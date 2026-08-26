from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk


@dataclass
class RankedChunk:
    chunk: RetrievedChunk
    final_score: float


def authority_bonus(chunk: RetrievedChunk) -> float:
    """
    Calculate a small ranking adjustment based on
    document authority and status.
    """

    metadata = chunk.metadata

    score = 0.0

    status = str(
        metadata.get("status", "")
    ).lower()

    authority = str(
        metadata.get("policy_authority", "")
    ).lower()

    audience = str(
        metadata.get("audience", "")
    ).lower()

    if status == "active":
        score += 0.20

    if authority == "official":
        score += 0.30

    if status in {
        "legacy",
        "superseded",
        "inactive",
    }:
        score -= 0.40

    if audience == "internal":
        score -= 0.30

    return score


def rank_chunks(
    chunks: list[RetrievedChunk],
) -> list[RankedChunk]:
    """
    Rank retrieved chunks using semantic similarity
    plus document authority.
    """

    ranked = []

    for chunk in chunks:
        score = (
            chunk.similarity_score
            + authority_bonus(chunk)
        )

        ranked.append(
            RankedChunk(
                chunk=chunk,
                final_score=score,
            )
        )

    ranked.sort(
        key=lambda item: item.final_score,
        reverse=True,
    )

    return ranked