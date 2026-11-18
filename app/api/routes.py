import datetime
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.api.schemas import (
    HealthResponse,
    StatusResponse,
    DocumentItem,
    UploadResponse,
    DeleteResponse,
    QueryRequest,
    QueryResponse,
    CitationItem
)
from app.api.services import services
from app.utils.security import sanitize_filename
from app.config import settings

router = APIRouter(prefix="/api", tags=["NexusRAG"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint verifying Qdrant points and Ollama connectivity."""
    ollama_ok = services.ollama_client.is_available()
    points_count = services.vector_store.count()

    return HealthResponse(
        status="healthy",
        service="NexusRAG API",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        qdrant_points=points_count,
        ollama_connected=ollama_ok,
        configured_model=settings.OLLAMA_MODEL
    )


@router.get("/status", response_model=StatusResponse)
def get_system_status():
    """Return comprehensive system status, model configurations, and document counts."""
    docs = services.pipeline.list_documents()
    total_chunks = services.vector_store.count()
    ollama_diag = services.ollama_client.check_status()

    return StatusResponse(
        project_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_device=settings.EMBEDDING_DEVICE,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        total_documents=len(docs),
        total_chunks=total_chunks,
        ollama_status=ollama_diag
    )


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(None),
    chunk_overlap: Optional[int] = Form(None)
):
    """
    Upload and ingest a document (.pdf, .docx, .csv).
    Validates file format, size limits, and checks for duplicates.
    """
    clean_name = sanitize_filename(file.filename or "uploaded_file")
    ext = Path(clean_name).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Save to a temporary file while validating size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_path = Path(temp_file.name)
        total_size = 0
        try:
            while chunk := file.file.read(65536):
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
                    )
                temp_file.write(chunk)
        except HTTPException:
            if temp_path.exists():
                temp_path.unlink()
            raise

    actual_chunk_size = chunk_size if isinstance(chunk_size, int) else None
    actual_chunk_overlap = chunk_overlap if isinstance(chunk_overlap, int) else None

    try:
        result = services.pipeline.ingest_file(
            source_path=str(temp_path),
            original_filename=clean_name,
            chunk_size=actual_chunk_size,
            chunk_overlap=actual_chunk_overlap
        )
        return UploadResponse(
            document_id=result["document_id"],
            filename=result["filename"],
            chunks=result["chunks"],
            status=result["status"],
            file_size=result["file_size"],
            message=result.get("message")
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {exc}"
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.get("/documents", response_model=List[DocumentItem])
def list_documents():
    """List all ingested documents and their metadata."""
    docs = services.pipeline.list_documents()
    items = []
    for d in docs:
        items.append(
            DocumentItem(
                document_id=d.get("document_id", ""),
                filename=d.get("filename", ""),
                file_type=d.get("file_type", ""),
                file_size=d.get("file_size", 0),
                total_chunks=d.get("total_chunks", 0),
                uploaded_at=d.get("uploaded_at", ""),
                status=d.get("status", "indexed")
            )
        )
    return items


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str):
    """Delete an ingested document and its vector embeddings and BM25 index entries."""
    success = services.pipeline.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )

    return DeleteResponse(
        success=True,
        document_id=document_id,
        message=f"Document '{document_id}' successfully removed from index and storage."
    )


@router.post("/query", response_model=QueryResponse)
def query_documents(req: QueryRequest):
    """
    Execute grounded RAG query:
    1. Retrieves top passages via dense/BM25 hybrid search
    2. Calls local Ollama LLM with strict grounding prompt
    3. Returns synthesized answer with verified source citations
    """
    try:
        res = services.rag_engine.answer_question(
            question=req.question,
            document_id=req.document_id,
            retrieval_mode=req.retrieval_mode,
            top_k=req.top_k,
            session_id=req.session_id,
            temperature=req.temperature
        )

        citations_out = [CitationItem(**c) for c in res["citations"]]
        evidence_out = [CitationItem(**e) for e in res["retrieved_evidence"]]

        return QueryResponse(
            answer=res["answer"],
            citations=citations_out,
            retrieved_evidence=evidence_out,
            session_id=res["session_id"],
            model=res["model"],
            retrieval_mode=res["retrieval_mode"]
        )
    except ConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Local LLM service unavailable: {exc}"
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM query timed out: {exc}"
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {exc}"
        )


@router.post("/chat", response_model=QueryResponse)
def chat_documents(req: QueryRequest):
    """
    Multi-turn conversation query endpoint with session preservation.
    """
    session_id = req.session_id or services.conversation_manager.create_session()
    req_with_session = req.model_copy(update={"session_id": session_id})
    return query_documents(req_with_session)


@router.delete("/chat/{session_id}")
def clear_chat_session(session_id: str):
    """Clear conversation history for a given session."""
    cleared = services.conversation_manager.clear_session(session_id)
    return {"session_id": session_id, "cleared": cleared}


@router.get("/models")
def list_models():
    """List local Ollama models and availability."""
    return services.ollama_client.check_status()
