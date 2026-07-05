"use client";

import { useState, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import {
  FileText, Zap, Download, RefreshCw, ChevronDown,
  Brain, BarChart3, AlertTriangle, CheckCircle2,
  Layers, TrendingUp, BookOpen, Cpu, Loader2,
  Shield, ToggleLeft, ToggleRight, Star, Info
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

type ReportType = "executive_summary" | "ml_model_card" | "statistical_breakdown" | "full_analytics";
type ExportFormat = "pdf" | "excel" | "pptx" | "png" | "markdown";

interface ReportResult {
  report_id: string;
  narrative: string;
  export_path: string;
  export_format: string;
  shap_available: boolean;
  model_trained: boolean;
  generated_at: string;
  latency_seconds: number;
}

const REPORT_TYPES: { value: ReportType; label: string; icon: React.ReactNode; desc: string }[] = [
  {
    value: "executive_summary",
    label: "Executive Summary",
    icon: <TrendingUp className="h-4 w-4" />,
    desc: "CEO-level overview with KPIs and key insights",
  },
  {
    value: "ml_model_card",
    label: "ML Model Card",
    icon: <Brain className="h-4 w-4" />,
    desc: "Model performance, feature importance & SHAP explanations",
  },
  {
    value: "statistical_breakdown",
    label: "Statistical Breakdown",
    icon: <BarChart3 className="h-4 w-4" />,
    desc: "Full statistical analysis: mean, std, outliers, correlations",
  },
  {
    value: "full_analytics",
    label: "Full Analytics Report",
    icon: <Layers className="h-4 w-4" />,
    desc: "Comprehensive report covering analytics + ML + SHAP",
  },
];

const EXPORT_FORMATS: { value: ExportFormat; label: string; color: string }[] = [
  { value: "pdf", label: "PDF", color: "text-red-400" },
  { value: "excel", label: "Excel", color: "text-green-400" },
  { value: "pptx", label: "PowerPoint", color: "text-orange-400" },
  { value: "png", label: "PNG Card", color: "text-purple-400" },
  { value: "markdown", label: "Markdown", color: "text-blue-400" },
];

export default function ReportArea() {
  const { token, documents } = useChatStore();

  // Config state
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [reportType, setReportType] = useState<ReportType>("full_analytics");
  const [exportFormat, setExportFormat] = useState<ExportFormat>("pdf");
  const [grounded, setGrounded] = useState(true);
  const [customInstructions, setCustomInstructions] = useState("");
  const [includeAnalytics, setIncludeAnalytics] = useState(true);
  const [includeMl, setIncludeMl] = useState(true);
  const [includeShap, setIncludeShap] = useState(true);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<ReportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Headers helper
  const headers = useCallback(
    () => ({ "Content-Type": "application/json", Authorization: `Bearer ${token}` }),
    [token]
  );

  const handleGenerate = async () => {
    if (!selectedDocId) {
      setError("Please select a document first.");
      return;
    }
    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/reports/generate/${selectedDocId}`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          report_type: reportType,
          export_format: exportFormat,
          grounded,
          custom_instructions: customInstructions,
          include_analytics: includeAnalytics,
          include_ml: includeMl,
          include_shap: includeShap,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Report generation failed");
      }
      const data: ReportResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Unknown error");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!result) return;
    try {
      const res = await fetch(`${API_BASE}/reports/download/${result.report_id}`, {
        headers: headers(),
      });
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nexora_report_${result.report_id}.${result.export_format === "excel" ? "xlsx" : result.export_format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b] text-[#f4f4f5]">
      {/* ── Left Config Panel ─────────────────────────────────────────── */}
      <div className="flex w-80 shrink-0 flex-col border-r border-zinc-800 overflow-y-auto">
        {/* Header */}
        <div className="border-b border-zinc-800 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
              <FileText className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white">Report Studio</h1>
              <p className="text-[10px] text-zinc-500">AI-Powered Report Generator</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-5 px-5 py-5">
          {/* Dataset Selection */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Source Document
            </label>
            <div className="relative">
              <select
                value={selectedDocId ?? ""}
                onChange={(e) => setSelectedDocId(Number(e.target.value) || null)}
                className="w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
              >
                <option value="">— Select a document —</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.file_name || `Document ${doc.id}`}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3 w-3 text-zinc-500" />
            </div>
          </section>

          {/* Report Type */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Report Type
            </label>
            <div className="flex flex-col gap-1.5">
              {REPORT_TYPES.map((rt) => (
                <button
                  key={rt.value}
                  onClick={() => setReportType(rt.value)}
                  className={`flex items-start gap-3 rounded-lg border px-3 py-2.5 text-left transition-all ${
                    reportType === rt.value
                      ? "border-indigo-500/50 bg-indigo-600/10 text-white"
                      : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                  }`}
                >
                  <span className={`mt-0.5 shrink-0 ${reportType === rt.value ? "text-indigo-400" : ""}`}>
                    {rt.icon}
                  </span>
                  <div>
                    <div className="text-xs font-semibold">{rt.label}</div>
                    <div className="text-[10px] text-zinc-500 mt-0.5">{rt.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </section>

          {/* Export Format */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Export Format
            </label>
            <div className="grid grid-cols-5 gap-1">
              {EXPORT_FORMATS.map((fmt) => (
                <button
                  key={fmt.value}
                  onClick={() => setExportFormat(fmt.value)}
                  className={`rounded-lg border px-2 py-1.5 text-[10px] font-bold transition-all ${
                    exportFormat === fmt.value
                      ? `border-indigo-500/50 bg-indigo-600/10 ${fmt.color}`
                      : "border-zinc-800 bg-zinc-900/50 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300"
                  }`}
                >
                  {fmt.label}
                </button>
              ))}
            </div>
          </section>

          {/* Grounded Toggle */}
          <section>
            <div className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <Shield className="h-3.5 w-3.5 text-indigo-400" />
                <div>
                  <div className="text-xs font-semibold text-zinc-200">Grounded Mode</div>
                  <div className="text-[10px] text-zinc-500">No hallucinations — cite all data</div>
                </div>
              </div>
              <button onClick={() => setGrounded(!grounded)}>
                {grounded ? (
                  <ToggleRight className="h-5 w-5 text-indigo-400" />
                ) : (
                  <ToggleLeft className="h-5 w-5 text-zinc-600" />
                )}
              </button>
            </div>
          </section>

          {/* Data Sources */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Data Sources
            </label>
            <div className="flex flex-col gap-1.5">
              {[
                { key: "analytics", label: "Analytics Profile", icon: <BarChart3 className="h-3 w-3" />, state: includeAnalytics, set: setIncludeAnalytics },
                { key: "ml", label: "ML Model Session", icon: <Brain className="h-3 w-3" />, state: includeMl, set: setIncludeMl },
                { key: "shap", label: "SHAP Explainability", icon: <Cpu className="h-3 w-3" />, state: includeShap, set: setIncludeShap },
              ].map((src) => (
                <label
                  key={src.key}
                  className="flex cursor-pointer items-center gap-2.5 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2"
                >
                  <input
                    type="checkbox"
                    checked={src.state}
                    onChange={(e) => src.set(e.target.checked)}
                    className="accent-indigo-500"
                  />
                  <span className="text-indigo-400">{src.icon}</span>
                  <span className="text-xs text-zinc-300">{src.label}</span>
                </label>
              ))}
            </div>
          </section>

          {/* Custom Instructions */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Custom Instructions <span className="text-zinc-600">(optional)</span>
            </label>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="e.g. Focus on customer churn drivers. Keep it under 500 words."
              maxLength={2000}
              rows={3}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600 focus:border-indigo-500 focus:outline-none resize-none"
            />
          </section>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={generating || !selectedDocId}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-900/30 transition-all hover:from-indigo-500 hover:to-purple-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {generating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Generating Report...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                Generate Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Right Preview Panel ───────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Panel Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-3.5">
          <div className="flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-indigo-400" />
            <span className="text-sm font-semibold text-zinc-200">
              {result ? "Report Preview" : "Report Studio"}
            </span>
            {result && (
              <span className="ml-2 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-400">
                Generated in {result.latency_seconds}s
              </span>
            )}
          </div>
          {result && (
            <button
              onClick={handleDownload}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-indigo-500 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              Download {result.export_format.toUpperCase()}
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-6 mt-4 flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
            <p className="text-xs text-red-300">{error}</p>
          </div>
        )}

        {/* Result */}
        {result ? (
          <div className="flex flex-1 flex-col overflow-y-auto px-6 py-5">
            {/* Status Badges */}
            <div className="mb-5 flex flex-wrap gap-2">
              <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-400">
                <CheckCircle2 className="h-3 w-3" /> Report Generated
              </span>
              {result.model_trained && (
                <span className="flex items-center gap-1.5 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 text-[11px] font-medium text-indigo-400">
                  <Brain className="h-3 w-3" /> ML Model Included
                </span>
              )}
              {result.shap_available ? (
                <span className="flex items-center gap-1.5 rounded-full border border-purple-500/20 bg-purple-500/10 px-2.5 py-1 text-[11px] font-medium text-purple-400">
                  <Cpu className="h-3 w-3" /> SHAP Available
                </span>
              ) : (
                <span className="flex items-center gap-1.5 rounded-full border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 text-[11px] font-medium text-zinc-500">
                  <Info className="h-3 w-3" /> SHAP Not Available
                </span>
              )}
              {grounded && (
                <span className="flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium text-amber-400">
                  <Shield className="h-3 w-3" /> Grounded
                </span>
              )}
            </div>

            {/* Narrative Preview */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
              <div className="border-b border-zinc-800 bg-zinc-900 px-4 py-2.5">
                <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                  AI Narrative
                </span>
              </div>
              <div className="overflow-y-auto max-h-[calc(100vh-300px)] px-5 py-4">
                <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-zinc-300">
                  {result.narrative}
                </pre>
              </div>
            </div>

            {/* Metadata Footer */}
            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-1.5 text-[10px] text-zinc-600">
              <span>Report ID: <span className="font-mono text-zinc-500">{result.report_id}</span></span>
              <span>Format: <span className="text-zinc-400 font-semibold">{result.export_format.toUpperCase()}</span></span>
              <span>Generated: <span className="text-zinc-500">{new Date(result.generated_at).toLocaleString()}</span></span>
            </div>
          </div>
        ) : (
          /* ── Empty State ──────────────────────────────────────────── */
          <div className="flex flex-1 flex-col items-center justify-center gap-5 px-8 py-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 border border-indigo-500/20">
              <FileText className="h-8 w-8 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">AI Report Generator</h2>
              <p className="mt-1.5 max-w-sm text-sm text-zinc-500">
                Select a document and report type on the left, then click{" "}
                <span className="font-semibold text-indigo-400">Generate Report</span> to create
                a professional AI-narrated report.
              </p>
            </div>

            {/* Feature Grid */}
            <div className="mt-4 grid grid-cols-2 gap-3 max-w-md w-full">
              {[
                { icon: <Brain className="h-4 w-4 text-indigo-400" />, title: "ML Model Card", desc: "Algorithm metrics & SHAP" },
                { icon: <BarChart3 className="h-4 w-4 text-emerald-400" />, title: "Statistical EDA", desc: "Distributions & outliers" },
                { icon: <TrendingUp className="h-4 w-4 text-amber-400" />, title: "Executive Summary", desc: "CEO-level insights" },
                { icon: <Star className="h-4 w-4 text-purple-400" />, title: "Multi-Format Export", desc: "PDF · Excel · PPT · PNG" },
              ].map((f) => (
                <div key={f.title} className="flex items-start gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 px-3.5 py-3 text-left">
                  <div className="mt-0.5 shrink-0">{f.icon}</div>
                  <div>
                    <div className="text-xs font-semibold text-zinc-200">{f.title}</div>
                    <div className="text-[10px] text-zinc-500">{f.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* SHAP Architecture Hook Note */}
            <div className="mt-2 flex max-w-md items-start gap-2.5 rounded-xl border border-purple-500/20 bg-purple-500/5 px-4 py-3 text-left">
              <Cpu className="mt-0.5 h-4 w-4 shrink-0 text-purple-400" />
              <p className="text-[11px] text-purple-300">
                <span className="font-bold">SHAP Explainability</span> and{" "}
                <span className="font-bold">Model Comparison</span> hooks are active.
                Train ≥2 algorithms in ML Studio to see comparison tables in your report.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
