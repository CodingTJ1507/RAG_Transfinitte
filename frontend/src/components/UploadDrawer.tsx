'use client';

import React, { useState } from 'react';
import { IngestedFile, SourceType } from '../lib/types';
import { getSourceTypeLabel } from './CitationCard';
import { X, Upload, Trash2, FolderSync } from 'lucide-react';

interface UploadDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  files: IngestedFile[];
  onAddFiles: (files: File[]) => Promise<void>;
  onRemoveFile: (id: string) => void | Promise<void>;
  onLoadSyntheticPack: () => Promise<void>;
}

export const UploadDrawer: React.FC<UploadDrawerProps> = ({
  isOpen,
  onClose,
  files,
  onAddFiles,
  onRemoveFile,
  onLoadSyntheticPack,
}) => {
  const [selectedType, setSelectedType] = useState<SourceType | 'all'>('all');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [loadingPack, setLoadingPack] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleRemove = async (id: string) => {
    setUploadError(null);
    try {
      await onRemoveFile(id);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Could not remove source.');
    }
  };

  const handleManualUpload = async (uploadedFiles: File[]) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      await onAddFiles(uploadedFiles);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Could not index the selected file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadPack = async () => {
    setUploadError(null);
    setLoadingPack(true);
    try {
      await onLoadSyntheticPack();
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Could not index the demo evidence pack.');
    } finally {
      setLoadingPack(false);
    }
  };

  const filteredFiles = selectedType === 'all' 
    ? files 
    : files.filter(f => f.source_type === selectedType);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/35 backdrop-blur-2xs animate-in fade-in duration-150">
      <div 
        className="w-full max-w-md bg-[#ffffff] border-l border-[#dde4ec] h-full flex flex-col justify-between p-6 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-[#dde4ec]">
            <div>
              <h2 className="text-base font-bold text-[#162748]">
                Evidence Collection
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Indexed in MongoDB Atlas
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-[#162748] hover:bg-[#eaf0f6] rounded-full transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Demo Pack Loader */}
          <div className="mt-4 p-3.5 rounded-xl bg-[#eef2f6] border border-[#dde4ec] shadow-2xs">
            <h4 className="text-xs font-bold text-[#162748]">
              Demo Incident Evidence Pack
            </h4>
            <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">
              Load the 20 evidence files for incident INC-2026-1042.
            </p>
            <button
              onClick={() => void handleLoadPack()}
              disabled={loadingPack || isUploading}
              className="mt-2.5 px-3 py-1.5 text-xs font-semibold bg-[#162748] text-white hover:bg-[#1f3660] hover:shadow-[0_0_12px_rgba(9,190,193,0.3)] rounded-lg w-full flex items-center justify-center space-x-1.5 transition-all cursor-pointer"
            >
              <FolderSync className="w-3.5 h-3.5 text-[#09bec1]" />
              <span>{loadingPack ? 'Indexing evidence pack…' : 'Load incident evidence pack'}</span>
            </button>
          </div>

          {/* Upload Area */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              if (e.dataTransfer.files) void handleManualUpload(Array.from(e.dataTransfer.files));
            }}
            className={`mt-4 border border-dashed rounded-xl p-4 text-center transition-all ${
              dragActive ? 'border-[#09bec1] bg-[#eaf0f6]' : 'border-[#d4dee8] bg-[#f8fafc] hover:border-[#09bec1]'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              multiple
              accept=".pdf,.docx,.md,.html,.htm,.vtt,.txt,.json,.csv,.png,.jpg,.jpeg,.webp"
              className="hidden"
              disabled={isUploading || loadingPack}
              onChange={(e) => {
                if (e.target.files) void handleManualUpload(Array.from(e.target.files));
                e.target.value = '';
              }}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <Upload className="w-5 h-5 text-slate-400 mx-auto mb-1" />
              <p className="text-xs font-semibold text-[#162748]">
                {isUploading ? 'Uploading and indexing…' : 'Upload evidence files'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">PDF, DOCX, Markdown, HTML, VTT, text, JSON, CSV, PNG</p>
            </label>
          </div>
          {uploadError && (
            <p className="mt-2 text-xs text-rose-600 font-medium" role="alert">{uploadError}</p>
          )}

          {/* Category Filter Chips */}
          <div className="mt-4 flex flex-wrap gap-1.5">
            {(['all', 'document', 'webpage', 'image', 'transcript', 'structured_record'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`text-[11px] font-medium px-2.5 py-1 rounded-full border transition-all cursor-pointer ${
                  selectedType === t
                    ? 'bg-[#162748] text-white border-[#162748]'
                    : 'bg-[#eaf0f6] text-[#162748] border-[#d4dee8] hover:border-[#09bec1]/40 hover:bg-[#dce6f0]'
                }`}
              >
                {t === 'all' ? 'All' : t.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Ingested File List */}
          <div className="mt-3 space-y-1.5 max-h-72 overflow-y-auto pr-1">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                className="p-2.5 rounded-lg border border-[#dde4ec] hover:bg-[#eef2f6] flex items-center justify-between group transition-colors shadow-2xs"
              >
                <div className="min-w-0">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-[9px] font-semibold text-[#087f82] bg-[#09bec1]/10 px-1 py-0.2 rounded border border-[#09bec1]/25">
                      {getSourceTypeLabel(file.source_type)}
                    </span>
                    <p className="text-xs font-medium text-[#162748] truncate">
                      {file.name}
                    </p>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5 pl-6">
                    {file.chunkCount} chunks • {file.size}
                  </p>
                </div>

                <button
                  onClick={() => void handleRemove(file.id)}
                  className="p-1 text-slate-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                  title="Remove"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-4 border-t border-[#dde4ec] mt-4">
          <button
            onClick={onClose}
            className="w-full py-2 text-xs font-semibold text-[#162748] bg-[#eaf0f6] hover:bg-[#dce6f0] rounded-lg transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
