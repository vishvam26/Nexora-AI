"use client";

import { useState, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import { KnowledgeDocument } from "../types/chat";
import {
  Terminal, Play, Loader2, AlertCircle, CheckCircle2,
  Code, Sparkles, Send, FileText, Image as ImageIcon,
  ChevronDown, HelpCircle, RefreshCw
} from "lucide-react";

import { apiService, API_BASE_URL } from "../services/api-service";

const API_BASE = API_BASE_URL;

interface SandboxResult {
  stdout: string;
  stderr: string;
  return_code: number;
  chart_path?: string;
  chart_id?: string;
}

export default function PythonStudio() {
  const { token, activeWorkspace } = useChatStore();
  const [localDocs, setLocalDocs] = useState<KnowledgeDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  // Panel sizing state
  const [rightPanelWidth, setRightPanelWidth] = useState(450);
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback((mouseDownEvent: React.MouseEvent) => {
    mouseDownEvent.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((mouseMoveEvent: MouseEvent) => {
    if (isResizing) {
      const newWidth = window.innerWidth - mouseMoveEvent.clientX;
      if (newWidth > 280 && newWidth < 900) {
        setRightPanelWidth(newWidth);
      }
    }
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener("mousemove", resize);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [resize, stopResizing]);

  // Document context
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  // Editor/Script state
  const [code, setCode] = useState(
    "# Auto-loaded CSV Dataset into pandas DataFrame 'df'\nprint('--- DATASET INFORMATION ---')\nprint(df.info())\n\nprint('\\n--- FIRST 5 ROWS ---')\nprint(df.head())\n\n# Generate Histogram Plot\ndf.hist(bins=15, figsize=(8, 5))\nplt.tight_layout()\nplt.show()"
  );
  const [result, setResult] = useState<SandboxResult | null>(null);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // AI Copilot state
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [generatingCode, setGeneratingCode] = useState(false);

  const headers = useCallback(() => ({
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "69420",
    Authorization: `Bearer ${token}`
  }), [token]);

  const loadWorkspaceDocs = useCallback(async () => {
    if (!activeWorkspace?.id) return;
    setLoadingDocs(true);
    try {
      const bases = await apiService.fetchKnowledgeBases(activeWorkspace.id);
      const docPromises = bases.map(async (kb) => {
        try {
          const res = await fetch(`${API_BASE}/knowledge/documents?kb_id=${kb.id}`, { headers: headers() });
          if (res.ok) {
            const data = await res.json();
            return data.documents || [];
          }
        } catch { /* ignore */ }
        return [];
      });
      const results = await Promise.all(docPromises);
      const allDocs = results.flat();
      setLocalDocs(allDocs);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
    setLoadingDocs(false);
  }, [activeWorkspace, headers]);

  useEffect(() => {
    loadWorkspaceDocs();
  }, [loadWorkspaceDocs]);

  const handleRunCode = async () => {
    if (!selectedDocId) {
      setErrorMsg("Please select a target dataset document first.");
      return;
    }
    if (!code.trim()) return;

    setRunning(true);
    setErrorMsg("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/python/execute/${selectedDocId}`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Sandbox script crashed.");
      }
      setResult(data);
    } catch (e: any) {
      setErrorMsg(e.message || "Execution error occurred");
    } finally {
      setRunning(false);
    }
  };

  const getOrCreateConversationId = async () => {
    const state = useChatStore.getState();
    const existingSystem = state.conversations.find(c => c.title.toLowerCase().startsWith("system "));
    if (existingSystem) {
      return existingSystem.id;
    }
    const wsId = state.activeWorkspace?.id || state.workspaces[0]?.id;
    if (!wsId) {
      throw new Error("No active workspace found to start chat.");
    }
    const convo = await apiService.createConversation("System Copilot Chat", wsId);
    return convo.id;
  };

  const handleAICopilot = async () => {
    if (!naturalLanguage.trim()) return;
    setGeneratingCode(true);
    try {
      const prompt = `Convert this natural language data request to a clean Pandas/Matplotlib script. The load path is automatically set as global DF_PATH variable. Load dataframe as: df = pd.read_csv(DF_PATH). Task: "${naturalLanguage}". Reply ONLY with the python script code block. No markdown backticks.`;
      
      const convoId = await getOrCreateConversationId();
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          conversation_id: convoId,
          message: prompt,
          grounded: false,
          provider: "gemini"
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "AI Copilot failed to generate python script.");
      }
      if (data.assistant_message?.content) {
        let content = data.assistant_message.content;
        if (content.includes("</think>")) {
          const parts = content.split("</think>");
          content = parts[parts.length - 1];
        }
        const cleanCode = content.replace(/```python|```/g, "").trim();
        setCode(cleanCode);
        setErrorMsg("");
      }
    } catch (err: any) {
      console.error("AI Copilot failed:", err);
      setErrorMsg(err.message || "AI Copilot failed to generate code.");
    }
    setGeneratingCode(false);
  };

  // Construct absolute image download source (points to backend root static storage)
  const BACKEND_ROOT = API_BASE.replace("/api/v1", "");
  const [chartBlobUrl, setChartBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (result?.chart_path) {
      const fetchChart = async () => {
        try {
          const res = await fetch(`${BACKEND_ROOT}${result.chart_path}`, {
            headers: headers()
          });
          if (res.ok) {
            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            setChartBlobUrl(blobUrl);
          } else {
            setChartBlobUrl(null);
          }
        } catch (err) {
          console.error("Failed to fetch chart image:", err);
          setChartBlobUrl(null);
        }
      };
      fetchChart();
    } else {
      setChartBlobUrl(null);
    }
  }, [result, headers, BACKEND_ROOT]);

  return (
    <div className="flex h-screen w-full overflow-hidden text-[#f4f4f5] bg-transparent">
      {/* ── Left Workspace: Editor & Copilot ─────────────────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden" style={{ background: "var(--panel-bg)", borderRight: "1px solid var(--border)", backdropFilter: "blur(12px)" }}>
        {/* Workspace Toolbar */}
        <div className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 border border-indigo-500/30">
              <Code className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Python Sandbox</h2>
              <p className="text-[10px] text-zinc-500">Isolate Pandas & Matplotlib executions</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Target Selector */}
            <div className="relative">
              <select
                value={selectedDocId ?? ""}
                onChange={(e) => setSelectedDocId(Number(e.target.value) || null)}
                className="appearance-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none pr-8"
              >
                <option value="">— Select Dataset —</option>
                {localDocs.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename || `Document ${doc.id}`}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
            </div>

            <button
              onClick={handleRunCode}
              disabled={running || !selectedDocId || !code.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              Run Script
            </button>
          </div>
        </div>

        {/* Editor Box */}
        <div className="flex-1 p-5 flex flex-col gap-4 overflow-hidden">
          <div className="flex-1 relative rounded-xl border border-zinc-700 bg-zinc-900 flex flex-col">
            <div className="border-b border-zinc-800 bg-zinc-950 px-4 py-2 flex items-center gap-1.5">
              <Terminal className="h-3.5 w-3.5 text-indigo-400" />
              <span className="font-mono text-[10px] text-zinc-500">main.py (Read-Only Dataset Mode)</span>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="flex-1 w-full bg-[#0d0d0e] p-4 font-mono text-xs text-indigo-200 placeholder:text-zinc-700 focus:outline-none resize-y overflow-y-auto min-h-[150px] rounded-b-xl"
            />
          </div>

          {/* AI SQL Copilot */}
          <div className="flex items-center gap-2.5 rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-2.5">
            <Sparkles className="h-4 w-4 text-indigo-400 shrink-0" />
            <input
              type="text"
              value={naturalLanguage}
              onChange={(e) => setNaturalLanguage(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAICopilot(); }}
              placeholder="Ask AI Copilot to code (e.g. 'Plot hist of Age column' or 'group by department and average salary')"
              className="flex-1 bg-transparent text-xs text-zinc-200 placeholder:text-zinc-500 focus:outline-none"
            />
            <button
              onClick={handleAICopilot}
              disabled={generatingCode || !naturalLanguage.trim()}
              className="rounded p-1 text-indigo-400 hover:bg-indigo-500/10 disabled:opacity-30"
            >
              {generatingCode ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Resize Divider handle */}
      <div
        onMouseDown={startResizing}
        className={`w-1 hover:w-1.5 cursor-col-resize bg-zinc-800 hover:bg-indigo-500 transition-all shrink-0 h-full ${
          isResizing ? "bg-indigo-600 w-1.5" : ""
        }`}
      />

      {/* ── Right Panel: Outputs Console & Generated Charts ─────────── */}
      <div
        style={{ width: `${rightPanelWidth}px`, background: "var(--panel-bg)", backdropFilter: "blur(8px)" }}
        className="flex shrink-0 flex-col overflow-hidden border-l border-zinc-800"
      >
        <div className="border-b border-zinc-800 px-5 py-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">Console & Visualizations</h2>
          <p className="text-[10px] text-zinc-500">Subprocess log outputs</p>
        </div>

        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
          {errorMsg && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              <p className="text-xs text-red-300">{errorMsg}</p>
            </div>
          )}

          {result ? (
            <div className="flex flex-col gap-5">
              {/* STDOUT console logs */}
              <div className="rounded-xl border border-zinc-800" style={{ background: "rgba(18,18,22,0.6)" }}>
                <div className="border-b border-zinc-800 bg-zinc-900 px-4 py-2">
                  <span className="text-[9px] font-semibold text-zinc-400 uppercase tracking-wider">Console output (STDOUT)</span>
                </div>
                <div className="p-4 font-mono text-xs text-emerald-400/90 leading-relaxed min-h-[140px] max-h-[320px] overflow-y-auto whitespace-pre-wrap rounded-b-xl border-t border-zinc-800/40 select-text">
                  {result.stdout || <span className="text-zinc-600 italic">Script completed with no STDOUT messages.</span>}
                </div>
              </div>

              {/* Chart Plot Visualizer */}
              {chartBlobUrl ? (
                <div className="rounded-xl border border-indigo-500/15 bg-indigo-500/5 overflow-hidden">
                  <div className="border-b border-indigo-500/10 bg-indigo-500/10 px-4 py-2 flex items-center gap-1.5">
                    <ImageIcon className="h-3.5 w-3.5 text-indigo-400" />
                    <span className="text-[9px] font-semibold text-indigo-300 uppercase tracking-wider">Exported plot visualization</span>
                  </div>
                  <div className="p-4 flex items-center justify-center bg-white/5">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={chartBlobUrl} alt="Generated Matplotlib Chart" className="max-h-96 w-full max-w-full object-contain rounded" />
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 text-center text-zinc-600 text-xs">
                  No visual charts exported by Matplotlib.
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 py-12 text-center text-zinc-600">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800">
                <Terminal className="h-6 w-6 text-zinc-700" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-zinc-500">No logs generated</h3>
                <p className="mt-1 max-w-xs text-[10px] text-zinc-700">
                  Select a document and click Run Script. Output logs and generated plots will load dynamically.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
