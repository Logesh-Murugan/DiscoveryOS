import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useReport } from '../context/ReportContext';
import {
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  FileText,
  Filter,
  Layers,
  Lightbulb,
  Quote,
  Sparkles,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react';
import type { Theme, PainPointUnit } from '../types';
import { ReportChatPanel } from './ReportChatPanel';

export const DashboardScreen: React.FC = () => {
  const { reportData } = useReport();
  const navigate = useNavigate();

  const [selectedSegment, setSelectedSegment] = useState<string>('All');
  const [expandedThemeIds, setExpandedThemeIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'themes' | 'markdown'>('themes');

  const themes: Theme[] = useMemo(() => {
    if (!reportData?.themes) return [];
    // Defensively sort by priority_score descending
    return [...reportData.themes].sort((a, b) => b.priority_score - a.priority_score);
  }, [reportData?.themes]);

  const painPointsLookup: Record<string, PainPointUnit> = useMemo(() => {
    if (!reportData?.pain_points) return {};
    const map: Record<string, PainPointUnit> = {};
    reportData.pain_points.forEach((pp) => {
      map[pp.id] = pp;
    });
    return map;
  }, [reportData?.pain_points]);

  // Extract unique segment names from themes
  const availableSegments = useMemo(() => {
    const segs = new Set<string>();
    themes.forEach((t) => {
      Object.keys(t.segment_breakdown).forEach((s) => segs.add(s));
    });
    return Array.from(segs);
  }, [themes]);

  // Filter themes based on selected segment
  const filteredThemes = useMemo(() => {
    if (selectedSegment === 'All') return themes;
    return themes.filter((t) => (t.segment_breakdown[selectedSegment] || 0) > 0);
  }, [themes, selectedSegment]);

  const toggleThemeExpand = (themeId: string) => {
    setExpandedThemeIds((prev) => {
      const next = new Set(prev);
      if (next.has(themeId)) {
        next.delete(themeId);
      } else {
        next.add(themeId);
      }
      return next;
    });
  };

  const getSegmentBadgeColor = (segment: string) => {
    switch (segment.toLowerCase()) {
      case 'enterprise':
        return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300';
      case 'smb':
        return 'bg-sky-500/10 border-sky-500/30 text-sky-300';
      case 'free':
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
      default:
        return 'bg-amber-500/10 border-amber-500/30 text-amber-300';
    }
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'severe':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-red-500/20 text-red-300 border border-red-500/30 uppercase">Severe</span>;
      case 'moderate':
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">Moderate</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 uppercase">Mild</span>;
    }
  };

  if (!reportData || (!reportData.themes && !reportData.markdown)) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 font-sans">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-10 max-w-md text-center shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4">
            <Layers className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold mb-2">No Report Loaded</h2>
          <p className="text-slate-400 text-sm mb-6">
            Please upload feedback files from the ingestion screen to run the pipeline.
          </p>
          <button
            onClick={() => navigate('/')}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" /> Go to Ingestion
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Top Navbar Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
              title="Back to Ingestion"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" /> DiscoveryOS Priority Intelligence
              </div>
              <h1 className="text-2xl font-extrabold text-slate-100">Feedback Analysis Dashboard</h1>
            </div>
          </div>

          {/* Header Metadata Pill */}
          {reportData.report && (
            <div className="flex items-center gap-4 bg-slate-900 border border-slate-800/90 rounded-xl px-4 py-2 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Report ID</span>
                <span className="font-mono text-slate-300 font-semibold">{reportData.report.id}</span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Themes</span>
                <span className="text-slate-200 font-bold">{themes.length}</span>
              </div>
              <div className="h-6 w-px bg-slate-800" />
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Pain Points</span>
                <span className="text-slate-200 font-bold">{reportData.pain_points?.length || 0}</span>
              </div>
            </div>
          )}
        </div>

        {/* Controls Bar: View Toggle & Segment Filter */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Tabs */}
          <div className="flex p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setActiveTab('themes')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'themes'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <TrendingUp className="w-3.5 h-3.5" /> Ranked Themes ({filteredThemes.length})
            </button>
            <button
              onClick={() => setActiveTab('markdown')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'markdown'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> Raw Markdown Report
            </button>
          </div>

          {/* Segment Filter (Only shown on themes tab) */}
          {activeTab === 'themes' && availableSegments.length > 0 && (
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-400 font-medium">Segment:</span>
              <div className="flex gap-1 overflow-x-auto">
                <button
                  onClick={() => setSelectedSegment('All')}
                  className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                    selectedSegment === 'All'
                      ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  All
                </button>
                {availableSegments.map((seg) => (
                  <button
                    key={seg}
                    onClick={() => setSelectedSegment(seg)}
                    className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                      selectedSegment === seg
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {seg}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main Content Area */}
        {activeTab === 'themes' ? (
          <div className="space-y-4">
            {filteredThemes.length === 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-sm">
                No themes match the selected segment filter: <span className="font-semibold text-slate-300">{selectedSegment}</span>.
              </div>
            ) : (
              filteredThemes.map((theme, index) => {
                const isExpanded = expandedThemeIds.has(theme.id);
                const isLowConfidence = theme.label.startsWith('[Low-confidence]');
                const displayLabel = isLowConfidence
                  ? theme.label.replace('[Low-confidence]', '').trim()
                  : theme.label;

                return (
                  <div
                    key={theme.id}
                    className={`bg-slate-900/90 border rounded-2xl transition-all duration-200 shadow-xl overflow-hidden ${
                      isExpanded
                        ? 'border-indigo-500/50 bg-slate-900'
                        : 'border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    {/* Theme Card Header */}
                    <div
                      onClick={() => toggleThemeExpand(theme.id)}
                      className="p-6 cursor-pointer select-none space-y-4"
                    >
                      <div className="flex items-start justify-between gap-4">
                        {/* Title & Rank */}
                        <div className="flex items-start gap-3.5">
                          <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                            #{index + 1}
                          </div>

                          <div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <h3 className="text-lg font-bold text-slate-100 hover:text-indigo-300 transition-colors">
                                {displayLabel}
                              </h3>
                              {isLowConfidence && (
                                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" /> Singleton Theme
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              Frequency: <span className="font-semibold text-slate-200">{theme.frequency} pain point{theme.frequency > 1 ? 's' : ''}</span>
                            </div>
                          </div>
                        </div>

                        {/* Priority Score Visual Indicator */}
                        <div className="flex items-center gap-4 flex-shrink-0">
                          <div className="text-right">
                            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 block">Priority Score</span>
                            <div className="flex items-center gap-2 justify-end">
                              <span className="text-lg font-extrabold text-indigo-400 font-mono">
                                {theme.priority_score.toFixed(3)}
                              </span>
                              <div className="w-16 h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                                <div
                                  className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full"
                                  style={{ width: `${Math.min(100, Math.max(10, theme.priority_score * 100))}%` }}
                                />
                              </div>
                            </div>
                          </div>

                          <button className="text-slate-500 hover:text-slate-200 transition-colors p-1">
                            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                          </button>
                        </div>
                      </div>

                      {/* Mini Segment Breakdown Tags */}
                      <div className="flex items-center gap-2 flex-wrap text-xs">
                        <span className="text-slate-500 text-[11px] font-semibold">Segments:</span>
                        {Object.entries(theme.segment_breakdown).map(([segment, count]) => (
                          <span
                            key={segment}
                            className={`px-2.5 py-0.5 rounded-full border text-xs font-semibold ${getSegmentBadgeColor(segment)}`}
                          >
                            {segment}: {count}
                          </span>
                        ))}
                      </div>

                      {/* PM Recommendation Box */}
                      {theme.recommendation && (
                        <div className="p-3.5 rounded-xl bg-indigo-500/5 border border-indigo-500/15 flex items-start gap-3 text-xs text-indigo-200">
                          <Lightbulb className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <span className="font-semibold text-indigo-400 uppercase tracking-wider text-[10px] block mb-0.5">
                              Actionable Recommendation
                            </span>
                            {theme.recommendation}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Expandable Supporting Verbatim Quotes */}
                    {isExpanded && (
                      <div className="border-t border-slate-800 bg-slate-950/60 p-6 space-y-3">
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                          <Quote className="w-3.5 h-3.5 text-indigo-400" />
                          Supporting Verbatim Quotes ({theme.pain_point_ids.length})
                        </div>

                        <div className="space-y-3">
                          {theme.pain_point_ids.map((ppId) => {
                            const pp = painPointsLookup[ppId];

                            if (!pp) {
                              return (
                                <div key={ppId} className="text-xs text-slate-500 italic p-3 rounded-xl bg-slate-900 border border-slate-800">
                                  Pain point ID: {ppId}
                                </div>
                              );
                            }

                            return (
                              <div
                                key={ppId}
                                className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2 text-xs"
                              >
                                <div className="text-slate-200 italic font-medium leading-relaxed">
                                  "{pp.verbatim_quote}"
                                </div>

                                <div className="flex items-center justify-between text-[11px] text-slate-400 flex-wrap gap-2 pt-1 border-t border-slate-800/60">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-slate-300">Text:</span>
                                    <span>{pp.text}</span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    {getSentimentBadge(pp.sentiment)}
                                    <span className="font-mono text-slate-500">Source: <span className="text-slate-400">{pp.source_id}</span></span>
                                    <span className="text-slate-500">Use Case: <span className="text-slate-300 font-medium">{pp.use_case}</span></span>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        ) : (
          /* Raw Markdown View Tab */
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" /> Generated Discovery Report Markdown
              </h2>
              <span className="text-xs text-slate-500 font-mono">Raw output</span>
            </div>

            <pre className="bg-slate-950 p-6 rounded-xl text-xs text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed border border-slate-800/80">
              {reportData.markdown}
            </pre>
          </div>
        )}
      </div>

      {/* Floating Q&A Chat Panel */}
      {reportData.report?.id && (
        <ReportChatPanel reportId={reportData.report.id} />
      )}
    </div>
  );
};
