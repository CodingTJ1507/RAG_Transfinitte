'use client';

import React, { useState } from 'react';
import { Header } from '../components/Header';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { UploadDrawer } from '../components/UploadDrawer';
import { CitationModal } from '../components/CitationModal';
import { ChatMessage as ChatMessageType, Citation, IngestedFile } from '../lib/types';
import { Plus, Settings, PanelLeftClose, PanelLeft, Sparkles } from 'lucide-react';

const INITIAL_FILES: IngestedFile[] = [
  {
    id: 'doc-1',
    name: 'service_operations_runbook_v1.8.md',
    source_type: 'document',
    size: '14.2 KB',
    uploadedAt: 'Today, 09:30 AM',
    status: 'indexed',
    chunkCount: 18
  },
  {
    id: 'web-1',
    name: 'payment_gateway_v2.4.0_release_notes.html',
    source_type: 'webpage',
    size: '8.6 KB',
    uploadedAt: 'Today, 09:32 AM',
    status: 'indexed',
    chunkCount: 12
  },
  {
    id: 'img-1',
    name: 'grafana_error_latency_spike_1011.png',
    source_type: 'image',
    size: '340 KB',
    uploadedAt: 'Today, 10:12 AM',
    status: 'indexed',
    chunkCount: 4
  },
  {
    id: 'trans-1',
    name: 'incident_warroom_call_1014am.txt',
    source_type: 'transcript',
    size: '19.5 KB',
    uploadedAt: 'Today, 10:20 AM',
    status: 'indexed',
    chunkCount: 22
  },
  {
    id: 'log-1',
    name: 'payment_service_production_logs.json',
    source_type: 'structured_record',
    size: '88.4 KB',
    uploadedAt: 'Today, 10:25 AM',
    status: 'indexed',
    chunkCount: 64
  }
];

