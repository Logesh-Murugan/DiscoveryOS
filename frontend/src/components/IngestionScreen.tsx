import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle2, Loader2, AlertCircle, X, Sparkles, Layers } from 'lucide-react';
import { useReport } from '../context/ReportContext';
import type { ReportResponse } from '../types';
import { API_BASE_URL } from '../config';

const STAGES = [
  { id: 'ingest', label: 'Ingesting sources', desc: 'Parsing raw .csv and .txt feedback files...' },
  { id: 'extract', label: 'Extracting pain points', desc: 'Extracting atomic pain points & validating verbatim quotes...' },
  { id: 'cluster', label: 'Clustering themes', desc: 'Embedding texts & running HDBSCAN density clustering...' },
  { id: 'score', label: 'Scoring priority', desc: 'Computing severity, segment weights, & priority scores...' },
  { id: 'report', label: 'Generating report', desc: 'Compiling structured report & markdown summary...' },
];

export const IngestionScreen: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStageIndex, setActiveStageIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<{ stage?: string; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setReportData } = useReport();
  const navigate = useNavigate();

  // Time-based simulated progress sequence while real backend request runs
  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setActiveStageIndex((prev) => {
        if (prev < STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 3500); // Progress through stages every 3.5s visually

    return () => clearInterval(interval);
  }, [isProcessing]);

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;
    const validFiles: File[] = [];

    Array.from(selectedFiles).forEach((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext && ['txt', 'csv', 'mp3', 'wav'].includes(ext)) {
        validFiles.push(file);
      }
    });

    if (validFiles.length > 0) {
      setFiles((prev) => [...prev, ...validFiles]);
      setErrorMsg(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;

    setIsProcessing(true);
    setActiveStageIndex(0);
    setErrorMsg(null);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`${API_BASE_URL}/report/generate`, {
        method: 'POST',
        body: formData,
      });

      const data: ReportResponse = await response.json();

      if (response.ok && data.status === 'success') {
        // Allow the final stage animation to complete cleanly
        setActiveStageIndex(STAGES.length - 1);
        setTimeout(() => {
          setReportData(data);
          navigate('/dashboard');
        }, 800);
      } else {
        setErrorMsg({
          stage: data.stage || 'Pipeline',
          message: data.message || 'An error occurred during report generation.',
        });
        setIsProcessing(false);
      }
    } catch (err: any) {
      setErrorMsg({
        stage: 'Network/Server',
        message: err.message || `Failed to connect to DiscoveryOS backend at ${API_BASE_URL}.`,
      });
      setIsProcessing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 font-sans">
      {/* Header Branding */}
      <div className="w-full max-w-2xl mb-8 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-4">
          <Sparkles className="w-3.5 h-3.5" /> DiscoveryOS Intelligence Pipeline
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent mb-2">
          Feedback Ingestion
        </h1>
        <p className="text-slate-400 text-sm max-w-md mx-auto">
          Upload raw interview transcripts (.txt) or survey/support CSV files to extract, cluster, and prioritize customer pain points.
        </p>
      </div>

      {/* Main Card */}
      <div className="w-full max-w-2xl bg-slate-900/80 border border-slate-800 rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-3 text-red-400 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold uppercase tracking-wider text-xs block mb-0.5 text-red-300">
                [{errorMsg.stage} Error]
              </span>
              {errorMsg.message}
            </div>
          </div>
        )}

        {!isProcessing ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Drag and Drop Zone */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragging
                  ? 'border-indigo-500 bg-indigo-500/5 scale-[1.01]'
                  : 'border-slate-700 hover:border-slate-600 bg-slate-950/40 hover:bg-slate-950/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".txt,.csv,.mp3,.wav"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files)}
              />

              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-3">
                <Upload className="w-6 h-6" />
              </div>

              <p className="text-sm font-medium text-slate-200 mb-1">
                Drag and drop your feedback files here, or <span className="text-indigo-400 underline">browse</span>
              </p>
              <p className="text-xs text-slate-500">Supports .txt (transcripts), .csv (surveys & tickets), and .mp3/.wav (audio recordings)</p>
            </div>

            {/* Selected Files List */}
            {files.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex justify-between">
                  <span>Selected Files ({files.length})</span>
                  <button
                    type="button"
                    onClick={() => setFiles([])}
                    className="text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    Clear all
                  </button>
                </div>
                {files.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs"
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                      <span className="truncate text-slate-200 font-medium">{file.name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-500">{formatFileSize(file.size)}</span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFile(idx);
                        }}
                        className="text-slate-500 hover:text-red-400 transition-colors p-1"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Action Submit Button */}
            <button
              type="submit"
              disabled={files.length === 0}
              className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/10 ${
                files.length === 0
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer hover:shadow-indigo-500/25 active:scale-[0.99]'
              }`}
            >
              <Layers className="w-4 h-4" />
              Analyze Feedback & Generate Report
            </button>
          </form>
        ) : (
          /* Processing Stage Tracker */
          <div className="py-6 space-y-6">
            <div className="text-center mb-6">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-3 animate-pulse">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Running DiscoveryOS Pipeline</h3>
              <p className="text-xs text-slate-400 mt-1">Analyzing feedback sources across AI agents...</p>
            </div>

            {/* Step-by-step progress visualizer */}
            <div className="space-y-3 relative before:absolute before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-800">
              {STAGES.map((stage, idx) => {
                const isCompleted = idx < activeStageIndex;
                const isActive = idx === activeStageIndex;

                return (
                  <div key={stage.id} className="relative flex items-start gap-4 z-10">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                        isCompleted
                          ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400'
                          : isActive
                          ? 'bg-indigo-600 border border-indigo-400 text-white shadow-lg shadow-indigo-500/30 scale-110'
                          : 'bg-slate-900 border border-slate-800 text-slate-600'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : isActive ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        idx + 1
                      )}
                    </div>

                    <div className="pt-1">
                      <div
                        className={`text-sm font-semibold transition-colors ${
                          isActive
                            ? 'text-indigo-300'
                            : isCompleted
                            ? 'text-slate-300'
                            : 'text-slate-600'
                        }`}
                      >
                        {stage.label}
                      </div>
                      {isActive && (
                        <p className="text-xs text-slate-400 mt-0.5 animate-fadeIn">
                          {stage.desc}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
