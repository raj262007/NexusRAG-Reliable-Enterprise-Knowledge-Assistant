"use client";

import React, { useState, useRef, useEffect } from "react";
import { CitationItem, api } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: CitationItem[];
  model?: string;
}

interface ChatInterfaceProps {
  activeDocFilter: string | null;
  retrievalMode: string;
  topK: number;
  temperature: number;
  onOpenCitations: (citations: CitationItem[]) => void;
}

export function ChatInterface({
  activeDocFilter,
  retrievalMode,
  topK,
  temperature,
  onOpenCitations,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || loading) return;

    setErrorMsg(null);
    setInput("");
    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.query({
        question: q,
        document_id: activeDocFilter || undefined,
        top_k: topK,
        retrieval_mode: retrievalMode,
        session_id: sessionId,
        temperature: temperature,
      });

      if (res.session_id) setSessionId(res.session_id);

      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        citations: res.citations,
        model: res.model,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate answer. Ensure Ollama is running if generating locally.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (sessionId) {
      try {
        await api.clearChat(sessionId);
      } catch (e) {
        // ignore
      }
    }
    setMessages([]);
    setSessionId(undefined);
    setErrorMsg(null);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl flex flex-col h-[650px] shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-blue-500 animate-pulse"></div>
          <span className="font-semibold text-sm text-slate-200">Grounded Conversation</span>
          <span className="text-[11px] text-slate-500 font-mono">
            Mode: {retrievalMode.toUpperCase()} | Top-K: {topK}
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-xs text-slate-400 hover:text-red-400 transition"
          >
            Clear History
          </button>
        )}
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
            <div className="h-12 w-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-2xl text-blue-400">
              💬
            </div>
            <div className="max-w-md space-y-1">
              <h4 className="font-medium text-sm text-slate-200">Ask questions about your uploaded documents</h4>
              <p className="text-xs text-slate-400">
                NexusRAG retrieves grounded facts via hybrid search and cites verifiable sources without hallucinations.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg pt-2 text-xs">
              {[
                "Summarize the key findings from my documents",
                "What are the main risks identified in the text?",
                "Extract all action items and metrics",
                "Compare the sections discussing architecture",
              ].map((starter, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(starter)}
                  className="p-2.5 bg-slate-950/60 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/40 rounded-lg text-slate-300 text-left transition"
                >
                  "{starter}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex flex-col ${
                msg.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-slate-950 border border-slate-800 text-slate-200 shadow-sm"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citation Pills on Assistant Answers */}
                {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-semibold mr-1">
                      CITATIONS:
                    </span>
                    {msg.citations.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => onOpenCitations(msg.citations || [])}
                        className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-blue-950/80 text-blue-300 border border-blue-700/50 hover:bg-blue-900 transition flex items-center gap-1"
                        title={`Click to view passage excerpt (Score: ${c.score})`}
                      >
                        <span>[{c.id}]</span>
                        <span className="truncate max-w-[120px]">{c.source}</span>
                        {c.page && <span>p.{c.page}</span>}
                        {c.row && <span>r.{c.row}</span>}
                      </button>
                    ))}
                    <button
                      onClick={() => onOpenCitations(msg.citations || [])}
                      className="text-[10px] text-blue-400 hover:underline ml-1"
                    >
                      Inspect All Evidence →
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-start">
            <div className="bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3 text-sm text-slate-400 flex items-center space-x-2">
              <span className="inline-block animate-spin h-3.5 w-3.5 border-2 border-blue-400 border-t-transparent rounded-full"></span>
              <span>Retrieving hybrid context & generating grounded answer...</span>
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="p-3 bg-red-950/60 border border-red-800/80 rounded-xl text-xs text-red-300 space-y-1">
            <p className="font-semibold flex items-center gap-1">⚠️ Error</p>
            <p>{errorMsg}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/90">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              activeDocFilter
                ? `Ask about selected document (${activeDocFilter})...`
                : "Ask any question across all indexed documents..."
            }
            disabled={loading}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl text-sm font-medium transition shadow-sm"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
