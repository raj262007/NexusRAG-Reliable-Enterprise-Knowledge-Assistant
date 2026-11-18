const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface DocumentItem {
  document_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  total_chunks: number;
  uploaded_at: string;
  status: string;
}

export interface CitationItem {
  id: number;
  source: string;
  page?: number | null;
  row?: number | null;
  chunk_index?: number;
  location_label: string;
  score: number;
  dense_score?: number | null;
  bm25_score?: number | null;
  text: string;
  snippet: string;
  document_id?: string | null;
}

export interface QueryResponse {
  answer: string;
  citations: CitationItem[];
  retrieved_evidence: CitationItem[];
  session_id?: string | null;
  model: string;
  retrieval_mode: string;
}

export interface SystemStatus {
  project_name: string;
  environment: string;
  embedding_model: string;
  embedding_device: string;
  chunk_size: number;
  chunk_overlap: number;
  total_documents: number;
  total_chunks: number;
  ollama_status: {
    available: boolean;
    base_url: string;
    configured_model: string;
    installed_models: string[];
    model_ready: boolean;
    instructions?: string | null;
  };
}

export const api = {
  async getStatus(): Promise<SystemStatus> {
    const res = await fetch(`${API_BASE}/status`);
    if (!res.ok) throw new Error("Failed to fetch system status");
    return res.json();
  },

  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Failed health check");
    return res.json();
  },

  async listDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error("Failed to load document library");
    return res.json();
  },

  async uploadDocument(file: File, chunkSize?: number, chunkOverlap?: number) {
    const formData = new FormData();
    formData.append("file", file);
    if (chunkSize) formData.append("chunk_size", chunkSize.toString());
    if (chunkOverlap) formData.append("chunk_overlap", chunkOverlap.toString());

    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json();
  },

  async deleteDocument(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete document");
    return res.json();
  },

  async query(params: {
    question: string;
    document_id?: string;
    top_k?: number;
    retrieval_mode?: string;
    session_id?: string;
    temperature?: number;
  }): Promise<QueryResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Query failed" }));
      throw new Error(err.detail || "Query failed");
    }
    return res.json();
  },

  async clearChat(sessionId: string) {
    const res = await fetch(`${API_BASE}/chat/${sessionId}`, {
      method: "DELETE",
    });
    return res.json();
  },
};
