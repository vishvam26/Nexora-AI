"use client";

import { useState, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import {
  Shield, CheckCircle2, AlertTriangle, Play,
  ThumbsUp, ThumbsDown, Database, Cpu, Loader2,
  X, RefreshCw, Sparkles, MessageSquare, ArrowRight,
  TrendingUp, Award, Download, Clock, Zap, HelpCircle
} from "lucide-react";

import { API_BASE_URL } from "../services/api-service";

const API_BASE = API_BASE_URL;

interface DashboardKPIs {
  avg_faithfulness: number;
  avg_relevance: number;
  avg_recall: number;
  avg_hallucination: number;
  avg_confidence: number;
  avg_latency_ms: number;
  satisfaction_rate: number;
  positive_feedback_count: number;
  negative_feedback_count: number;
  pending_reviews_count: number;
  approved_samples_count: number;
  rejected_samples_count: number;
  dataset_size_bytes: number;
  current_model_version: string;
}

interface ReviewCandidate {
  id: number;
  query: string;
  original_response: string;
  faithfulness: number;
  hallucination_score: number;
  confidence_score: number;
  priority: string;
  review_status: string;
  root_cause?: string;
  domain_tag?: string;
  model_version: string;
  rag_pipeline_version: string;
  created_at: string;
}

interface ReplayResult {
  query: string;
  original_response: string;
  new_response: string;
  original_scores: { faithfulness: number; answer_relevance: number };
  new_scores: { faithfulness: number; answer_relevance: number };
}

export default function EvalDashboard() {
  const { token } = useChatStore();

  // Dashboard states
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [pendingReviews, setPendingReviews] = useState<ReviewCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  // Replay modal states
  const [activeReplayCandidate, setActiveReplayCandidate] = useState<ReviewCandidate | null>(null);
  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);
  const [replaying, setReplaying] = useState(false);
  const [replayError, setReplayError] = useState("");

  const headers = useCallback(() => ({
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "69420",
    Authorization: `Bearer ${token}`
  }), [token]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [kpiRes, queueRes] = await Promise.all([
        fetch(`${API_BASE}/eval/dashboard`, { headers: headers() }),
        fetch(`${API_BASE}/eval/review-queue`, { headers: headers() })
      ]);
      if (kpiRes.ok) setKpis(await kpiRes.json());
      if (queueRes.ok) setPendingReviews(await queueRes.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, [headers]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleReviewAction = async (id: number, actionStatus: "approved" | "rejected") => {
    try {
      const res = await fetch(`${API_BASE}/eval/review/${id}/status?status_value=${actionStatus}`, {
        method: "POST",
        headers: headers()
      });
      if (res.ok) {
        loadData();
      }
    } catch { /* ignore */ }
  };

  const handleExecuteReplay = async (candidateId: number) => {
    setReplaying(true);
    setReplayError("");
    setReplayResult(null);

    try {
      const res = await fetch(`${API_BASE}/eval/replay/${candidateId}`, {
        method: "POST",
        headers: headers()
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Replay executor crashed.");
      }
      setReplayResult(data);
    } catch (e: any) {
      setReplayError(e.message || "Replay sandbox compilation error");
    } finally {
      setReplaying(false);
    }
  };

  const handleExport = async (format: "jsonl" | "csv") => {
    try {
      window.open(`${API_BASE}/eval/export/${format}?token=${token}`, "_blank");
    } catch { /* ignore */ }
  };

  const getMetricStyle = (score: number) => {
    if (score >= 0.8) return { text: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
    if (score >= 0.6) return { text: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" };
    return { text: "text-red-400", bg: "bg-red-500/10 border-red-500/20" };
  };

  const getPriorityStyle = (priority: string) => {
    if (priority === "HIGH") return "bg-red-500/15 text-red-300 border border-red-500/20";
    if (priority === "MEDIUM") return "bg-amber-500/15 text-amber-300 border border-amber-500/20";
    return "bg-zinc-800 text-zinc-400 border border-zinc-700/60";
  };

  if (loading && !kpis) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[#09090b]">
        <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
        <p className="mt-4 text-sm text-zinc-400">Loading AI Judge dashboard...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col bg-[#09090b] text-[#f4f4f5] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 border border-indigo-500/30">
            <Shield className="h-4 w-4 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">AI Evaluation & Continuous Learning</h1>
            <p className="text-[10px] text-zinc-500">Hallucination metrics, Human Review, and QLoRA Dataset Export Hub</p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <button onClick={loadData} className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-6 p-6">
        {/* KPI Cards Grid */}
        {kpis && (
          <div className="grid grid-cols-4 gap-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4 relative">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Faithfulness</span>
              <p className={`mt-2 text-2xl font-black ${getMetricStyle(kpis.avg_faithfulness).text}`}>
                {Math.round(kpis.avg_faithfulness * 100)}%
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Claims supported by context</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Confidence</span>
              <p className={`mt-2 text-2xl font-black ${getMetricStyle(kpis.avg_confidence).text}`}>
                {Math.round(kpis.avg_confidence * 100)}%
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Average RAG prediction confidence</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Hallucination Rate</span>
              <p className="mt-2 text-2xl font-black text-rose-500">
                {Math.round(kpis.avg_hallucination * 100)}%
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Grounding failure proxy</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Avg Latency</span>
              <p className="mt-2 text-2xl font-black text-amber-500">
                {(kpis.avg_latency_ms / 1000).toFixed(2)}s
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Response generation time</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">User Satisfaction</span>
              <p className="mt-2 text-2xl font-black text-indigo-400">
                {kpis.satisfaction_rate}%
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Thumbs Up: {kpis.positive_feedback_count} | Thumbs Down: {kpis.negative_feedback_count}</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Review Queue</span>
              <p className="mt-2 text-2xl font-black text-pink-400">
                {kpis.pending_reviews_count}
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Pending Human Review</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Approved / Rejected</span>
              <p className="mt-2 text-2xl font-black text-emerald-400">
                {kpis.approved_samples_count} <span className="text-zinc-600">/</span> <span className="text-red-400">{kpis.rejected_samples_count}</span>
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Dataset samples built</span>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
              <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider block">Model Version</span>
              <p className="mt-2 text-2xl font-black text-zinc-300">
                {kpis.current_model_version}
              </p>
              <span className="text-[9px] text-zinc-600 block mt-1">Dataset size: {Math.round(kpis.dataset_size_bytes / 1024)} KB</span>
            </div>
          </div>
        )}

        {/* Dataset Exporter Tools */}
        <div className="flex gap-4 items-center justify-between rounded-xl border border-indigo-500/15 bg-indigo-500/5 px-6 py-4">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-400" />
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">Dataset Export Workspace</h4>
              <p className="text-[10px] text-zinc-500">Download clean conversational datasets approved by reviews</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleExport("jsonl")}
              className="flex items-center gap-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 px-4 py-2 text-xs font-bold text-zinc-200 transition"
            >
              <Download className="h-4 w-4" />
              Export JSONL (QLoRA)
            </button>
            <button
              onClick={() => handleExport("csv")}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-xs font-bold text-white transition"
            >
              <Download className="h-4 w-4" />
              Export CSV Format
            </button>
          </div>
        </div>

        {/* Human Review Queue Grid */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 overflow-hidden">
          <div className="border-b border-zinc-800 bg-zinc-900 px-5 py-3 flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
              <Cpu className="h-4 w-4 text-indigo-400" /> Human Review Queue & AI Replay Debugger
            </h2>
          </div>
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500">
                <th className="px-5 py-3 font-semibold">User Query</th>
                <th className="px-5 py-3 font-semibold">Domain</th>
                <th className="px-5 py-3 font-semibold">Root Cause</th>
                <th className="px-5 py-3 font-semibold text-center">Priority</th>
                <th className="px-5 py-3 font-semibold text-center">Confidence</th>
                <th className="px-5 py-3 font-semibold text-right">Human Verification Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {pendingReviews.map((cand) => (
                <tr key={cand.id} className="hover:bg-zinc-800/10 text-zinc-300">
                  <td className="px-5 py-3 max-w-[200px] truncate" title={cand.query}>{cand.query}</td>
                  <td className="px-5 py-3 font-medium text-indigo-300">{cand.domain_tag || "General"}</td>
                  <td className="px-5 py-3 text-zinc-400">{cand.root_cause || "None"}</td>
                  <td className="px-5 py-3 text-center">
                    <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold ${getPriorityStyle(cand.priority)}`}>
                      {cand.priority}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-center font-mono">
                    {Math.round(cand.confidence_score * 100)}%
                  </td>
                  <td className="px-5 py-3 text-right flex items-center justify-end gap-2">
                    <button
                      onClick={() => { setActiveReplayCandidate(cand); setReplayResult(null); setReplayError(""); }}
                      className="rounded bg-indigo-600/15 border border-indigo-500/20 px-2 py-1 text-[10px] font-bold text-indigo-400 hover:bg-indigo-600/25 transition"
                    >
                      Replay
                    </button>
                    <button
                      onClick={() => handleReviewAction(cand.id, "approved")}
                      className="rounded bg-emerald-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-emerald-500 transition"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleReviewAction(cand.id, "rejected")}
                      className="rounded bg-rose-600/10 border border-rose-500/20 px-2 py-1 text-[10px] font-bold text-rose-400 hover:bg-rose-600/20 transition"
                    >
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
              {pendingReviews.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-zinc-600">
                    Human review queue is currently empty.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── AI Replay Sandbox Modal ────────────────────────────────── */}
      {activeReplayCandidate && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-[#09090b] border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between bg-zinc-900/40">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Replay Debugger Sandbox</h3>
              </div>
              <button
                onClick={() => { setActiveReplayCandidate(null); setReplayResult(null); }}
                className="rounded-lg p-1 hover:bg-zinc-800 text-zinc-500 hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
              <div className="rounded-xl border border-zinc-800 bg-[#0d0d0e] p-4 text-xs">
                <span className="text-[9px] font-semibold text-zinc-500 uppercase tracking-wider block">Failed Prompt query</span>
                <p className="mt-1 text-zinc-300 font-mono text-[11px]">{activeReplayCandidate.query}</p>
              </div>

              {!replayResult ? (
                <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                    <Cpu className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-zinc-300">Ready to rerun query sandbox</h4>
                    <p className="mt-1 max-w-xs text-xs text-zinc-600 leading-normal">
                      Nexora will reload the original RAG prompt and retrieved chunks to compile a new response.
                    </p>
                  </div>
                  <button
                    onClick={() => handleExecuteReplay(activeReplayCandidate.id)}
                    disabled={replaying}
                    className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
                  >
                    {replaying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    Rerun Replay Sandbox
                  </button>
                  {replayError && (
                    <p className="text-xs text-red-400 mt-2">{replayError}</p>
                  )}
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {/* Side-by-side Response Panels */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Old Response */}
                    <div className="rounded-xl border border-zinc-800 bg-zinc-950/20 overflow-hidden flex flex-col">
                      <div className="border-b border-zinc-800 bg-zinc-900 px-4 py-2 flex items-center justify-between">
                        <span className="text-[9px] font-semibold text-zinc-500 uppercase tracking-wider">Original output</span>
                        <div className="flex gap-2">
                          <span className="rounded bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 text-[8px] font-mono text-red-400">
                            F: {Math.round(replayResult.original_scores.faithfulness * 100)}%
                          </span>
                          <span className="rounded bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 text-[8px] font-mono text-red-400">
                            R: {Math.round(replayResult.original_scores.answer_relevance * 100)}%
                          </span>
                        </div>
                      </div>
                      <div className="p-4 font-mono text-[10px] text-zinc-400 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                        {replayResult.original_response}
                      </div>
                    </div>

                    {/* New Replay Response */}
                    <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 overflow-hidden flex flex-col">
                      <div className="border-b border-indigo-500/20 bg-indigo-500/10 px-4 py-2 flex items-center justify-between">
                        <span className="text-[9px] font-semibold text-indigo-400 uppercase tracking-wider">Sandbox Replay output</span>
                        <div className="flex gap-2">
                          <span className={`rounded px-1.5 py-0.5 text-[8px] font-mono border ${getMetricStyle(replayResult.new_scores.faithfulness).bg} ${getMetricStyle(replayResult.new_scores.faithfulness).text}`}>
                            F: {Math.round(replayResult.new_scores.faithfulness * 100)}%
                          </span>
                          <span className={`rounded px-1.5 py-0.5 text-[8px] font-mono border ${getMetricStyle(replayResult.new_scores.answer_relevance).bg} ${getMetricStyle(replayResult.new_scores.answer_relevance).text}`}>
                            R: {Math.round(replayResult.new_scores.answer_relevance * 100)}%
                          </span>
                        </div>
                      </div>
                      <div className="p-4 font-mono text-[10px] text-indigo-200 max-h-60 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                        {replayResult.new_response}
                      </div>
                    </div>
                  </div>

                  {/* Replay feedback comparison details */}
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex gap-2.5 items-start">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div className="text-xs">
                      <p className="font-semibold text-emerald-300">Replay Complete</p>
                      <p className="text-[10px] text-zinc-500 mt-1 leading-normal">
                        Faithfulness score comparison: {Math.round(replayResult.original_scores.faithfulness * 100)}% → <span className="font-bold text-emerald-400">{Math.round(replayResult.new_scores.faithfulness * 100)}%</span>.
                        The query data remains saved in the Human Review queue.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
