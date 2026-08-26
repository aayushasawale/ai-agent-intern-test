from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class KnowledgeDocument:
    document_id: str
    title: str
    metadata: dict[str, Any]
    content: str
    source_file: str


def _normalize_metadata(value: Any) -> Any:
    """
    Convert YAML-specific values such as dates into strings so that
    metadata remains easy to serialize and store in a vector database.
    """
    if isinstance(value, dict):
        return {
            str(key): _normalize_metadata(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_normalize_metadata(item) for item in value]

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return value


def parse_markdown_file(file_path: Path) -> KnowledgeDocument:
    """
    Parse a Markdown knowledge-base file containing YAML front matter.

    Expected format:

    ---
    document_id: ...
    title: ...
    ...
    ---

    Markdown content...
    """

    text = file_path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        raise ValueError(
            f"{file_path.name} does not contain YAML front matter."
        )

    parts = text.split("---", 2)

    if len(parts) != 3:
        raise ValueError(
            f"{file_path.name} has invalid front matter."
        )

    _, front_matter, content = parts

    metadata = yaml.safe_load(front_matter) or {}
    metadata = _normalize_metadata(metadata)

    document_id = metadata.get("document_id")
    title = metadata.get("title")

    if not document_id:
        raise ValueError(
            f"{file_path.name} is missing document_id."
        )

    if not title:
        raise ValueError(
            f"{file_path.name} is missing title."
        )

    return KnowledgeDocument(
        document_id=document_id,
        title=title,
        metadata=metadata,
        content=content.strip(),
        source_file=file_path.name,
    )


def load_knowledge_base(
    knowledge_base_path: str | Path,
) -> list[KnowledgeDocument]:
    """
    Load every Markdown document from the knowledge-base directory.
    """

    knowledge_base_path = Path(knowledge_base_path)

    if not knowledge_base_path.exists():
        raise FileNotFoundError(
            f"Knowledge-base directory not found: {knowledge_base_path}"
        )

    files = sorted(knowledge_base_path.glob("*.md"))

    documents = [
        parse_markdown_file(file_path)
        for file_path in files
    ]

    return documents