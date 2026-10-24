'use client';

import React, { useState } from 'react';
import { Header } from '../components/Header';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { UploadDrawer } from '../components/UploadDrawer';
import { CitationModal } from '../components/CitationModal';
import { ChatMessage as ChatMessageType, Citation, IngestedFile } from '../lib/types';
import { Plus, Settings, PanelLeftClose, PanelLeft, Sparkles } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

interface SourceRecord {
  source_id: string;
  title: string;
  source_type: IngestedFile['source_type'];
  size_bytes?: number;
  chunk_count?: number;
  updated_at?: string;
  created_at?: string;
}

interface SourceListResponse {
  sources: SourceRecord[];
}

interface UploadResponse {
  source: SourceRecord;
}

function mapSourceToFile(source: SourceRecord): IngestedFile {
  const size = source.size_bytes ?? 0;
  return {
    id: source.source_id,
    name: source.title,
    source_type: source.source_type,
    size: size ? `${(size / 1024).toFixed(1)} KB` : '—',
    uploadedAt: formatIndexedAt(source.updated_at ?? source.created_at ?? 'Indexed'),
    status: 'indexed',
    chunkCount: source.chunk_count ?? 0,
  };
}

function sourceTypeForFile(file: File): IngestedFile['source_type'] {
  const extension = file.name.split('.').pop()?.toLowerCase();
  if (['html', 'htm'].includes(extension ?? '')) return 'webpage';
  if (['png', 'jpg', 'jpeg', 'webp'].includes(extension ?? '')) return 'image';
  if (['json', 'csv'].includes(extension ?? '')) return 'structured_record';
  if (extension === 'vtt' || extension === 'txt') return 'transcript';
  return 'document';
}

