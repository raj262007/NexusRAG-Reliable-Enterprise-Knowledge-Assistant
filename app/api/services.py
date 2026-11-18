import logging
from typing import Optional

from app.config import settings
from app.embeddings.embedder import EmbeddingEngine
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25_index import BM25Index
from app.retrieval.hybrid_search import HybridRetriever
from app.ingestion.pipeline import IngestionPipeline
from app.generation.ollama_client import OllamaClient
from app.generation.rag_engine import RAGEngine
from app.generation.conversation import ConversationManager

logger = logging.getLogger(__name__)


class ServiceContainer:
    """Singleton service registry for NexusRAG application."""
    def __init__(self):
        self._embedder: Optional[EmbeddingEngine] = None
        self._vector_store: Optional[VectorStore] = None
        self._bm25_index: Optional[BM25Index] = None
        self._retriever: Optional[HybridRetriever] = None
        self._pipeline: Optional[IngestionPipeline] = None
        self._ollama_client: Optional[OllamaClient] = None
        self._conversation_manager: Optional[ConversationManager] = None
        self._rag_engine: Optional[RAGEngine] = None

    @property
    def embedder(self) -> EmbeddingEngine:
        if self._embedder is None:
            self._embedder = EmbeddingEngine(
                model_name=settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
        return self._embedder

    @property
    def vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = VectorStore(
                storage_path=str(settings.QDRANT_STORAGE_PATH),
                collection_name=settings.COLLECTION_NAME
            )
            self._vector_store.create_collection(vector_size=self.embedder.dimension)
        return self._vector_store

    @property
    def bm25_index(self) -> BM25Index:
        if self._bm25_index is None:
            self._bm25_index = BM25Index()
        return self._bm25_index

    @property
    def retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = HybridRetriever(
                vector_store=self.vector_store,
                bm25_index=self.bm25_index,
                embedder=self.embedder,
                k=settings.RRF_K
            )
        return self._retriever

    @property
    def pipeline(self) -> IngestionPipeline:
        if self._pipeline is None:
            self._pipeline = IngestionPipeline(
                vector_store=self.vector_store,
                bm25_index=self.bm25_index,
                embedder=self.embedder,
                upload_dir=settings.UPLOAD_DIR
            )
        return self._pipeline

    @property
    def ollama_client(self) -> OllamaClient:
        if self._ollama_client is None:
            self._ollama_client = OllamaClient(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                timeout=settings.OLLAMA_TIMEOUT_SECONDS
            )
        return self._ollama_client

    @property
    def conversation_manager(self) -> ConversationManager:
        if self._conversation_manager is None:
            self._conversation_manager = ConversationManager()
        return self._conversation_manager

    @property
    def rag_engine(self) -> RAGEngine:
        if self._rag_engine is None:
            self._rag_engine = RAGEngine(
                retriever=self.retriever,
                ollama_client=self.ollama_client,
                conversation_manager=self.conversation_manager
            )
        return self._rag_engine


# Global service container instance
services = ServiceContainer()
