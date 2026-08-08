import logging
import chromadb
from app.config import settings
from app.models.schemas import FAQItem, Language
from app.faq.ingestion import FAQIngestion
from app.faq.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class FAQStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        self.ingestion = FAQIngestion()
        self.embeddings = EmbeddingService()
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        items = self.ingestion.load_all()
        if not items:
            logger.warning("No FAQ items found to index")
            self._initialized = True
            return

        self.ingest_items(items)
        self._initialized = True

    def ingest_items(self, items: list[FAQItem]):
        documents = []
        metadatas = []
        ids = []

        for item in items:
            documents.append(f"{item.question} {item.answer}")
            metadatas.append({
                "id": item.id,
                "question": item.question,
                "answer": item.answer,
                "category": item.category,
                "language": item.language.value,
            })
            ids.append(item.id)

        embeddings = self.embeddings.get_embeddings(documents)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info(f"Ingested {len(items)} FAQ items into vector store")

    def search(self, query: str, language: str, top_k: int = 3) -> list[dict]:
        chunks, _ = self.search_with_scores(query, language, top_k)
        return chunks

    def search_with_scores(self, query: str, language: str, top_k: int = 3) -> tuple[list[dict], list[float]]:
        if not self._initialized:
            self.initialize()

        query_embedding = self.embeddings.get_single_embedding(query)

        where_filter = {"language": language} if language else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        if not results["metadatas"][0]:
            return [], []

        distances = list(results["distances"][0]) if results.get("distances") else []

        chunks = []
        for metadata in results["metadatas"][0]:
            chunks.append({
                "id": metadata["id"],
                "question": metadata["question"],
                "answer": metadata["answer"],
                "category": metadata["category"],
                "language": metadata["language"],
            })

        return chunks, distances

    def delete_item(self, item_id: str):
        self.collection.delete(ids=[item_id])
        logger.info(f"Deleted FAQ item {item_id}")

    def get_all(self) -> list[dict]:
        if not self._initialized:
            self.initialize()

        results = self.collection.get()
        items = []
        for metadata in results["metadatas"]:
            items.append({
                "id": metadata["id"],
                "question": metadata["question"],
                "answer": metadata["answer"],
                "category": metadata["category"],
                "language": metadata["language"],
            })
        return items
