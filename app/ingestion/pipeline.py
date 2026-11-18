import datetime
import json
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4, uuid5, NAMESPACE_DNS

from app.ingestion.document_processor import process_document
from app.ingestion.chunker import chunk_documents
from app.utils.security import sanitize_filename, compute_file_hash_from_path, compute_file_hash
from app.config import settings

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        vector_store,
        bm25_index,
        embedder,
        upload_dir: Optional[Path] = None,
        registry_path: Optional[Path] = None
    ):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.embedder = embedder
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = Path(registry_path or (self.upload_dir.parent / "documents_registry.json"))

        # Initialize documents registry
        self._load_registry()

        # Sync BM25 index from stored vector store chunks if BM25 is empty
        if self.bm25_index.count() == 0 and self.vector_store.count() > 0:
            existing_chunks = self.vector_store.get_all_chunks(limit=10000)
            if existing_chunks:
                self.bm25_index.build_index(existing_chunks)
                logger.info("Initialized BM25 index with %d chunks from vector store.", len(existing_chunks))

    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry: Dict[str, Dict[str, Any]] = json.load(f)
            except Exception as e:
                logger.warning("Failed to load documents registry: %s. Re-initializing.", e)
                self.registry = {}
        else:
            self.registry = {}

    def _save_registry(self):
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error("Failed to save documents registry: %s", e)

    def validate_file(self, file_path: Path, max_size_mb: Optional[int] = None) -> None:
        """Validate file existence, extension, and size."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        limit_mb = max_size_mb or settings.MAX_FILE_SIZE_MB
        size_bytes = file_path.stat().st_size
        max_bytes = limit_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(
                f"File size ({size_bytes / (1024*1024):.1f} MB) exceeds maximum allowed limit of {limit_mb} MB."
            )

    def ingest_file(
        self,
        source_path: str,
        original_filename: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        End-to-end ingestion pipeline:
        1. Validates file
        2. Checks for duplicates via hash
        3. Copies to upload storage
        4. Extracts document content
        5. Chunks text with metadata preservation
        6. Generates embeddings
        7. Indexes in Qdrant & BM25
        8. Registers document record
        """
        src = Path(source_path)
        self.validate_file(src)

        filename = sanitize_filename(original_filename or src.name)
        file_hash = compute_file_hash_from_path(src)
        file_size = src.stat().st_size

        # Check for existing document with same content hash
        for doc_id, doc_meta in list(self.registry.items()):
            if doc_meta.get("hash") == file_hash:
                logger.info("File %s is a duplicate of doc_id %s (matching hash)", filename, doc_id)
                return {
                    "document_id": doc_id,
                    "filename": doc_meta.get("filename", filename),
                    "chunks": doc_meta.get("total_chunks", 0),
                    "status": "duplicate",
                    "file_size": file_size,
                    "message": "File already ingested with identical content."
                }

        # Save to persistent storage with unique doc_id
        doc_id = str(uuid4())
        ext = src.suffix.lower()
        dest_filename = f"{doc_id}_{filename}"
        dest_path = self.upload_dir / dest_filename
        shutil.copy2(src, dest_path)

        # 4. Extract content
        raw_docs = process_document(str(dest_path))

        # 5. Chunk text
        c_size = chunk_size or settings.CHUNK_SIZE
        c_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        chunks = chunk_documents(raw_docs, chunk_size=c_size, overlap=c_overlap)

        if not chunks:
            if dest_path.exists():
                dest_path.unlink()
            raise ValueError(f"No text chunks could be generated from {filename}.")

        # Enrich chunk metadata
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for idx, chunk in enumerate(chunks):
            safe_chunk_id = str(uuid5(NAMESPACE_DNS, f"{doc_id}_{idx}"))
            chunk["id"] = safe_chunk_id
            chunk["metadata"]["chunk_id"] = safe_chunk_id
            chunk["metadata"]["document_id"] = doc_id
            chunk["metadata"]["source"] = filename
            chunk["metadata"]["file_type"] = ext
            chunk["metadata"]["uploaded_at"] = now_iso
            # Avoid exposing absolute server paths to clients
            chunk["metadata"]["file_name"] = filename

        # 6. Embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed_texts(chunk_texts)

        # 7. Index in Qdrant & BM25
        self.vector_store.add_chunks(chunks, embeddings, document_id=doc_id)
        self.bm25_index.add_chunks(chunks)

        # 8. Update Registry
        record = {
            "document_id": doc_id,
            "filename": filename,
            "stored_filename": dest_filename,
            "file_type": ext,
            "file_size": file_size,
            "hash": file_hash,
            "total_chunks": len(chunks),
            "uploaded_at": now_iso,
            "status": "indexed"
        }
        self.registry[doc_id] = record
        self._save_registry()

        logger.info("Ingested %s: %d chunks indexed into Qdrant & BM25", filename, len(chunks))

        return {
            "document_id": doc_id,
            "filename": filename,
            "chunks": len(chunks),
            "status": "success",
            "file_size": file_size
        }

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by document_id from vector store, BM25 index, and upload storage.
        """
        if document_id not in self.registry:
            # Check by filename / source
            matched_id = None
            for d_id, meta in self.registry.items():
                if meta.get("filename") == document_id or meta.get("stored_filename") == document_id:
                    matched_id = d_id
                    break
            if not matched_id:
                return False
            document_id = matched_id

        # 1. Delete from Vector Store
        self.vector_store.delete_document(document_id)

        # 2. Delete from BM25
        self.bm25_index.delete_document(document_id)

        # 3. Delete physical file
        meta = self.registry.get(document_id, {})
        stored_file = meta.get("stored_filename")
        if stored_file:
            fp = self.upload_dir / stored_file
            if fp.exists():
                try:
                    fp.unlink()
                except Exception as e:
                    logger.warning("Failed to delete physical file %s: %s", fp, e)

        # 4. Remove from registry
        del self.registry[document_id]
        self._save_registry()
        logger.info("Successfully deleted document %s", document_id)
        return True

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents with metadata."""
        return list(self.registry.values())

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a single document."""
        return self.registry.get(document_id)
