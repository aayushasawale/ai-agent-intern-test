from dataclasses import dataclass
from typing import Any

from app.rag.vector_store import VectorStore


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    source_file: str
    heading: str
    text: str
    metadata: dict[str, Any]
    similarity_score: float


class Retriever:
    """
    Performs semantic retrieval from the knowledge base.

    This class intentionally does NOT decide which source is
    authoritative. That decision belongs to the ranking layer.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        n_results: int = 8,
    ) -> list[RetrievedChunk]:

        results = self.vector_store.search(
            query=query,
            n_results=n_results,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        retrieved: list[RetrievedChunk] = []

        for index, document in enumerate(documents):

            metadata = metadatas[index]

            # Chroma distance is smaller for more similar results.
            distance = distances[index]

            similarity_score = 1.0 - distance

            retrieved.append(
                RetrievedChunk(
                    chunk_id=ids[index],
                    document_id=metadata["document_id"],
                    source_file=metadata["source_file"],
                    heading=metadata["heading"],
                    text=document,
                    metadata=metadata,
                    similarity_score=similarity_score,
                )
            )

        return retrieved