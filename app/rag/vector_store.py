from pathlib import Path
from typing import Any

import chromadb

from app.rag.chunker import DocumentChunk
from app.rag.embeddings import EmbeddingModel


class VectorStore:
    """
    ChromaDB-backed vector store for knowledge-base chunks.
    """

    def __init__(
        self,
        persist_directory: str | Path = "chroma_db",
        collection_name: str = "knowledge_base",
    ):
        self.persist_directory = str(
            Path(persist_directory)
        )

        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Aster & Row knowledge base"
            },
        )

        self.embedding_model = EmbeddingModel()

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> None:
        """
        Add document chunks to ChromaDB.
        """

        if not chunks:
            return

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = self.embedding_model.encode(texts)

        ids = [
            chunk.chunk_id
            for chunk in chunks
        ]

        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            metadata = dict(chunk.metadata)

            metadata.update(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source_file": chunk.source_file,
                    "heading": chunk.heading,
                }
            )

            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> dict[str, Any]:
        """
        Perform semantic search.
        """

        query_embedding = self.embedding_model.encode(
            [query]
        )[0]

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )

    def count(self) -> int:
        """
        Return number of stored chunks.
        """

        return self.collection.count()