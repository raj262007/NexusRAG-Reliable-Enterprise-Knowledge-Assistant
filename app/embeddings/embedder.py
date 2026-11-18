import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.device = device

        # Set offline hub fallback to prevent network timeouts when offline
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

        # Lazy import of SentenceTransformer to avoid 20s import tax at module load
        from sentence_transformers import SentenceTransformer

        try:
            self.model = SentenceTransformer(
                model_name,
                device=device
            )
        except Exception as exc:
            logger.warning(
                "Failed to initialize model on %s (%s). Falling back to CPU.",
                device, exc
            )
            self.model = SentenceTransformer(
                model_name,
                device="cpu"
            )

        # Sentence-transformers v3+ renamed get_sentence_embedding_dimension
        if hasattr(self.model, "get_embedding_dimension"):
            self.dimension = self.model.get_embedding_dimension()
        else:
            self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text cannot be empty.")

        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(not isinstance(t, str) or not t.strip() for t in texts):
            raise ValueError("All texts must be non-empty strings.")

        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        return vectors.tolist()
