from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    qdrant_points: int
    ollama_connected: bool
    configured_model: str


class DocumentItem(BaseModel):
    document_id: str
    filename: str
    file_type: str
    file_size: int
    total_chunks: int
    uploaded_at: str
    status: str = "indexed"


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks: int
    status: str
    file_size: int
    message: Optional[str] = None


class DeleteResponse(BaseModel):
    success: bool
    document_id: str
    message: str


class CitationItem(BaseModel):
    id: int
    source: str
    page: Optional[int] = None
    row: Optional[int] = None
    chunk_index: Optional[int] = 0
    location_label: str = ""
    score: float
    dense_score: Optional[float] = None
    bm25_score: Optional[float] = None
    text: str
    snippet: str
    document_id: Optional[str] = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    document_id: Optional[str] = Field(None, description="Optional document ID to restrict search")
    top_k: int = Field(5, ge=1, le=20, description="Number of context chunks to retrieve")
    retrieval_mode: str = Field("hybrid", description="'hybrid', 'dense', or 'lexical'")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Generation temperature")


class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationItem]
    retrieved_evidence: List[CitationItem]
    session_id: Optional[str] = None
    model: str
    retrieval_mode: str


class StatusResponse(BaseModel):
    project_name: str
    environment: str
    embedding_model: str
    embedding_device: str
    chunk_size: int
    chunk_overlap: int
    total_documents: int
    total_chunks: int
    ollama_status: Dict[str, Any]
