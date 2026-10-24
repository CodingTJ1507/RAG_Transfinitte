'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Sparkles, CornerDownLeft, ShieldCheck, Search, Scale, FileQuestion } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (query: string, attachedFiles?: string[]) => void;
  isLoading: boolean;
  onOpenUpload: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  onOpenUpload,
}) => {
  const [input, setInput] = useState<string>('');
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const testScenarios = [
    {
      id: 'test-1',
      label: '1️⃣ Root Cause',
      icon: <Search className="w-3 h-3 text-indigo-500" />,
      query: 'Why did payment failures begin after yesterday\'s deployment?'
    },
    {
      id: 'test-2',
      label: '2️⃣ Exact Code (PAY-401)',
      icon: <Sparkles className="w-3 h-3 text-emerald-500" />,
      query: 'Find every occurrence of error code PAY-401 and compare the affected versions.'
    },
    {
      id: 'test-3',
      label: '3️⃣ Cache Conflict',
      icon: <Scale className="w-3 h-3 text-amber-500" />,
      query: 'The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?'
    },
    {
      id: 'test-4',
      label: '4️⃣ Abstention Check',
      icon: <FileQuestion className="w-3 h-3 text-rose-500" />,
      query: 'Which engineer secretly caused the outage, and what exact line of code did they change?'
    }
  ];

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim(), attachedFiles);
    setInput('');
    setAttachedFiles([]);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="sticky bottom-0 z-10 p-4 md:p-6 bg-gradient-to-t from-[#f4f6fa] via-[#f4f6fa]/95 to-transparent">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Quick Demo Test Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs no-scrollbar">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0 pl-1">
            Judge Tests:
          </span>
          {testScenarios.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => onSendMessage(scenario.query)}
              disabled={isLoading}
              className="clay-btn px-3 py-1.5 flex items-center space-x-1.5 shrink-0 text-slate-700 hover:text-indigo-600 transition-all font-medium text-xs disabled:opacity-50"
            >
              {scenario.icon}
              <span>{scenario.label}</span>
            </button>
          ))}
        </div>

        {/* Floating Claymorphic Input Bar */}
        <div className="clay-card p-2 md:p-3 bg-white border border-white/80 transition-shadow">
          {attachedFiles.length > 0 && (
            <div className="px-3 pt-1 pb-2 flex flex-wrap gap-1.5">
              {attachedFiles.map((f, i) => (
                <span key={i} className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/50 flex items-center space-x-1">
                  <span>📎 {f}</span>
                  <button onClick={() => setAttachedFiles(attachedFiles.filter((_, idx) => idx !== i))} className="hover:text-rose-600 ml-1">×</button>
                </span>
              ))}
            </div>
          )}

          <div className="flex items-end space-x-2">
            {/* Attachment Button */}
            <button
              type="button"
              onClick={onOpenUpload}
              className="clay-btn p-2.5 text-slate-500 hover:text-indigo-600 transition-colors shrink-0"
              title="Attach or upload evidence file"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            {/* Auto-growing Textarea */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask an investigation query (e.g., 'Why did payment failures spike after 10:02 AM?')..."
              rows={1}
              disabled={isLoading}
              className="flex-1 bg-transparent border-0 resize-none outline-hidden py-2 px-1 text-sm text-slate-800 placeholder-slate-400 leading-relaxed font-normal max-h-36"
            />

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={!input.trim() || isLoading}
              className={`p-2.5 rounded-full shrink-0 transition-all ${
                input.trim() && !isLoading
                  ? 'clay-btn-primary cursor-pointer'
                  : 'bg-slate-100 text-slate-300 cursor-not-allowed'
              }`}
              title="Send investigation request"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-[11px] text-center text-slate-400 font-medium">
          TraceIQ cross-checks documents, release notes, Grafana graphs, transcripts, and microservice logs with evidence citations.
        </p>
      </div>
    </div>
  );
};
