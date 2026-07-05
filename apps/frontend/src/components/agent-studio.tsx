"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import {
  Sparkles, Send, Loader2, ChevronDown, CheckCircle2,
  AlertCircle, Clock, Brain, BarChart3, BookOpen,
  FileText, Cpu, ChevronRight, ExternalLink,
  RotateCcw, Shield, Star, Zap, Info, History,
  Play, StopCircle, Database
} from "lucide-react";
import AgentMetrics from "./agent-metrics";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// ── Types ──────────────────────────────────────────────────────────────────────

type AgentName = "analytics_agent" | "ml_agent" | "rag_agent" | "report_agent" | string;
type AgentStatus = "idle" | "running" | "success" | "error" | "skipped";
type StreamPhase = "idle" | "planning" | "running" | "synthesizing" | "done" | "error";

interface PlanStep { agent: AgentName; task: string; }
interface AgentState {
  name: AgentName;
  task: string;
  status: AgentStatus;
  summary: string;
  latency_ms: number;
  tool_calls: string[];
  expanded: boolean;
}
interface Citation { source: string; page: string | number; score: number; snippet: string; }
interface PastSession {
  session_id: string;
  question: string;
  status: string;
  agents_run: string[];
  confidence: number;
  total_latency_ms: number;
  created_at: string;
}

// ── Agent metadata ─────────────────────────────────────────────────────────────

const AGENT_META: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  analytics_agent: { label: "Analytics Agent",  icon: <BarChart3 className="h-4 w-4" />,  color: "text-emerald-400",  bg: "bg-emerald-500/10 border-emerald-500/30" },
  ml_agent:        { label: "ML Agent",          icon: <Brain className="h-4 w-4" />,       color: "text-indigo-400",   bg: "bg-indigo-500/10 border-indigo-500/30" },
  rag_agent:       { label: "RAG Agent",          icon: <BookOpen className="h-4 w-4" />,    color: "text-amber-400",    bg: "bg-amber-500/10 border-amber-500/30" },
  report_agent:    { label: "Report Agent",       icon: <FileText className="h-4 w-4" />,    color: "text-purple-400",   bg: "bg-purple-500/10 border-purple-500/30" },
  memory_agent:    { label: "Memory Agent",       icon: <Clock className="h-4 w-4" />,       color: "text-pink-400",     bg: "bg-pink-500/10 border-pink-500/30" },
};


const STATUS_ICON: Record<AgentStatus, React.ReactNode> = {
  idle:    <div className="h-3 w-3 rounded-full border-2 border-zinc-600" />,
  running: <Loader2 className="h-3 w-3 animate-spin text-indigo-400" />,
  success: <CheckCircle2 className="h-3 w-3 text-emerald-400" />,
  error:   <AlertCircle className="h-3 w-3 text-red-400" />,
  skipped: <div className="h-3 w-3 rounded-full border-2 border-zinc-700 bg-zinc-800" />,
};

// ── Suggestions ────────────────────────────────────────────────────────────────

