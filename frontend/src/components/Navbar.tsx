"use client";

import React from "react";
import { SystemStatus } from "@/lib/api";

interface NavbarProps {
  status: SystemStatus | null;
  onOpenSettings: () => void;
  activeDocFilter: string | null;
  onClearFilter: () => void;
}

export function Navbar({ status, onOpenSettings, activeDocFilter, onClearFilter }: NavbarProps) {
  const ollamaOnline = status?.ollama_status?.available ?? false;

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            NR
          </div>
          <div>
            <h1 className="font-semibold text-lg text-white tracking-tight flex items-center gap-2">
              NexusRAG
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">
                Local Enterprise RAG
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {activeDocFilter && (
            <div className="hidden sm:flex items-center text-xs bg-indigo-950/60 text-indigo-300 border border-indigo-700/40 rounded-full px-3 py-1 gap-2">
              <span>Filter: <strong>{activeDocFilter}</strong></span>
              <button
                onClick={onClearFilter}
                className="hover:text-white"
                title="Clear filter"
              >
                ✕
              </button>
            </div>
          )}

          {/* Ollama Status Pill */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs border font-medium ${
              ollamaOnline
                ? "bg-emerald-950/60 border-emerald-700/50 text-emerald-300"
                : "bg-amber-950/60 border-amber-700/50 text-amber-300"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                ollamaOnline ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span>{ollamaOnline ? `Ollama (${status?.ollama_status?.configured_model || "Ready"})` : "Ollama Offline"}</span>
          </div>

          {/* Chunks / Points pill */}
          <div className="hidden md:flex items-center text-xs bg-slate-800/80 text-slate-300 px-3 py-1 rounded-full border border-slate-700">
            <span>{status?.total_chunks ?? 0} vectors</span>
          </div>

          {/* Settings Trigger */}
          <button
            onClick={onOpenSettings}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Settings & Diagnostics"
          >
            ⚙️
          </button>
        </div>
      </div>
    </header>
  );
}
