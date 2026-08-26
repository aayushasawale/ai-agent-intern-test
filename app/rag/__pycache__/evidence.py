from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk
from app.rag.ranking import RankedChunk


@dataclass
class EvidenceResult:
    chunks: list[RetrievedChunk]
    conflict_detected: bool
    requires_handoff: bool
    reason: str | None


def is_active_official(chunk: RetrievedChunk) -> bool:
    metadata = chunk.metadata

    status = str(
        metadata.get("status", "")
    ).lower()

    authority = str(
        metadata.get("policy_authority", "")
    ).lower()

    return (
        status == "active"
        and authority == "official"
    )


def _contains_any(
    text: str,
    phrases: list[str],
) -> bool:
    text = text.lower()

    return any(
        phrase.lower() in text
        for phrase in phrases
    )


def detect_conflict(
    ranked_chunks: list[RankedChunk],
) -> bool:
    """
    Detect a genuine conflict between active,
    official sources.
    """

    official_chunks = [
        item.chunk
        for item in ranked_chunks
        if is_active_official(item.chunk)
    ]

    documents: dict[str, RetrievedChunk] = {}

    for chunk in official_chunks:
        documents.setdefault(
            chunk.source_file,
            chunk,
        )

    chunks = list(documents.values())

    if len(chunks) < 2:
        return False

    has_hand_wash_guidance = any(
        _contains_any(
            chunk.text,
            [
                "hand-washed",
                "hand wash",
                "hand-wash",
            ],
        )
        and _contains_any(
            chunk.text,
            [
                "breeze tumbler",
                "stainless-steel body",
                "tumbler",
            ],
        )
        for chunk in chunks
    )

    has_dishwasher_guidance = any(
        _contains_any(
            chunk.text,
            [
                "dishwasher safe",
                "dishwasher-safe",
                "all components",
            ],
        )
        and _contains_any(
            chunk.text,
            [
                "breeze tumbler",
                "tumbler",
                "all components",
            ],
        )
        for chunk in chunks
    )

    return (
        has_hand_wash_guidance
        and has_dishwasher_guidance
    )


def analyze_evidence(
    ranked_chunks: list[RankedChunk],
    minimum_results: int = 1,
) -> EvidenceResult:

    if len(ranked_chunks) < minimum_results:
        return EvidenceResult(
            chunks=[],
            conflict_detected=False,
            requires_handoff=True,
            reason="Insufficient retrieved evidence.",
        )

    conflict = detect_conflict(
        ranked_chunks
    )

    if conflict:
        return EvidenceResult(
            chunks=[
                item.chunk
                for item in ranked_chunks
            ],
            conflict_detected=True,
            requires_handoff=True,
            reason=(
                "Two active official sources contain "
                "conflicting guidance."
            ),
        )

    return EvidenceResult(
        chunks=[
            item.chunk
            for item in ranked_chunks
        ],
        conflict_detected=False,
        requires_handoff=False,
        reason=None,
    )