'use client';

import React, { useState } from 'react';
import { IngestedFile, SourceType } from '../lib/types';
import { getSourceIcon, getSourceBadge } from './CitationCard';
import { X, Upload, Plus, FileText, CheckCircle2, Trash2, Sparkles, FolderSync } from 'lucide-react';

interface UploadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  files: IngestedFile[];
  onAddFiles: (newFiles: IngestedFile[]) => void;
  onRemoveFile: (id: string) => void;
  onLoadSyntheticPack: () => void;
}

export const UploadDrawer: React.FC<UploadDrawerProps> = ({
  isOpen,
  onClose,
  files,
  onAddFiles,
  onRemoveFile,
  onLoadSyntheticPack
}) => {
  const [selectedType, setSelectedType] = useState<SourceType | 'all'>('all');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleManualUpload(Array.from(e.dataTransfer.files));
    }
  };

  const handleManualUpload = (uploaded: File[]) => {
    setIsIngesting(true);
    setTimeout(() => {
      const newItems: IngestedFile[] = uploaded.map((f, i) => {
        let type: SourceType = 'document';
        if (f.name.endsWith('.json') || f.name.endsWith('.csv') || f.name.endsWith('.log')) type = 'structured_record';
        else if (f.name.endsWith('.png') || f.name.endsWith('.jpg') || f.name.endsWith('.svg')) type = 'image';
        else if (f.name.endsWith('.html') || f.name.endsWith('.url')) type = 'webpage';
        else if (f.name.includes('transcript') || f.name.includes('meeting')) type = 'transcript';

        return {
          id: `upload-${Date.now()}-${i}`,
          name: f.name,
          source_type: type,
          size: `${(f.size / 1024).toFixed(1)} KB`,
          uploadedAt: 'Just now',
          status: 'indexed',
          chunkCount: Math.max(3, Math.floor(f.size / 400))
        };
      });
      onAddFiles(newItems);
      setIsIngesting(false);
    }, 1200);
  };

  const filteredFiles = selectedType === 'all' 
    ? files 
    : files.filter(f => f.source_type === selectedType);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/20 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md bg-white border-l border-slate-200 shadow-2xl h-full flex flex-col justify-between p-6 overflow-y-auto animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Drawer Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-800 flex items-center space-x-2">
                <span>Multi-Source Evidence Pack</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Ingested sources indexed in MongoDB Atlas
              </p>
            </div>
            <button
              onClick={onClose}
              className="clay-btn p-1.5 text-slate-400 hover:text-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Demo Pack Loader */}
          <div className="mt-4 p-3.5 rounded-2xl bg-gradient-to-r from-indigo-50 to-indigo-100/60 border border-indigo-200/60 clay-card-sm">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-xs font-bold text-indigo-900 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Hackathon Incident Pack</span>
                </h4>
                <p className="text-[11px] text-indigo-700/80 mt-1 leading-relaxed">
                  Load all 5 multi-source evidence files (Payment logs, Runbook, v2.4.0 notes, Grafana spike, War-room audio).
                </p>
              </div>
            </div>
            <button
              onClick={onLoadSyntheticPack}
              className="mt-2.5 clay-btn-primary px-3 py-1.5 text-xs font-semibold w-full flex items-center justify-center space-x-1.5"
            >
              <FolderSync className="w-3.5 h-3.5" />
              <span>Load 5 Multi-Source Evidence Files</span>
            </button>
          </div>

          {/* Upload Dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`mt-4 border-2 border-dashed rounded-2xl p-4 text-center transition-all ${
              dragActive ? 'border-indigo-500 bg-indigo-50/50 scale-[1.01]' : 'border-slate-200 bg-slate-50/50 hover:bg-slate-50'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && handleManualUpload(Array.from(e.target.files))}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <Upload className="w-6 h-6 text-indigo-500 mx-auto mb-1.5 animate-bounce" />
              <p className="text-xs font-bold text-slate-700">
                {isIngesting ? 'Ingesting & Chunking...' : 'Upload your own evidence files'}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                PDFs, Markdown, JSON logs, Grafana PNGs, Transcripts
              </p>
            </label>
          </div>

          {/* Source Type Filter Chips */}
          <div className="mt-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                Indexed Sources ({filteredFiles.length})
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(['all', 'document', 'webpage', 'image', 'transcript', 'structured_record'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedType(t)}
                  className={`text-[10px] font-semibold px-2.5 py-1 rounded-full border transition-all ${
                    selectedType === t
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                      : 'bg-white text-slate-600 border-slate-200/70 hover:border-slate-300'
                  }`}
                >
                  {t === 'all' ? 'All Sources' : t.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Ingested File List */}
          <div className="mt-3.5 space-y-2 max-h-72 overflow-y-auto pr-1">
            {filteredFiles.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-400 italic">
                No sources matching filter.
              </div>
            ) : (
              filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="clay-card-sm p-2.5 flex items-center justify-between group hover:border-indigo-200 transition-all"
                >
                  <div className="flex items-center space-x-2.5 min-w-0">
                    <span className="p-1.5 rounded-lg bg-slate-50 border border-slate-200 shrink-0">
                      {getSourceIcon(file.source_type)}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-800 truncate">
                        {file.name}
                      </p>
                      <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-0.5">
                        <span className={`px-1.5 py-0.2 rounded-md font-semibold border ${getSourceBadge(file.source_type)} uppercase text-[9px]`}>
                          {file.source_type.replace('_', ' ')}
                        </span>
                        <span>•</span>
                        <span>{file.chunkCount} chunks</span>
                        <span>•</span>
                        <span>{file.size}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0">
                    <span className="flex items-center text-emerald-600 text-[10px] font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-0.5" />
                    </span>
                    <button
                      onClick={() => onRemoveFile(file.id)}
                      className="p-1 text-slate-300 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100"
                      title="Remove source"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Bottom Drawer Close */}
        <div className="pt-4 border-t border-slate-100 mt-4">
          <button
            onClick={onClose}
            className="clay-btn w-full py-2 text-xs font-semibold text-slate-700 hover:text-indigo-600 transition-colors"
          >
            Close Evidence Drawer
          </button>
        </div>
      </div>
    </div>
  );
};
