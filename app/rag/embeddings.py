from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Local embedding model used for knowledge-base retrieval.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

    def encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Convert text into embedding vectors.
        """

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()