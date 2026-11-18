"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "@/components/Navbar";
import { UploadDropzone } from "@/components/UploadDropzone";
import { DocumentLibrary } from "@/components/DocumentLibrary";
import { ChatInterface } from "@/components/ChatInterface";
import { CitationDrawer } from "@/components/CitationDrawer";
import { SettingsModal } from "@/components/SettingsModal";
import { DocumentItem, CitationItem, SystemStatus, api } from "@/lib/api";

export default function Home() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  // Settings & Filter states
  const [activeDocFilter, setActiveDocFilter] = useState<string | null>(null);
  const [retrievalMode, setRetrievalMode] = useState("hybrid");
  const [topK, setTopK] = useState(5);
  const [temperature, setTemperature] = useState(0.1);

  // UI Drawer / Modal states
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isCitationsOpen, setIsCitationsOpen] = useState(false);
  const [activeCitations, setActiveCitations] = useState<CitationItem[]>([]);
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.getStatus();
      setStatus(data);
    } catch (e) {
      console.error("Failed to load status:", e);
    }
  }, []);

  const fetchDocuments = useCallback(async () => {
    setDocsLoading(true);
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (e) {
      console.error("Failed to load documents:", e);
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    fetchDocuments();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchDocuments]);

  const handleOpenCitations = (citations: CitationItem[]) => {
    setActiveCitations(citations);
    setSelectedCitation(citations.length > 0 ? citations[0] : null);
    setIsCitationsOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar
        status={status}
        onOpenSettings={() => setIsSettingsOpen(true)}
        activeDocFilter={
          activeDocFilter
            ? documents.find((d) => d.document_id === activeDocFilter)?.filename || activeDocFilter
            : null
        }
        onClearFilter={() => setActiveDocFilter(null)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Upload Dropzone & Document Library */}
          <div className="lg:col-span-5 space-y-6">
            <UploadDropzone
              onUploadSuccess={() => {
                fetchDocuments();
                fetchStatus();
              }}
            />

            <DocumentLibrary
              documents={documents}
              loading={docsLoading}
              activeFilter={activeDocFilter}
              onSelectFilter={(docId) => setActiveDocFilter(docId)}
              onRefresh={() => {
                fetchDocuments();
                fetchStatus();
              }}
            />
          </div>

          {/* Right Column: Interactive Grounded Chat */}
          <div className="lg:col-span-7">
            <ChatInterface
              activeDocFilter={activeDocFilter}
              retrievalMode={retrievalMode}
              topK={topK}
              temperature={temperature}
              onOpenCitations={handleOpenCitations}
            />
          </div>
        </div>
      </main>

      {/* Slide-out Citation Drawer */}
      <CitationDrawer
        isOpen={isCitationsOpen}
        onClose={() => setIsCitationsOpen(false)}
        citations={activeCitations}
        selectedCitation={selectedCitation}
        onSelectCitation={(c) => setSelectedCitation(c)}
      />

      {/* Settings & Engine Diagnostics Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        status={status}
        retrievalMode={retrievalMode}
        onChangeRetrievalMode={setRetrievalMode}
        topK={topK}
        onChangeTopK={setTopK}
        temperature={temperature}
        onChangeTemperature={setTemperature}
      />
    </div>
  );
}
