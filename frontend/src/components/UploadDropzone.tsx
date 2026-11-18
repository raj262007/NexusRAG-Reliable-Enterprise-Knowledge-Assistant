"use client";

import React, { useState, useRef } from "react";
import { api } from "@/lib/api";

interface UploadDropzoneProps {
  onUploadSuccess: () => void;
}

export function UploadDropzone({ onUploadSuccess }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    const file = fileList[0];

    const validExtensions = [".pdf", ".docx", ".csv"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Unsupported file type: ${ext}. Only PDF, DOCX, and CSV are accepted.`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg("File size exceeds 25 MB limit.");
      return;
    }

    setErrorMsg(null);
    setSuccessMsg(null);
    setUploading(true);

    try {
      const res = await api.uploadDocument(file);
      if (res.status === "duplicate") {
        setSuccessMsg(`Document '${res.filename}' was already indexed (${res.chunks} chunks).`);
      } else {
        setSuccessMsg(`Successfully ingested '${res.filename}' into ${res.chunks} vectorized chunks.`);
      }
      onUploadSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload document.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
      <h3 className="font-semibold text-sm text-slate-200 mb-3 flex items-center justify-between">
        <span>Ingest Document</span>
        <span className="text-xs text-slate-400 font-normal">PDF, DOCX, CSV up to 25MB</span>
      </h3>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
          isDragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-slate-700/80 hover:border-slate-600 bg-slate-950/40"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.csv"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {uploading ? (
          <div className="py-2">
            <div className="inline-block animate-spin rounded-full h-7 w-7 border-t-2 border-b-2 border-blue-500 mb-2"></div>
            <p className="text-sm text-blue-400 font-medium">Extracting, Chunking & Embedding...</p>
            <p className="text-xs text-slate-500 mt-1">Generating 384-d vectors & updating BM25 index</p>
          </div>
        ) : (
          <div>
            <div className="text-2xl mb-1">📄</div>
            <p className="text-sm font-medium text-slate-300">
              Drag & drop or <span className="text-blue-400 underline">browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Deterministic deduplication & metadata preservation
            </p>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="mt-3 p-3 bg-red-950/50 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-start gap-2">
          <span>⚠️</span>
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mt-3 p-3 bg-emerald-950/50 border border-emerald-800/60 rounded-lg text-xs text-emerald-300 flex items-start gap-2">
          <span>✓</span>
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
}
