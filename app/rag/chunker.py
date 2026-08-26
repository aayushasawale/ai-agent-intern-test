from dataclasses import dataclass
from typing import Any

from app.rag.loader import KnowledgeDocument


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_file: str
    heading: str
    text: str
    metadata: dict[str, Any]


def split_into_sections(content: str) -> list[tuple[str, str]]:
    """
    Split Markdown content into sections based on ## headings.

    Returns:
        List of (heading, section_text) tuples.
    """

    lines = content.splitlines()

    sections: list[tuple[str, str]] = []

    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            if current_lines:
                sections.append(
                    (
                        current_heading,
                        "\n".join(current_lines).strip(),
                    )
                )

            current_heading = stripped[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            (
                current_heading,
                "\n".join(current_lines).strip(),
            )
        )

    return [
        (heading, text)
        for heading, text in sections
        if text.strip()
    ]


def chunk_document(
    document: KnowledgeDocument,
    max_characters: int = 1200,
) -> list[DocumentChunk]:
    """
    Convert one knowledge document into searchable chunks.

    Sections are kept intact when possible. Large sections are
    split into smaller chunks while preserving their heading.
    """

    sections = split_into_sections(document.content)

    chunks: list[DocumentChunk] = []

    chunk_number = 0

    for heading, section_text in sections:

        if len(section_text) <= max_characters:
            pieces = [section_text]

        else:
            pieces = []

            for start in range(
                0,
                len(section_text),
                max_characters,
            ):
                piece = section_text[
                    start:start + max_characters
                ].strip()

                if piece:
                    pieces.append(piece)

        for piece in pieces:
            chunk_id = (
                f"{document.document_id}"
                f"-{chunk_number}"
            )

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    source_file=document.source_file,
                    heading=heading,
                    text=piece,
                    metadata=dict(document.metadata),
                )
            )

            chunk_number += 1

    return chunks


def chunk_documents(
    documents: list[KnowledgeDocument],
    max_characters: int = 1200,
) -> list[DocumentChunk]:
    """
    Chunk every knowledge-base document.
    """

    all_chunks: list[DocumentChunk] = []

    for document in documents:
        all_chunks.extend(
            chunk_document(
                document,
                max_characters=max_characters,
            )
        )

    return all_chunks