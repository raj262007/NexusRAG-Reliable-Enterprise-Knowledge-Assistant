"use client";

import React from "react";
import { SystemStatus } from "@/lib/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: SystemStatus | null;
  retrievalMode: string;
  onChangeRetrievalMode: (mode: string) => void;
  topK: number;
  onChangeTopK: (k: number) => void;
  temperature: number;
  onChangeTemperature: (t: number) => void;
}

export function SettingsModal({
  isOpen,
  onClose,
  status,
  retrievalMode,
  onChangeRetrievalMode,
  topK,
  onChangeTopK,
  temperature,
  onChangeTemperature,
}: SettingsModalProps) {
  if (!isOpen) return null;

  const ollama = status?.ollama_status;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span>⚙️ Retrieval & Engine Settings</span>
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg"
          >
            ✕
          </button>
        </div>

        {/* Retrieval Mode */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Retrieval Fusion Mode
          </label>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {[
              { id: "hybrid", label: "Hybrid (RRF)", desc: "Dense + BM25" },
              { id: "dense", label: "Dense Only", desc: "Cosine Vector" },
              { id: "lexical", label: "Lexical Only", desc: "BM25 Okapi" },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => onChangeRetrievalMode(m.id)}
                className={`p-2.5 rounded-lg border text-left transition ${
                  retrievalMode === m.id
                    ? "bg-blue-600/20 border-blue-500 text-blue-200"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="font-medium text-slate-200">{m.label}</div>
                <div className="text-[10px] text-slate-500 mt-0.5">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Top K */}
        <div>
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300 mb-1">
            <span>Top-K Context Passages</span>
            <span className="font-mono text-blue-400">{topK}</span>
          </div>
          <input
            type="range"
            min="1"
            max="15"
            value={topK}
            onChange={(e) => onChangeTopK(parseInt(e.target.value, 10))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>1 passage</span>
            <span>15 passages</span>
          </div>
        </div>

        {/* Temperature */}
        <div>
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300 mb-1">
            <span>Generation Temperature</span>
            <span className="font-mono text-blue-400">{temperature}</span>
          </div>
          <input
            type="range"
            min="0.0"
            max="0.8"
            step="0.05"
            value={temperature}
            onChange={(e) => onChangeTemperature(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>0.0 (Strict / Factual)</span>
            <span>0.8 (Creative)</span>
          </div>
        </div>

        {/* Ollama Runtime Status & Guide */}
        <div className="bg-slate-950 rounded-xl p-3.5 border border-slate-800/80 text-xs space-y-2">
          <div className="flex items-center justify-between font-medium">
            <span className="text-slate-300">Local LLM Runtime:</span>
            <span className={ollama?.available ? "text-emerald-400" : "text-amber-400"}>
              {ollama?.available ? "Connected" : "Disconnected"}
            </span>
          </div>
          <div className="text-slate-400 text-[11px] space-y-1">
            <p><strong>Configured Model:</strong> {ollama?.configured_model || "qwen2.5:3b"}</p>
            <p><strong>Installed Models:</strong> {ollama?.installed_models?.length ? ollama.installed_models.join(", ") : "None detected"}</p>
          </div>

          {!ollama?.available && (
            <div className="mt-2 p-2.5 bg-amber-950/40 border border-amber-800/50 rounded text-[11px] text-amber-200 leading-relaxed font-mono">
              <p className="font-semibold text-amber-300 mb-1">To enable local generation:</p>
              <p>1. Run <code>winget install Ollama.Ollama</code></p>
              <p>2. Run <code>ollama run qwen2.5:3b</code></p>
            </div>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
