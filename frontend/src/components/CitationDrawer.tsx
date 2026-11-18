"use client";

import React from "react";
import { CitationItem } from "@/lib/api";

interface CitationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  citations: CitationItem[];
  selectedCitation: CitationItem | null;
  onSelectCitation: (c: CitationItem) => void;
}

export function CitationDrawer({
  isOpen,
  onClose,
  citations,
  selectedCitation,
  onSelectCitation,
}: CitationDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-40 flex flex-col">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
            <span>Retrieved Evidence</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-300 font-mono">
              {citations.length} sources
            </span>
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Ranked passages with hybrid similarity scores
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {citations.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-500">
            No citation passages selected or available for this answer.
          </div>
        ) : (
          citations.map((c) => {
            const isSelected = selectedCitation?.id === c.id;

            return (
              <div
                key={c.id}
                onClick={() => onSelectCitation(c)}
                className={`p-3.5 rounded-xl border transition cursor-pointer text-left ${
                  isSelected
                    ? "bg-slate-800/90 border-blue-500/80 shadow-md ring-1 ring-blue-500/30"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-blue-400 truncate max-w-[200px]">
                    [{c.id}] {c.source}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/70 text-blue-300 border border-blue-800/40">
                    RRF: {c.score.toFixed(4)}
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-2">
                  <span>{c.location_label || `Chunk ${c.chunk_index}`}</span>
                  {c.dense_score !== null && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      (Dense: {c.dense_score})
                    </span>
                  )}
                  {c.bm25_score !== null && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      (BM25: {c.bm25_score})
                    </span>
                  )}
                </div>

                <div className="text-xs text-slate-300 bg-slate-900/90 rounded p-2.5 font-sans leading-relaxed border border-slate-800/60">
                  {c.text}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