export default function Home() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isInvestigating, setIsInvestigating] = useState<boolean>(false);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [ingestedFiles, setIngestedFiles] = useState<IngestedFile[]>(INITIAL_FILES);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);

  const pastConversations = [
    'Payment Failure Root Cause v2.4.0',
    'Error Code PAY-401 Occurrences',
    'Redis Cache vs In-Memory Architecture',
    'Blameless Outage Audit & Attribution'
  ];

  const handleSendMessage = async (query: string, attachedFiles?: string[]) => {
    const userMsgId = `user-${Date.now()}`;
    const userMessage: ChatMessageType = {
      id: userMsgId,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      attachedFiles
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsInvestigating(true);

    const startTime = Date.now();

    // Connect to live FastAPI backend at http://localhost:8000
    try {
      const response = await fetch('http://localhost:8000/api/investigate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: AbortSignal.timeout(6000) // 6s timeout
      });

      if (response.ok) {
        const liveReport = await response.json();
        const durationMs = Date.now() - startTime;
        const assistantMessage: ChatMessageType = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: liveReport.likely_root_cause || (liveReport.is_abstention ? liveReport.abstention_reason || '' : 'Investigation completed.'),
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          thinkingSteps: [
            { step: 'Atlas Vector Search', detail: 'Retrieved matching chunks from vector index.', timestamp: '0.4s' },
            { step: 'Hybrid Reciprocal Rank Fusion', detail: 'Blended semantic embeddings with exact keyword matches.', timestamp: '0.8s' },
            { step: 'Cross-Source Synthesis', detail: 'Compiled chronological timeline with grounded citations.', timestamp: '1.2s' }
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
              id: `assistant-${Date.now()}`,
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
    } catch (err: any) {
      // Clean context-aware error without leaking code or injecting sample evidence
      let errorTitle = 'Service Unreachable';
      let errorMessage = 'Unable to connect to the investigation service. Please verify your connection or try again.';

      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        errorTitle = "You're Offline";
        errorMessage = 'Please check your internet connection and try again.';
      } else if (err?.name === 'TimeoutError' || err?.name === 'AbortError') {
        errorTitle = 'Request Timed Out';
        errorMessage = 'The investigation took longer than expected to complete. Please try asking again.';
      }

      // In case of an error, strictly present the error message with a retry option — no sample evidence
      setTimeout(() => {
        const assistantErrorMessage: ChatMessageType = {
          id: `assistant-${Date.now()}`,
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

  const handleAddFiles = (newFiles: IngestedFile[]) => {
    setIngestedFiles((prev) => [...newFiles, ...prev]);
  };

  const handleRemoveFile = (id: string) => {
    setIngestedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleLoadSyntheticPack = () => {
    setIngestedFiles(INITIAL_FILES);
    setIsUploadOpen(false);
  };

  return (
    <div className="min-h-screen flex bg-white text-slate-800">
      {/* Gemini Collapsible Sidebar */}
      {isSidebarOpen && (
        <aside className="w-64 border-r border-slate-100 bg-[#f9fafb] p-3 flex flex-col justify-between shrink-0 hidden md:flex transition-all">
          <div>
            {/* Top Gemini Brand & Toggle */}
            <div className="flex items-center justify-between px-2 py-1 mb-4">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="font-semibold text-sm text-slate-800">TraceIQ</span>
              </div>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200/50"
                title="Collapse sidebar"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>

            {/* New Chat Button */}
            <button
              onClick={handleResetChat}
              className="w-full flex items-center space-x-2 px-3 py-2 rounded-full bg-slate-200/60 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors mb-5"
            >
              <Plus className="w-4 h-4 text-slate-600" />
              <span>New investigation</span>
            </button>

            {/* Recent Chats Section */}
            <div className="px-2">
              <span className="text-[11px] font-medium text-slate-400 block mb-2">Recent</span>
              <div className="space-y-1">
                {pastConversations.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(item)}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg hover:bg-slate-200/50 text-xs text-slate-700 truncate block transition-colors font-normal"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* User Profile Footer */}
          <div className="border-t border-slate-200/60 pt-3 px-2 flex items-center justify-between">
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-amber-500 text-white flex items-center justify-center font-bold text-xs shrink-0">
                T
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-800 truncate">Tanishq</p>
                <p className="text-[10px] text-slate-400">Pro</p>
              </div>
            </div>
            <button className="p-1 text-slate-400 hover:text-slate-600 rounded-lg">
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
              className="p-2 ml-3 text-slate-400 hover:text-slate-600 rounded-lg hidden md:block"
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
          {messages.length === 0 ? (
            /* Gemini Welcome Screen */
            <div className="my-auto py-10 max-w-xl mx-auto text-center space-y-3">
              <h2 className="text-2xl md:text-3xl font-semibold text-slate-800 tracking-tight">
                Investigate with Evidence
              </h2>
              <p className="text-sm text-slate-500 leading-relaxed max-w-md mx-auto">
                Connect documents, changelogs, images, meeting transcripts, and structured logs into cited incident findings.
              </p>

              {/* Starter Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-6 text-left">
                <button
                  onClick={() => handleSendMessage("Why did payment failures begin after yesterday's deployment?")}
                  className="p-3 rounded-xl border border-slate-200/80 hover:bg-slate-50 transition-colors text-xs text-slate-700"
                >
                  <span className="font-semibold block text-slate-900 mb-0.5">Why did payments fail?</span>
                  <span className="text-slate-400 text-[11px]">Connects logs, v2.4.0 notes, and transcript.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('Find every occurrence of error code PAY-401 and compare the affected versions.')}
                  className="p-3 rounded-xl border border-slate-200/80 hover:bg-slate-50 transition-colors text-xs text-slate-700"
                >
                  <span className="font-semibold block text-slate-900 mb-0.5">Error PAY-401 occurrences</span>
                  <span className="text-slate-400 text-[11px]">Exact keyword search across versions.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?')}
                  className="p-3 rounded-xl border border-slate-200/80 hover:bg-slate-50 transition-colors text-xs text-slate-700"
                >
                  <span className="font-semibold block text-slate-900 mb-0.5">Redis vs In-Memory cache</span>
                  <span className="text-slate-400 text-[11px]">Detects contradictory documentation.</span>
                </button>

                <button
                  onClick={() => handleSendMessage('Which engineer secretly caused the outage, and what exact line of code did they change?')}
                  className="p-3 rounded-xl border border-slate-200/80 hover:bg-slate-50 transition-colors text-xs text-slate-700"
                >
                  <span className="font-semibold block text-slate-900 mb-0.5">Outage code blame audit</span>
                  <span className="text-slate-400 text-[11px]">Tests evidence-based abstention.</span>
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