function formatIndexedAt(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [ingestedFiles, setIngestedFiles] = useState<IngestedFile[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [sourceTypeFilter, setSourceTypeFilter] = useState('');
  const [versionFilter, setVersionFilter] = useState('');
  const [ownerFilter, setOwnerFilter] = useState('');
  const [timeStartFilter, setTimeStartFilter] = useState('');
  const [timeEndFilter, setTimeEndFilter] = useState('');

  const pastConversations = [
    'Payment Failure Root Cause v2.4.0',
    'Error Code PAY-401 Occurrences',
    'Redis Cache vs In-Memory Architecture',
    'Blameless Outage Audit & Attribution'
  ];

  const handleSendMessage = async (query: string, attachedFiles?: string[]) => {
    const userMsgId = `user-${crypto.randomUUID()}`;
    const userMessage: ChatMessageType = {
      id: userMsgId,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachedFiles
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsInvestigating(true);

    const startTime = new Date().getTime();

    // Connect to live FastAPI backend at http://localhost:8000
    try {
      const response = await fetch(`${API_BASE_URL}/api/investigate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          incident_id: 'INC-2026-1042',
          source_types: sourceTypeFilter ? [sourceTypeFilter] : undefined,
          version: versionFilter || undefined,
          owner: ownerFilter || undefined,
          time_range_start: timeStartFilter ? new Date(timeStartFilter).toISOString() : undefined,
          time_range_end: timeEndFilter ? new Date(timeEndFilter).toISOString() : undefined,
        }),
        signal: AbortSignal.timeout(120000)
      });

      if (response.ok) {
        const liveReport = await response.json();
        const durationMs = new Date().getTime() - startTime;
        const assistantMessage: ChatMessageType = {
          id: `assistant-${crypto.randomUUID()}`,
          role: 'assistant',
          content: liveReport.likely_root_cause || (liveReport.is_abstention ? liveReport.abstention_reason || '' : 'Investigation completed.'),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          thinkingSteps: [
            {
              step: 'Query planning',
              detail: `${liveReport.retrieval_diagnostics?.query_variants?.length ?? 1} query variant(s) prepared.`,
              timestamp: 'complete',
            },
            {
              step: 'Atlas hybrid retrieval',
              detail: 'Searched vector, BM25, and exact identifier indexes with the selected metadata filters.',
              timestamp: 'complete',
            },
            {
              step: 'Claim verification',
              detail: `${liveReport.claims?.filter((claim: { verification_status?: string }) => claim.verification_status === 'verified').length ?? 0} claim(s) independently verified against cited evidence.`,
              timestamp: `${durationMs} ms`,
            },
          ],
          thinkingDurationMs: durationMs,
          report: liveReport,
          rawQuery: query
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setIsInvestigating(false);
        return;
      } else {
        // Specific HTTP error handling
        let errTitle = 'Service Error';
        let errMsg = 'The service encountered an issue processing your request. Please try again.';

        if (response.status === 429) {
          errTitle = 'Service Busy';
          errMsg = 'Too many requests at this moment. Please wait a moment before trying again.';
        } else if (response.status === 400 || response.status === 422) {
          errTitle = 'Unable to Process Query';
          errMsg = 'We could not process this question as formatted. Please try rephrasing your request.';
        } else if (response.status >= 500) {
          errTitle = 'Service Temporarily Unavailable';
          errMsg = 'An unexpected server error occurred while analyzing the incident evidence. Please try again shortly.';
        }

        setTimeout(() => {
          setMessages((prev) => [
            ...prev,
            {
              id: `assistant-${crypto.randomUUID()}`,
              role: 'assistant',
              content: errMsg,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              isError: true,
              errorTitle: errTitle,
              rawQuery: query
            }
          ]);
          setIsInvestigating(false);
        }, 500);
        return;
      }
    } catch (err: unknown) {
      // Clean context-aware error without leaking code or injecting sample evidence
      let errorTitle = 'Service Unreachable';
      let errorMessage = 'Unable to connect to the investigation service. Please verify your connection or try again.';

      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        errorTitle = "You're Offline";
        errorMessage = 'Please check your internet connection and try again.';
      } else if (err instanceof Error && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
        errorTitle = 'Request Timed Out';
        errorMessage = 'The investigation took longer than expected to complete. Please try asking again.';
      }

      // In case of an error, strictly present the error message with a retry option — no sample evidence
      setTimeout(() => {
        const assistantErrorMessage: ChatMessageType = {
          id: `assistant-${crypto.randomUUID()}`,
          role: 'assistant',
          content: errorMessage,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true,
          errorTitle: errorTitle,
          rawQuery: query
        };
        setMessages((prev) => [...prev, assistantErrorMessage]);
        setIsInvestigating(false);
      }, 500);
    }
  };

  const handleResetChat = () => {
    setMessages([]);
  };

  const handleAddFiles = async (newFiles: File[]) => {
    for (const file of newFiles) {
      const form = new FormData();
      form.append('file', file);
      form.append('source_type', sourceTypeForFile(file));
      form.append('incident_id', 'INC-2026-1042');
      const response = await fetch(`${API_BASE_URL}/api/ingest/upload`, {
        method: 'POST',
        body: form,
        signal: AbortSignal.timeout(120000),
      });
      if (!response.ok) {
        const message = response.status === 413
          ? 'The file exceeds the server upload limit.'
          : 'The backend could not index this file. Check the file format and service readiness.';
        throw new Error(message);
      }
      const payload = await response.json() as UploadResponse;
      const indexedFile = mapSourceToFile(payload.source);
      setIngestedFiles((previous) => [
        indexedFile,
        ...previous.filter((existing) => existing.id !== indexedFile.id),
      ]);
    }
  };

  const handleRemoveFile = (id: string) => {
    setIngestedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleLoadSyntheticPack = async () => {
    const response = await fetch(`${API_BASE_URL}/api/ingest/batch?incident_id=INC-2026-1042`, {
      method: 'POST',
      signal: AbortSignal.timeout(120000),
    });
    if (!response.ok) {
      throw new Error('Could not index the demo evidence pack. Check backend, Gemini, and Atlas readiness.');
    }
    const sourcesResponse = await fetch(
      `${API_BASE_URL}/api/ingest/sources?incident_id=INC-2026-1042`,
      { signal: AbortSignal.timeout(30000) },
    );
    if (!sourcesResponse.ok) {
      throw new Error('The evidence pack was indexed, but the source list could not be refreshed.');
    }
    const payload = await sourcesResponse.json() as SourceListResponse;
    setIngestedFiles(payload.sources.map(mapSourceToFile));
    setIsUploadOpen(false);
  };

  return (
    <div className="min-h-screen flex bg-[#f7f5f0] text-stone-800">
      {/* Gemini Collapsible Sidebar */}
      {isSidebarOpen && (
        <aside className="w-64 border-r border-[#ded9cf]/80 bg-[#efebe4] p-3 flex flex-col justify-between shrink-0 hidden md:flex transition-all">
          <div>
            {/* Top Gemini Brand & Toggle */}
            <div className="flex items-center justify-between px-2 py-1 mb-4">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="font-semibold text-sm text-stone-800">TraceIQ</span>
              </div>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="p-1 text-stone-400 hover:text-stone-700 rounded-lg hover:bg-stone-300/50 cursor-pointer"
                title="Collapse sidebar"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* New Chat Button */}
            <button
              onClick={handleResetChat}
              className="w-full flex items-center space-x-2 px-3 py-2 rounded-full bg-[#e2ded5] hover:bg-[#d8d3c8] text-stone-700 text-xs font-medium transition-colors mb-5 cursor-pointer"
            >
              <Plus className="w-4 h-4 text-stone-600" />
              <span>New investigation</span>
            </button>

            {/* Recent Chats Section */}
            <div className="px-2">
              <span className="text-[11px] font-medium text-stone-500 block mb-2">Recent</span>
              <div className="space-y-1">
                {pastConversations.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(item)}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-stone-300/50 text-xs text-stone-700 truncate block transition-colors font-normal cursor-pointer"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* User Profile Footer */}
          <div className="border-t border-[#ded9cf]/80 pt-3 px-2 flex items-center justify-between">
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-amber-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                T
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-stone-800 truncate">Tanishq</p>
                <p className="text-[10px] text-stone-500">Pro</p>
              </div>
            </div>
            <button className="p-1 text-stone-400 hover:text-stone-700 rounded-lg cursor-pointer">
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </aside>
      )}

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Minimal Header */}
        <div className="flex items-center">
          {!isSidebarOpen && (
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 ml-3 text-stone-400 hover:text-stone-700 rounded-lg hidden md:block cursor-pointer"
              title="Expand sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
          <div className="flex-1">
            <Header
              onOpenUpload={() => setIsUploadOpen(true)}
              onResetChat={handleResetChat}
              ingestedFileCount={ingestedFiles.length}
            />
          </div>
        </div>

        {/* Chat Stream */}
        <main className="flex-1 max-w-3xl w-full mx-auto px-4 md:px-6 pt-6 flex flex-col justify-between">
          <section
            aria-label="Evidence filters"
            className="mb-4 grid grid-cols-2 md:grid-cols-5 gap-2 rounded-xl border border-[#ded9cf] bg-[#efebe4] p-3"
          >
            <label className="text-[10px] font-medium text-stone-500">
              Source type
              <select
                value={sourceTypeFilter}
                onChange={(event) => setSourceTypeFilter(event.target.value)}
                className="mt-1 w-full rounded-lg border border-stone-300 bg-[#faf8f5] px-2 py-1.5 text-xs text-stone-700"
              >
                <option value="">All types</option>
                <option value="document">Documents</option>
                <option value="webpage">Webpages</option>
                <option value="image">Images</option>
                <option value="transcript">Transcripts</option>
                <option value="structured_record">Structured records</option>
              </select>
            </label>
            <label className="text-[10px] font-medium text-stone-500">
              Version
              <input
                value={versionFilter}
                onChange={(event) => setVersionFilter(event.target.value)}
                placeholder="Any version"
                className="mt-1 w-full rounded-lg border border-stone-300 bg-[#faf8f5] px-2 py-1.5 text-xs text-stone-700"
              />
            </label>
            <label className="text-[10px] font-medium text-stone-500">
              Owner
              <input
                value={ownerFilter}
                onChange={(event) => setOwnerFilter(event.target.value)}
                placeholder="Any owner"
                className="mt-1 w-full rounded-lg border border-stone-300 bg-[#faf8f5] px-2 py-1.5 text-xs text-stone-700"
              />
            </label>
            <label className="text-[10px] font-medium text-stone-500">
              From
              <input
                type="datetime-local"
                value={timeStartFilter}
                onChange={(event) => setTimeStartFilter(event.target.value)}
                className="mt-1 w-full rounded-lg border border-stone-300 bg-[#faf8f5] px-2 py-1.5 text-xs text-stone-700"
              />
            </label>
            <label className="text-[10px] font-medium text-stone-500">
              To
              <input
                type="datetime-local"
                value={timeEndFilter}
                onChange={(event) => setTimeEndFilter(event.target.value)}
                className="mt-1 w-full rounded-lg border border-stone-300 bg-[#faf8f5] px-2 py-1.5 text-xs text-stone-700"
              />
            </label>
          </section>
          {messages.length === 0 ? (
            /* Gemini Welcome Screen */
            <div className="my-auto py-10 max-w-xl mx-auto text-center space-y-3">
              <h2 className="text-2xl md:text-3xl font-semibold text-stone-800 tracking-tight">
                Investigate with Evidence
              </h2>
              <p className="text-sm text-stone-600 leading-relaxed max-w-md mx-auto">
                Connect documents, changelogs, images, meeting transcripts, and structured logs into cited incident findings.
              </p>

              {/* Starter Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-6 text-left">
                <button
                  onClick={() => handleSendMessage("Why did payment failures begin after yesterday's deployment?")}
                  className="p-3 rounded-xl bg-[#efebe3] border border-[#ded9cf] hover:bg-[#e6e1d7] transition-colors text-xs text-stone-700 cursor-pointer shadow-2xs"
                >
                  <span className="font-semibold block text-stone-900 mb-0.5">Why did payments fail?</span>
                  <span className="text-stone-500 text-[11px]">Connects logs, v2.4.0 notes, and transcript.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('Find every occurrence of error code PAY-401 and compare the affected versions.')}
                  className="p-3 rounded-xl bg-[#efebe3] border border-[#ded9cf] hover:bg-[#e6e1d7] transition-colors text-xs text-stone-700 cursor-pointer shadow-2xs"
                >
                  <span className="font-semibold block text-stone-900 mb-0.5">Error PAY-401 occurrences</span>
                  <span className="text-stone-500 text-[11px]">Exact keyword search across versions.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?')}
                  className="p-3 rounded-xl bg-[#efebe3] border border-[#ded9cf] hover:bg-[#e6e1d7] transition-colors text-xs text-stone-700 cursor-pointer shadow-2xs"
                >
                  <span className="font-semibold block text-stone-900 mb-0.5">Redis vs In-Memory cache</span>
                  <span className="text-stone-500 text-[11px]">Detects contradictory documentation.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('Which engineer secretly caused the outage, and what exact line of code did they change?')}
                  className="p-3 rounded-xl bg-[#efebe3] border border-[#ded9cf] hover:bg-[#e6e1d7] transition-colors text-xs text-stone-700 cursor-pointer shadow-2xs"
                >
                  <span className="font-semibold block text-stone-900 mb-0.5">Outage code blame audit</span>
                  <span className="text-stone-500 text-[11px]">Tests evidence-based abstention.</span>
                </button>
              </div>
            </div>
          ) : (
            /* Stream of Messages */
            <div className="space-y-4 pb-16">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onInspectCitation={(citation) => setSelectedCitation(citation)}
                  onRetry={(q) => handleSendMessage(q)}
                />
              ))}

              {isInvestigating && (
                <ChatMessage
                  message={{
                    id: 'streaming-temp',
                    role: 'assistant',
                    content: '',
                    timestamp: 'Just now'
                  }}
                  isStreaming={true}
                  onInspectCitation={() => {}}
                />
              )}
            </div>
          )}
        </main>

        {/* Gemini Pill Input Bar */}
        <ChatInput
          onSendMessage={(q, files) => handleSendMessage(q, files)}
          isLoading={isInvestigating}
          onOpenUpload={() => setIsUploadOpen(true)}
        />

        {/* Upload & Evidence Drawer */}
        <UploadDrawer
          isOpen={isUploadOpen}
          onClose={() => setIsUploadOpen(false)}
          files={ingestedFiles}
          onAddFiles={handleAddFiles}
          onRemoveFile={handleRemoveFile}
          onLoadSyntheticPack={handleLoadSyntheticPack}
        />

        {/* Citation Detail Inspector */}
        <CitationModal
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      </div>
    </div>
  );
}
