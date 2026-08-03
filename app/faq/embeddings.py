import logging
from sentence_transformers import SentenceTransformer
import chromadb

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(
            settings.embedding_model,
            local_files_only=settings.embedding_local_only,
        )
        logger.info(f"Embedding model loaded: {settings.embedding_model}")

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def get_single_embedding(self, text: str) -> list[float]:
        return self.model.encode([text])[0].tolist()