const SUGGESTIONS = [
  "What are the main drivers of customer churn in this dataset?",
  "Analyze the model's performance and explain which features matter most.",
  "Find all policy documents related to data retention and summarize key points.",
  "Generate an executive summary report of the analytics and ML findings.",
  "What outliers exist in this dataset and how should they be handled?",
  "Compare all trained algorithms and recommend the best one for production.",
];

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AgentStudio() {
  const { token, documents, knowledgeBases, activeWorkspace } = useChatStore();

  // Input config
  const [question, setQuestion] = useState("");
  const [docId, setDocId] = useState<number | null>(null);
  const [workspaceId, setWorkspaceId] = useState<number | null>(activeWorkspace?.id ?? null);
  const [topK, setTopK] = useState(5);
  const [generateReport, setGenerateReport] = useState(false);
  const [reportFormat, setReportFormat] = useState("pdf");

  // Orchestration state
  const [phase, setPhase] = useState<StreamPhase>("idle");
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [agents, setAgents] = useState<AgentState[]>([]);
  const [finalAnswer, setFinalAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [sessionId, setSessionId] = useState("");
  const [totalLatency, setTotalLatency] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");

  // Past sessions
  const [pastSessions, setPastSessions] = useState<PastSession[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);

  // Cost tracking summary states
  const [sessionCost, setSessionCost] = useState(0);
  const [sessionTokensIn, setSessionTokensIn] = useState(0);
  const [sessionTokensOut, setSessionTokensOut] = useState(0);


  const abortRef = useRef<() => void>(() => {});
  const answerRef = useRef<HTMLDivElement>(null);

  const headers = useCallback(() => ({
    Authorization: `Bearer ${token}`,
  }), [token]);

  // Load workspace into selector on mount
  useEffect(() => {
    if (activeWorkspace?.id && !workspaceId) {
      setWorkspaceId(activeWorkspace.id);
    }
  }, [activeWorkspace]);

  const loadSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/agents/sessions?limit=10`, { headers: headers() });
      if (res.ok) setPastSessions(await res.json());
    } catch { /* ignore */ }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    if (!workspaceId && !docId) {
      setErrorMsg("Select at least a workspace (for RAG) or a document (for Analytics/ML).");
      return;
    }

    // Reset state
    setPhase("planning");
    setPlan([]);
    setAgents([]);
    setFinalAnswer("");
    setCitations([]);
    setConfidence(0);
    setSessionId("");
    setTotalLatency(0);
    setErrorMsg("");

    // Build SSE URL
    const params = new URLSearchParams({
      question,
      top_k: String(topK),
      generate_report: String(generateReport),
      report_format: reportFormat,
      report_type: "full_analytics",
    });
    if (workspaceId) params.set("workspace_id", String(workspaceId));
    if (docId) params.set("doc_id", String(docId));

    const url = `${API_BASE}/agents/stream?${params.toString()}`;

    let es: EventSource | null = null;
    try {
      // EventSource doesn't support custom headers — use fetch + ReadableStream instead
      const controller = new AbortController();
      abortRef.current = () => controller.abort();

      const res = await fetch(url, {
        headers: headers(),
        signal: controller.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail || "Stream request failed");
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        let currentData = "";

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            currentData = line.slice(6).trim();
          } else if (line === "" && currentEvent && currentData) {
            try {
              const payload = JSON.parse(currentData);
              handleSSEEvent(currentEvent, payload);
            } catch { /* malformed JSON — skip */ }
            currentEvent = "";
            currentData = "";
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") {
        setErrorMsg(e.message || "Streaming connection failed.");
        setPhase("error");
      }
    }
  };

  const handleSSEEvent = (event: string, payload: any) => {
    switch (event) {
      case "plan_ready":
        setPlan(payload.plan || []);
        setSessionId(payload.session_id || "");
        setPhase("running");
        // Pre-populate agent cards from plan
        setAgents(
          (payload.plan || []).map((step: PlanStep) => ({
            name: step.agent,
            task: step.task,
            status: "idle" as AgentStatus,
            summary: "",
            latency_ms: 0,
            tool_calls: [],
            expanded: false,
          }))
        );
        break;

      case "agent_start":
        setAgents((prev) =>
          prev.map((a) =>
            a.name === payload.agent ? { ...a, status: "running" } : a
          )
        );
        break;

      case "agent_result":
        setAgents((prev) =>
          prev.map((a) =>
            a.name === payload.agent
              ? {
                  ...a,
                  status: payload.status as AgentStatus,
                  summary: payload.summary || "",
                  latency_ms: payload.latency_ms || 0,
                  tool_calls: payload.tool_calls || [],
                }
              : a
          )
        );
        break;

      case "synthesis_start":
        setPhase("synthesizing");
        break;

      case "final_answer":
        setFinalAnswer(payload.answer || "");
        setCitations(payload.citations || []);
        setConfidence(payload.confidence || 0);
        break;

      case "done":
        setTotalLatency(payload.total_latency_ms || 0);
        setSessionId(payload.session_id || sessionId);
        setSessionCost(payload.cost_usd || 0.0);
        setSessionTokensIn(payload.tokens_in || 0);
        setSessionTokensOut(payload.tokens_out || 0);
        setPhase("done");
        loadSessions();
        setTimeout(() => answerRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
        break;


      case "error":
        setErrorMsg(payload.error || "Unknown error from agent system.");
        setPhase("error");
        break;
    }
  };

  const handleStop = () => { abortRef.current(); setPhase("error"); setErrorMsg("Stopped by user."); };
  const handleReset = () => { setPhase("idle"); setPlan([]); setAgents([]); setFinalAnswer(""); setCitations([]); setErrorMsg(""); setQuestion(""); };

  const confidenceColor = confidence >= 0.8 ? "text-emerald-400" : confidence >= 0.5 ? "text-amber-400" : "text-red-400";
  const confidenceBg   = confidence >= 0.8 ? "bg-emerald-500/10 border-emerald-500/30" : confidence >= 0.5 ? "bg-amber-500/10 border-amber-500/30" : "bg-red-500/10 border-red-500/30";

  if (showMetrics) {
    return <AgentMetrics token={token} onBack={() => setShowMetrics(false)} />;
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b] text-[#f4f4f5]">


      {/* ── Left Config Panel ──────────────────────────────────────── */}
      <div className="flex w-80 shrink-0 flex-col border-r border-zinc-800 overflow-y-auto">
        {/* Header */}
        <div className="border-b border-zinc-800 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 shadow-lg shadow-indigo-900/30">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white">Agent Studio</h1>
              <p className="text-[10px] text-zinc-500">AI Decision Intelligence · Multi-Agent</p>
            </div>
          </div>
          <button 
            onClick={() => setShowMetrics(true)}
            className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition"
          >
            <BarChart3 className="h-3.5 w-3.5" />
            Diagnostics Dashboard
          </button>
        </div>


        <div className="flex flex-col gap-5 px-5 py-5">

          {/* Workspace (RAG scope) */}
          <section>
            <label className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              <Database className="h-3 w-3" /> Knowledge Base
              <span className="ml-1 text-zinc-700">(RAG Agent)</span>
            </label>
            <div className="relative">
              <select
                value={workspaceId ?? ""}
                onChange={(e) => setWorkspaceId(Number(e.target.value) || null)}
                className="w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
              >
                <option value="">— No knowledge base —</option>
                {knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.workspace_id}>
                    {kb.name}
                  </option>
                ))}
                {activeWorkspace && (
                  <option value={activeWorkspace.id}>{activeWorkspace.name}</option>
                )}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3 w-3 text-zinc-500" />
            </div>
          </section>

          {/* Document (Analytics + ML scope) */}
          <section>
            <label className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              <BarChart3 className="h-3 w-3" /> Dataset Document
              <span className="ml-1 text-zinc-700">(Analytics + ML)</span>
            </label>
            <div className="relative">
              <select
                value={docId ?? ""}
                onChange={(e) => setDocId(Number(e.target.value) || null)}
                className="w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
              >
                <option value="">— No dataset —</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.file_name || `Document ${doc.id}`}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3 w-3 text-zinc-500" />
            </div>
          </section>

          {/* Advanced Options */}
          <section className="flex flex-col gap-2">
            <label className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Options
            </label>

            {/* RAG depth */}
            <div className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
              <span className="text-xs text-zinc-400">RAG Depth (top_k)</span>
              <input
                type="number"
                min={1} max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-14 rounded border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-center text-xs text-zinc-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            {/* Generate report toggle */}
            <label className="flex cursor-pointer items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
              <div className="flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 text-purple-400" />
                <span className="text-xs text-zinc-300">Generate Report</span>
              </div>
              <input
                type="checkbox"
                checked={generateReport}
                onChange={(e) => setGenerateReport(e.target.checked)}
                className="accent-indigo-500"
              />
            </label>

            {/* Report format */}
            {generateReport && (
              <div className="relative">
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value)}
                  className="w-full appearance-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
                >
                  {["pdf", "excel", "pptx", "png", "markdown"].map((f) => (
                    <option key={f} value={f}>{f.toUpperCase()}</option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3 w-3 text-zinc-500" />
              </div>
            )}
          </section>

          {/* Suggestions */}
          <section>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
              Example Questions
            </label>
            <div className="flex flex-col gap-1">
              {SUGGESTIONS.slice(0, 4).map((s) => (
                <button
                  key={s}
                  onClick={() => setQuestion(s)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2 text-left text-[10px] text-zinc-400 hover:border-indigo-500/30 hover:text-zinc-200 transition-colors"
                >
                  {s.length > 70 ? s.slice(0, 70) + "…" : s}
                </button>
              ))}
            </div>
          </section>

          {/* Session History */}
          <section>
            <button
              onClick={() => { setShowHistory(!showHistory); if (!showHistory) loadSessions(); }}
              className="flex w-full items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 hover:text-zinc-300"
            >
              <History className="h-3 w-3" />
              Past Sessions
              <ChevronRight className={`h-3 w-3 ml-auto transition-transform ${showHistory ? "rotate-90" : ""}`} />
            </button>
            {showHistory && (
              <div className="mt-2 flex flex-col gap-1">
                {pastSessions.length === 0 ? (
                  <p className="text-[10px] text-zinc-600">No past sessions yet.</p>
                ) : (
                  pastSessions.map((s) => (
                    <div key={s.session_id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2">
                      <p className="text-[10px] font-medium text-zinc-300 leading-tight">{s.question.slice(0, 60)}…</p>
                      <p className="mt-1 text-[9px] text-zinc-600">
                        {s.agents_run.length} agents · {(s.total_latency_ms / 1000).toFixed(1)}s · {new Date(s.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))
                )}
              </div>
            )}
          </section>
        </div>
      </div>

      {/* ── Right Main Panel ───────────────────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Question Input Bar */}
        <div className="border-b border-zinc-800 bg-zinc-900/40 px-6 py-4">
          <div className="flex items-end gap-3">
            <div className="flex-1">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && phase === "idle") { e.preventDefault(); handleAsk(); } }}
                placeholder="Ask your AI agents a decision question… e.g. 'What are the main churn drivers and how confident is the model?'"
                rows={2}
                disabled={phase !== "idle" && phase !== "done" && phase !== "error"}
                className="w-full resize-none rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-2">
              {(phase === "idle" || phase === "done" || phase === "error") ? (
                <>
                  {phase !== "idle" && (
                    <button onClick={handleReset} className="rounded-lg border border-zinc-700 p-2 text-zinc-500 hover:text-zinc-300 transition-colors">
                      <RotateCcw className="h-4 w-4" />
                    </button>
                  )}
                  <button
                    onClick={handleAsk}
                    disabled={!question.trim()}
                    className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-900/30 hover:from-indigo-400 hover:to-purple-500 disabled:opacity-40 transition-all"
                  >
                    {phase === "idle" ? <Send className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </button>
                </>
              ) : (
                <button onClick={handleStop} className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-600/20 border border-red-500/30 text-red-400 hover:bg-red-600/30 transition-colors">
                  <StopCircle className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-y-auto px-6 py-5 gap-5">

          {/* Error */}
          {errorMsg && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              <p className="text-xs text-red-300">{errorMsg}</p>
            </div>
          )}

          {/* Phase: Planning indicator */}
          {phase === "planning" && (
            <div className="flex items-center gap-3 rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
              <div>
                <p className="text-xs font-semibold text-indigo-300">Manager Agent is planning...</p>
                <p className="text-[10px] text-indigo-500">Analyzing your question and selecting the right agents</p>
              </div>
            </div>
          )}

          {/* Execution Plan */}
          {plan.length > 0 && (
            <div>
              <div className="mb-2.5 flex items-center gap-2">
                <Zap className="h-3.5 w-3.5 text-indigo-400" />
                <span className="text-xs font-semibold text-zinc-300">Execution Plan</span>
                <span className="rounded-full bg-indigo-600/20 px-2 py-0.5 text-[10px] text-indigo-400">{plan.length} agents</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {plan.map((step, i) => {
                  const meta = AGENT_META[step.agent];
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <div className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[11px] font-semibold ${meta?.bg || "bg-zinc-800 border-zinc-700"} ${meta?.color || "text-zinc-400"}`}>
                        {meta?.icon}
                        {meta?.label || step.agent}
                      </div>
                      {i < plan.length - 1 && <ChevronRight className="h-3 w-3 text-zinc-700" />}
                    </div>
                  );
                })}
                <ChevronRight className="h-3 w-3 text-zinc-700" />
                <div className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800/60 px-2.5 py-1.5 text-[11px] font-semibold text-zinc-400">
                  <Star className="h-3 w-3" />
                  Final Answer
                </div>
              </div>
            </div>
          )}

          {/* Agent Pipeline Cards */}
          {agents.length > 0 && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-3.5 w-3.5 text-zinc-500" />
                <span className="text-xs font-semibold text-zinc-400">Agent Pipeline</span>
              </div>
              {agents.map((agent, i) => {
                const meta = AGENT_META[agent.name];
                return (
                  <div
                    key={i}
                    className={`rounded-xl border transition-all duration-300 overflow-hidden ${
                      agent.status === "running"
                        ? "border-indigo-500/40 bg-indigo-500/5 shadow-lg shadow-indigo-900/20"
                        : agent.status === "success"
                        ? "border-emerald-500/20 bg-emerald-500/5"
                        : agent.status === "error"
                        ? "border-red-500/20 bg-red-500/5"
                        : agent.status === "skipped"
                        ? "border-zinc-800 bg-zinc-900/30 opacity-60"
                        : "border-zinc-800 bg-zinc-900/50"
                    }`}
                  >
                    <button
                      className="flex w-full items-center gap-3 px-4 py-3 text-left"
                      onClick={() =>
                        setAgents((prev) =>
                          prev.map((a, j) => j === i ? { ...a, expanded: !a.expanded } : a)
                        )
                      }
                    >
                      <span className="shrink-0">{STATUS_ICON[agent.status]}</span>
                      <span className={`shrink-0 ${meta?.color || "text-zinc-400"}`}>{meta?.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-zinc-200">
                            {meta?.label || agent.name}
                          </span>
                          {agent.status === "running" && (
                            <span className="text-[9px] font-bold text-indigo-400 animate-pulse">RUNNING</span>
                          )}
                          {agent.status === "success" && agent.latency_ms > 0 && (
                            <span className="text-[9px] text-zinc-600">{agent.latency_ms}ms</span>
                          )}
                        </div>
                        <p className="mt-0.5 text-[10px] text-zinc-500 truncate">{agent.task}</p>
                        {agent.summary && (
                          <p className="mt-1 text-[11px] text-zinc-400 leading-relaxed">{agent.summary}</p>
                        )}
                      </div>
                      {agent.status === "success" && (
                        <ChevronRight className={`h-3.5 w-3.5 text-zinc-600 transition-transform ${agent.expanded ? "rotate-90" : ""}`} />
                      )}
                    </button>

                    {/* Expanded tool calls */}
                    {agent.expanded && agent.tool_calls.length > 0 && (
                      <div className="border-t border-zinc-800 bg-zinc-900/60 px-4 py-2.5">
                        <p className="mb-1.5 text-[9px] font-semibold uppercase tracking-wider text-zinc-600">
                          Tools Called
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {agent.tool_calls.map((tc, ti) => (
                            <span key={ti} className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-[10px] text-zinc-400">
                              {tc}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Synthesizing indicator */}
          {phase === "synthesizing" && (
            <div className="flex items-center gap-3 rounded-xl border border-purple-500/20 bg-purple-500/5 px-4 py-3">
              <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
              <div>
                <p className="text-xs font-semibold text-purple-300">Synthesizing final answer...</p>
                <p className="text-[10px] text-purple-500">Manager Agent is combining all agent outputs</p>
              </div>
            </div>
          )}

          {/* Final Answer */}
          {finalAnswer && (
            <div ref={answerRef} className="flex flex-col gap-4">
              {/* Confidence + meta row */}
              <div className="flex flex-wrap items-center gap-2">
                <div className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-bold ${confidenceBg} ${confidenceColor}`}>
                  <Shield className="h-3 w-3" />
                  Confidence: {Math.round(confidence * 100)}%
                </div>
                {sessionId && (
                  <span className="text-[10px] text-zinc-600 font-mono">ID: {sessionId.slice(0, 20)}…</span>
                )}
                {totalLatency > 0 && (
                  <span className="flex items-center gap-1 text-[10px] text-zinc-600">
                    <Clock className="h-3 w-3" />
                    {(totalLatency / 1000).toFixed(1)}s total
                  </span>
                )}
                {sessionCost > 0 && (
                  <span className="flex items-center gap-1 text-[10px] text-indigo-400 font-mono">
                    <DollarSign className="h-3 w-3" />
                    ${sessionCost.toFixed(5)}
                  </span>
                )}
                {(sessionTokensIn + sessionTokensOut) > 0 && (
                  <span className="text-[10px] text-zinc-600">
                    ({(sessionTokensIn + sessionTokensOut).toLocaleString()} tokens)
                  </span>
                )}
                <span className="ml-auto flex items-center gap-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] text-emerald-400 font-semibold">

                  <CheckCircle2 className="h-3 w-3" />
                  Complete
                </span>
              </div>

              {/* Answer card */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
                <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900 px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <Star className="h-3.5 w-3.5 text-amber-400" />
                    <span className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">Final Answer</span>
                  </div>
                </div>
                <div className="px-5 py-4 max-h-[50vh] overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-zinc-300">
                    {finalAnswer}
                  </pre>
                </div>
              </div>

              {/* Citations */}
              {citations.length > 0 && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
                  <p className="mb-2.5 text-[11px] font-semibold text-amber-400 uppercase tracking-wider">
                    Citations ({citations.length})
                  </p>
                  <div className="flex flex-col gap-2">
                    {citations.slice(0, 5).map((c, i) => (
                      <div key={i} className="rounded-lg border border-amber-500/10 bg-amber-500/5 px-3 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-semibold text-amber-300">
                            {c.source} · Page {c.page}
                          </span>
                          <span className="text-[9px] text-amber-600">{Math.round(c.score * 100)}% match</span>
                        </div>
                        <p className="text-[10px] text-zinc-400 leading-relaxed line-clamp-2">{c.snippet}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Empty state */}
          {phase === "idle" && !finalAnswer && (
            <div className="flex flex-1 flex-col items-center justify-center gap-6 py-12 text-center">
              <div className="relative">
                <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 via-purple-500/20 to-pink-500/20 border border-indigo-500/20">
                  <Sparkles className="h-10 w-10 text-indigo-400" />
                </div>
                <div className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-emerald-500 border-2 border-zinc-900 animate-pulse" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">AI Decision Intelligence</h2>
                <p className="mt-2 max-w-md text-sm text-zinc-500">
                  Ask any business question. The{" "}
                  <span className="font-semibold text-indigo-400">Manager Agent</span> will dynamically
                  select the right combination of Analytics, ML, RAG, and Report agents to answer it.
                </p>
              </div>
              {/* Architecture diagram */}
              <div className="flex items-center gap-2 flex-wrap justify-center max-w-lg">
                <div className="rounded-lg border border-zinc-700 bg-zinc-800/60 px-3 py-2 text-xs text-zinc-300 font-semibold">
                  👤 CEO Question
                </div>
                <ChevronRight className="h-4 w-4 text-zinc-600" />
                <div className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-3 py-2 text-xs text-indigo-300 font-semibold">
                  ✦ Manager Agent
                </div>
                <ChevronRight className="h-4 w-4 text-zinc-600" />
                <div className="flex flex-col gap-1">
                  {Object.entries(AGENT_META).map(([k, v]) => (
                    <div key={k} className={`flex items-center gap-1.5 rounded border px-2.5 py-1 text-[10px] font-semibold ${v.bg} ${v.color}`}>
                      {v.icon} {v.label}
                    </div>
                  ))}
                </div>
                <ChevronRight className="h-4 w-4 text-zinc-600" />
                <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-300 font-semibold">
                  ⭐ Final Answer
                </div>
              </div>
              <div className="flex items-start gap-2.5 max-w-sm rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-3 text-left">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
                <p className="text-[11px] text-indigo-300">
                  Select a workspace and/or dataset on the left, type your question, and press{" "}
                  <kbd className="rounded bg-indigo-900 px-1 py-0.5 font-mono text-[10px]">Enter</kbd> to
                  launch the agent pipeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
