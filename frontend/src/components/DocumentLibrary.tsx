"use client";

import React, { useState } from "react";
import { DocumentItem, api } from "@/lib/api";

interface DocumentLibraryProps {
  documents: DocumentItem[];
  loading: boolean;
  activeFilter: string | null;
  onSelectFilter: (docId: string | null) => void;
  onRefresh: () => void;
}

export function DocumentLibrary({
  documents,
  loading,
  activeFilter,
  onSelectFilter,
  onRefresh,
}: DocumentLibraryProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this document from the vector store?")) return;

    setDeletingId(docId);
    try {
      await api.deleteDocument(docId);
      if (activeFilter === docId) onSelectFilter(null);
      onRefresh();
    } catch (err: any) {
      alert(`Deletion failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm text-slate-200 flex items-center gap-2">
          <span>Document Library</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
            {documents.length}
          </span>
        </h3>
        <button
          onClick={onRefresh}
          className="text-xs text-slate-400 hover:text-slate-200 transition"
          title="Refresh document list"
        >
          🔄 Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[380px]">
        {loading ? (
          <div className="text-center py-8 text-xs text-slate-500">
            Loading indexed documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-800 rounded-lg p-4">
            <p className="text-xs text-slate-400 font-medium">No documents ingested yet</p>
            <p className="text-[11px] text-slate-500 mt-1">Upload a PDF, DOCX or CSV to start asking questions.</p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = activeFilter === doc.document_id;
            const isDeleting = deletingId === doc.document_id;

            return (
              <div
                key={doc.document_id}
                onClick={() => onSelectFilter(isSelected ? null : doc.document_id)}
                className={`p-3 rounded-lg border text-left transition cursor-pointer flex items-center justify-between ${
                  isSelected
                    ? "bg-blue-950/40 border-blue-600/60 shadow-sm"
                    : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="min-w-0 flex-1 pr-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono uppercase bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px]">
                      {doc.file_type.replace(".", "")}
                    </span>
                    <span className="text-xs font-medium text-slate-200 truncate block">
                      {doc.filename}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-1">
                    <span>{doc.total_chunks} chunks</span>
                    <span>•</span>
                    <span>{formatBytes(doc.file_size)}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => handleDelete(doc.document_id, e)}
                    disabled={isDeleting}
                    className="text-slate-500 hover:text-red-400 p-1.5 rounded transition text-xs"
                    title="Delete document and embeddings"
                  >
                    {isDeleting ? "..." : "🗑️"}
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {activeFilter && (
        <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Filtering retrieval to 1 document</span>
          <button
            onClick={() => onSelectFilter(null)}
            className="text-blue-400 hover:underline"
          >
            Show All
          </button>
        </div>
      )}
    </div>
  );
}
