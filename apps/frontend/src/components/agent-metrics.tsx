"use client";

import { useState, useEffect, useCallback } from "react";
import {
  TrendingUp, Clock, AlertTriangle, CheckCircle2,
  DollarSign, Cpu, Loader2, ArrowLeft, RefreshCw, BarChart2
} from "lucide-react";

import { API_BASE_URL } from "../services/api-service";

const API_BASE = API_BASE_URL;

interface AgentPerformance {
  name: string;
  runs: number;
  success_rate: number;
  avg_latency_ms: number;
  total_cost_usd: number;
}

interface DailyTrend {
  date: string;
  cost_usd: number;
  sessions: number;
}

interface MetricsData {
  total_sessions: number;
  avg_latency_ms: number;
  success_rate: number;
  total_cost_usd: number;
  total_tokens_in: number;
  total_tokens_out: number;
  status_breakdown: Record<string, number>;
  agents: Record<string, AgentPerformance>;
  daily_trends: DailyTrend[];
}

interface AgentMetricsProps {
  token: string;
  onBack: () => void;
}

export default function AgentMetrics({ token, onBack }: AgentMetricsProps) {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/agents/metrics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to load metrics data.");
      setMetrics(await res.json());
    } catch (e: any) {
      setError(e.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  if (loading) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[#09090b]">
        <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
        <p className="mt-4 text-sm text-zinc-400">Loading Agent Analytics & Cost logs...</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center bg-[#09090b] px-6 text-center">
        <AlertTriangle className="h-12 w-12 text-red-500" />
        <h3 className="mt-4 text-lg font-bold text-white">Diagnostics Unavailable</h3>
        <p className="mt-2 text-sm text-zinc-500 max-w-sm">{error || "No data captured yet. Run a few sessions in Agent Studio first."}</p>
        <div className="mt-6 flex gap-3">
          <button onClick={onBack} className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800">
            Back to Studio
          </button>
          <button onClick={fetchMetrics} className="rounded-lg bg-indigo-600 px-4 py-2 text-xs text-white hover:bg-indigo-500">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col bg-[#09090b] text-[#f4f4f5] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="rounded-lg p-1.5 hover:bg-zinc-800 text-zinc-400 hover:text-white transition">
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-sm font-bold text-white">Agent Operations Dashboard</h1>
            <p className="text-[10px] text-zinc-500">Billing Tracking & Pipeline Health Logs</p>
          </div>
        </div>
        <button onClick={fetchMetrics} className="flex items-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 transition">
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      <div className="flex flex-col gap-6 p-6">
        {/* KPI Cards Grid */}
        <div className="grid grid-cols-4 gap-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-xs font-medium">Total Sessions</span>
              <TrendingUp className="h-4 w-4 text-indigo-400" />
            </div>
            <p className="mt-2 text-2xl font-black text-white">{metrics.total_sessions}</p>
            <p className="mt-1 text-[10px] text-zinc-500">Cumulative planner runs</p>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-xs font-medium">Total Billing Cost</span>
              <DollarSign className="h-4 w-4 text-emerald-400" />
            </div>
            <p className="mt-2 text-2xl font-black text-white">${metrics.total_cost_usd.toFixed(4)}</p>
            <p className="mt-1 text-[10px] text-zinc-500">GPT-4o-mini API usage</p>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-xs font-medium">Average Latency</span>
              <Clock className="h-4 w-4 text-amber-400" />
            </div>
            <p className="mt-2 text-2xl font-black text-white">{(metrics.avg_latency_ms / 1000).toFixed(2)}s</p>
            <p className="mt-1 text-[10px] text-zinc-500">Synthesizer pipeline latency</p>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="flex items-center justify-between text-zinc-500">
              <span className="text-xs font-medium">Success Rate</span>
              <CheckCircle2 className="h-4 w-4 text-purple-400" />
            </div>
            <p className="mt-2 text-2xl font-black text-white">{metrics.success_rate}%</p>
            <p className="mt-1 text-[10px] text-zinc-500">Completed without errors</p>
          </div>
        </div>

        {/* Token Accounting Details */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 flex items-center gap-1.5">
            <Cpu className="h-4 w-4 text-indigo-400" /> Token Audit Summary
          </h2>
          <div className="grid grid-cols-3 gap-6">
            <div className="border-r border-zinc-800 pr-6">
              <span className="text-[11px] text-zinc-500 block">Input Tokens (Prompt Context)</span>
              <span className="text-xl font-bold text-zinc-300 block mt-1">{metrics.total_tokens_in.toLocaleString()}</span>
            </div>
            <div className="border-r border-zinc-800 pr-6">
              <span className="text-[11px] text-zinc-500 block">Output Tokens (Synthesizer answers)</span>
              <span className="text-xl font-bold text-zinc-300 block mt-1">{metrics.total_tokens_out.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-[11px] text-zinc-500 block">Total Computational Tokens</span>
              <span className="text-xl font-bold text-indigo-400 block mt-1">{(metrics.total_tokens_in + metrics.total_tokens_out).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Agent Breakdown Table */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 overflow-hidden">
          <div className="border-b border-zinc-800 bg-zinc-900 px-5 py-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
              <BarChart2 className="h-4 w-4 text-indigo-400" /> Specialized Agent Benchmarks
            </h2>
          </div>
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500">
                <th className="px-5 py-3 font-semibold">Agent Name</th>
                <th className="px-5 py-3 font-semibold text-center">Runs</th>
                <th className="px-5 py-3 font-semibold text-center">Success Rate</th>
                <th className="px-5 py-3 font-semibold text-center">Avg Latency</th>
                <th className="px-5 py-3 font-semibold text-right">Total Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {Object.values(metrics.agents).map((agent) => (
                <tr key={agent.name} className="hover:bg-zinc-800/20 text-zinc-300">
                  <td className="px-5 py-3 font-medium capitalize">{agent.name.replace("_", " ")}</td>
                  <td className="px-5 py-3 text-center">{agent.runs}</td>
                  <td className="px-5 py-3 text-center">
                    <span className={`rounded-full px-2 py-0.5 font-semibold text-[10px] ${agent.success_rate >= 80 ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
                      {agent.success_rate}%
                    </span>
                  </td>
                  <td className="px-5 py-3 text-center">{(agent.avg_latency_ms / 1000).toFixed(2)}s</td>
                  <td className="px-5 py-3 text-right font-mono text-indigo-400">${agent.total_cost_usd.toFixed(6)}</td>
                </tr>
              ))}
              {Object.keys(metrics.agents).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-zinc-600">No agent run telemetry available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Daily Cost Graph (Native SVG bar chart) */}
        {metrics.daily_trends.length > 0 && (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-6">
              Daily Cost History (USD)
            </h2>
            <div className="flex items-end justify-between h-40 gap-4 mt-2 px-2 border-b border-zinc-800 pb-2">
              {metrics.daily_trends.map((t, idx) => {
                const maxCost = Math.max(...metrics.daily_trends.map(d => d.cost_usd), 0.001);
                const pct = (t.cost_usd / maxCost) * 100;
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center group relative">
                    {/* Tooltip */}
                    <div className="absolute bottom-full mb-1 hidden group-hover:block bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-[9px] font-mono text-zinc-200 z-10 whitespace-nowrap shadow-xl">
                      ${t.cost_usd.toFixed(6)} ({t.sessions} runs)
                    </div>
                    {/* Bar */}
                    <div
                      className="w-full bg-indigo-500/40 border-t border-indigo-400 group-hover:bg-indigo-500 transition-all rounded-t-sm"
                      style={{ height: `${pct}%`, minHeight: "4px" }}
                    />
                    {/* Date */}
                    <span className="text-[9px] text-zinc-600 mt-2 font-mono whitespace-nowrap overflow-hidden text-ellipsis max-w-full">
                      {t.date.split("-").slice(1).join("/")}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
