import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useReport } from '../context/ReportContext';
import { FileText, ArrowLeft, CheckCircle2, Cpu } from 'lucide-react';

export const DashboardPlaceholder: React.FC = () => {
  const { reportData } = useReport();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors bg-slate-900 border border-slate-800 px-3.5 py-2 rounded-xl"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Ingestion
          </button>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" /> Pipeline Completed
          </span>
        </div>

        {/* Hero Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
          <div className="flex items-start justify-between">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">
                <Cpu className="w-4 h-4" /> DiscoveryOS Analysis Snapshot
              </div>
              <h1 className="text-3xl font-extrabold text-slate-100">Report Dashboard Placeholder</h1>
              <p className="text-slate-400 text-sm mt-1">
                Report generated successfully from backend pipeline.
              </p>
            </div>
            {reportData?.report && (
              <div className="text-right bg-slate-950/60 border border-slate-800 p-3 rounded-xl text-xs space-y-1">
                <div className="text-slate-400">ID: <span className="text-slate-200 font-mono">{reportData.report.id}</span></div>
                <div className="text-slate-400">Version: <span className="text-slate-200">{reportData.report.version}</span></div>
                <div className="text-slate-400">Themes: <span className="text-slate-200">{reportData.report.theme_ids.length}</span></div>
              </div>
            )}
          </div>
        </div>

        {/* Markdown Preview Section */}
        {reportData?.markdown ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" /> Generated Report Markdown
              </h2>
              <span className="text-xs text-slate-500 font-mono">Raw output</span>
            </div>

            <pre className="bg-slate-950 p-6 rounded-xl text-xs text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed border border-slate-800/80">
              {reportData.markdown}
            </pre>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-sm">
            No report data loaded. Upload files from the ingestion screen first.
          </div>
        )}
      </div>
    </div>
  );
};
