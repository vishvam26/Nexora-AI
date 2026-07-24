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

  // Auto-completion suggestions dictionary
  const AUTOCOMPLETE_ITEMS = [
    { label: "df.head()", insert: "df.head()", doc: "Return first 5 rows of DataFrame" },
    { label: "df.info()", insert: "df.info()", doc: "Print concise summary of DataFrame" },
    { label: "df.describe()", insert: "df.describe()", doc: "Generate descriptive statistics" },
    { label: "df.dropna()", insert: "df.dropna()", doc: "Remove missing values" },
    { label: "df.fillna()", insert: "df.fillna(0)", doc: "Fill missing values" },
    { label: "df.groupby()", insert: "df.groupby('')", doc: "Group DataFrame using a mapper" },
    { label: "df.corr()", insert: "df.corr()", doc: "Compute pairwise correlation" },
    { label: "pd.read_csv()", insert: "pd.read_csv('')", doc: "Read CSV dataset into DataFrame" },
    { label: "pd.DataFrame()", insert: "pd.DataFrame()", doc: "Two-dimensional tabular data structure" },
    { label: "plt.figure()", insert: "plt.figure(figsize=(10, 6))", doc: "Create a new figure" },
    { label: "plt.title()", insert: "plt.title('')", doc: "Set title for current axes" },
    { label: "plt.xlabel()", insert: "plt.xlabel('')", doc: "Set x-axis label" },
    { label: "plt.ylabel()", insert: "plt.ylabel('')", doc: "Set y-axis label" },
    { label: "plt.show()", insert: "plt.show()", doc: "Display all open figures" },
    { label: "sns.heatmap()", insert: "sns.heatmap(df.corr(), annot=True)", doc: "Plot rectangular data as color-encoded matrix" },
    { label: "train_test_split()", insert: "from sklearn.model_selection import train_test_split\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)", doc: "Split arrays into random train and test subsets" },
    { label: "RandomForestClassifier()", insert: "from sklearn.ensemble import RandomForestClassifier\nmodel = RandomForestClassifier()\nmodel.fit(X_train, y_train)", doc: "Random Forest Machine Learning Estimator" }
  ];

  const [suggestions, setSuggestions] = useState<typeof AUTOCOMPLETE_ITEMS>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [cursorWord, setCursorWord] = useState("");

  const handleCodeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setCode(val);

    const cursorPos = e.target.selectionStart;
    const textBefore = val.slice(0, cursorPos);
    const lastWordMatch = textBefore.match(/[\w\.]+$ /);
    const word = lastWordMatch ? lastWordMatch[0].trim() : textBefore.split(/\s+/).pop() || "";

    if (word.length >= 2) {
      const filtered = AUTOCOMPLETE_ITEMS.filter(item => 
        item.label.toLowerCase().includes(word.toLowerCase()) || 
        item.insert.toLowerCase().includes(word.toLowerCase())
      );
      if (filtered.length > 0) {
        setSuggestions(filtered);
        setShowSuggestions(true);
        setCursorWord(word);
        return;
      }
    }
    setShowSuggestions(false);
  };

  const applySuggestion = (insertText: string) => {
    setCode(prev => {
      if (cursorWord) {
        const lastIdx = prev.lastIndexOf(cursorWord);
        if (lastIdx !== -1) {
          return prev.slice(0, lastIdx) + insertText + prev.slice(lastIdx + cursorWord.length);
        }
      }
      return prev + "\n" + insertText;
    });
    setShowSuggestions(false);
  };

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

  // Active Output Tab state
  const [outputTab, setOutputTab] = useState<"console" | "chart" | "eval">("console");

  const lineCount = code.split("\n").length;
  const lineNumbers = Array.from({ length: Math.max(lineCount, 15) }, (_, i) => String(i + 1).padStart(2, "0"));

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden text-[#f4f4f5] bg-[#09090b]">
      {/* ── Top Header Toolbar ────────────────────────────────────────── */}
      <div className="border-b border-zinc-800/80 px-6 py-2.5 flex items-center justify-between bg-[#0d0d11] shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 border border-indigo-500/30">
            <Code className="h-4 w-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Python Sandbox IDE <span className="text-[9px] font-normal px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PRO COMPILER</span>
            </h2>
            <p className="text-[10px] text-zinc-500">Pandas, Matplotlib & AI Data Analytics Studio</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Target Dataset Selector */}
          <div className="relative">
            <select
              value={selectedDocId ?? ""}
              onChange={(e) => setSelectedDocId(Number(e.target.value) || null)}
              className="appearance-none rounded-lg border border-zinc-700/80 bg-[#121217] px-3.5 py-1.5 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none pr-8 font-medium"
            >
              <option value="">— Select Target Dataset —</option>
              {localDocs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  📄 {doc.filename || `Document ${doc.id}`}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
          </div>

          <button
            onClick={handleRunCode}
            disabled={running || !selectedDocId || !code.trim()}
            className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-1.5 text-xs font-bold text-white hover:from-indigo-500 hover:to-violet-500 disabled:opacity-40 transition shadow-md shadow-indigo-600/20"
          >
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
            Execute →
          </button>
        </div>
      </div>

      {/* ── Main Resizable IDE Split Body ─────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* ── Left Half: Code Editor (Dynamic Width) ────────────────── */}
        <div className="flex flex-1 flex-col overflow-hidden bg-[#0d0d11]">
          {/* File Tab Header */}
          <div className="border-b border-zinc-800 bg-[#09090c] px-4 py-2 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded bg-[#16161f] border border-zinc-800 text-[11px] font-mono text-indigo-400 flex items-center gap-1.5">
                <Terminal className="h-3 w-3 text-indigo-400" /> main.py
              </span>
            </div>
            <span className="text-[10px] text-zinc-600 font-mono">Python 3.10 Kernel</span>
          </div>

          {/* Code Editor with Line Numbers */}
          <div className="flex-1 flex overflow-hidden bg-[#08080a] relative">
            {/* Line Numbers */}
            <div className="w-12 bg-[#0a0a0e] border-r border-zinc-800/60 py-4 select-none flex flex-col font-mono text-[11px] text-zinc-600 text-right pr-3 shrink-0 leading-[1.6]">
              {lineNumbers.map((num) => (
                <div key={num}>{num}</div>
              ))}
            </div>

            {/* Editable Textarea */}
            <textarea
              value={code}
              onChange={handleCodeChange}
              className="flex-1 w-full bg-transparent p-4 font-mono text-xs text-indigo-200 placeholder:text-zinc-700 focus:outline-none overflow-y-auto leading-[1.6] select-text"
              style={{ tabSize: 4 }}
            />

            {/* Smart Autocomplete Dropdown Popup (IntelliSense) */}
            {showSuggestions && (
              <div className="absolute bottom-4 left-16 z-30 max-w-sm w-80 rounded-xl border border-indigo-500/30 bg-[#12121a]/95 p-1.5 shadow-2xl backdrop-blur-xl animate-fade-in-up">
                <div className="px-2.5 py-1 text-[9px] font-bold uppercase tracking-widest text-indigo-400 border-b border-zinc-800/80 flex items-center justify-between">
                  <span>Data Science IntelliSense</span>
                  <span className="text-[8px] text-zinc-500 font-mono">Press Tab or Click</span>
                </div>
                <div className="max-h-48 overflow-y-auto mt-1 space-y-0.5">
                  {suggestions.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => applySuggestion(item.insert)}
                      className="w-full text-left px-3 py-1.5 rounded-lg hover:bg-indigo-600/30 transition flex flex-col group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-semibold text-indigo-200 group-hover:text-white">{item.label}</span>
                        <span className="text-[9px] font-mono text-zinc-500">Snippet</span>
                      </div>
                      <span className="text-[9px] text-zinc-400 truncate mt-0.5">{item.doc}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Copilot Bar */}
          <div className="border-t border-zinc-800 bg-[#0d0d11] p-3 shrink-0">
            <div className="flex items-center gap-2.5 rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-2">
              <Sparkles className="h-4 w-4 text-indigo-400 shrink-0" />
              <input
                type="text"
                value={naturalLanguage}
                onChange={(e) => setNaturalLanguage(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleAICopilot(); }}
                placeholder="Ask AI Copilot to generate Python code (e.g. 'Plot histogram of columns' or 'Filter rows where score > 80')"
                className="flex-1 bg-transparent text-xs text-zinc-200 placeholder:text-zinc-500 focus:outline-none"
              />
              <button
                onClick={handleAICopilot}
                disabled={generatingCode || !naturalLanguage.trim()}
                className="rounded-lg p-1.5 text-indigo-400 hover:bg-indigo-500/20 disabled:opacity-30 transition"
              >
                {generatingCode ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>

        {/* ── Resizing Handle Divider ────────────────────────────────── */}
        <div
          onMouseDown={startResizing}
          className={`w-1.5 hover:w-2 cursor-col-resize bg-zinc-800 hover:bg-indigo-500 transition-all shrink-0 h-full z-20 flex items-center justify-center ${
            isResizing ? "bg-indigo-600 w-2" : ""
          }`}
          title="Drag left/right to resize Editor and Output panels"
        >
          <div className="h-8 w-0.5 bg-zinc-600 rounded-full" />
        </div>

        {/* ── Right Half: Resizable Output & Visualizations Panel ────── */}
        <div
          style={{ width: `${rightPanelWidth}px` }}
          className="flex shrink-0 flex-col overflow-hidden bg-[#0c0c0f] border-l border-zinc-800"
        >
          {/* JDoodle Style Output Tabs Header */}
          <div className="border-b border-zinc-800 bg-[#09090c] px-3 py-1.5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-1">
              <button
                onClick={() => setOutputTab("console")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  outputTab === "console" ? "bg-indigo-600 text-white shadow-sm" : "text-zinc-400 hover:bg-zinc-800/60"
                }`}
              >
                Output (Console)
              </button>
              <button
                onClick={() => setOutputTab("chart")}
                className={`px-3 py-1 rounded text-xs font-semibold transition flex items-center gap-1.5 ${
                  outputTab === "chart" ? "bg-indigo-600 text-white shadow-sm" : "text-zinc-400 hover:bg-zinc-800/60"
                }`}
              >
                Visualizations {chartBlobUrl && <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />}
              </button>
              <button
                onClick={() => setOutputTab("eval")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  outputTab === "eval" ? "bg-indigo-600 text-white shadow-sm" : "text-zinc-400 hover:bg-zinc-800/60"
                }`}
              >
                Evaluation & Logs
              </button>
            </div>
          </div>

          {/* Output Content Body */}
          <div className="flex-1 overflow-y-auto p-4 bg-[#070709]">
            {errorMsg && (
              <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 mb-4 text-red-300">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                <p className="text-xs">{errorMsg}</p>
              </div>
            )}

            {/* TAB 1: Console STDOUT */}
            {outputTab === "console" && (
              <div className="h-full flex flex-col rounded-xl border border-zinc-800 bg-[#050507] overflow-hidden">
                <div className="border-b border-zinc-800/80 bg-zinc-950 px-4 py-2 flex items-center justify-between shrink-0">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Subprocess STDOUT Stream</span>
                  <span className="text-[9px] text-emerald-400 font-mono">Status: 200 OK</span>
                </div>
                <div className="flex-1 p-4 font-mono text-xs text-emerald-400 leading-relaxed overflow-y-auto whitespace-pre-wrap select-text">
                  {result ? (
                    result.stdout || <span className="text-zinc-600 italic">Script executed with no console output.</span>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-600 text-center py-12">
                      <Terminal className="h-8 w-8 text-zinc-700 mb-2 opacity-50" />
                      <p className="text-xs">No execution output yet.</p>
                      <p className="text-[10px] text-zinc-700 mt-1">Select a dataset and click "Execute →"</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: Visualizations Matplotlib Chart */}
            {outputTab === "chart" && (
              <div className="h-full flex flex-col rounded-xl border border-zinc-800 bg-[#050507] overflow-hidden">
                <div className="border-b border-zinc-800/80 bg-zinc-950 px-4 py-2 flex items-center justify-between shrink-0">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Matplotlib Rendered Plot</span>
                  <span className="text-[9px] text-zinc-500 font-mono">4K HD Chart Export</span>
                </div>
                <div className="flex-1 p-4 flex items-center justify-center overflow-auto bg-black/40">
                  {chartBlobUrl ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={chartBlobUrl} alt="Generated Chart" className="max-h-full max-w-full object-contain rounded-lg shadow-2xl" />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-zinc-600 text-center py-12">
                      <ImageIcon className="h-8 w-8 text-zinc-700 mb-2 opacity-50" />
                      <p className="text-xs">No visual charts exported by Matplotlib.</p>
                      <p className="text-[10px] text-zinc-700 mt-1">Call plt.show() in your script to generate charts.</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: Errors & Evaluation */}
            {outputTab === "eval" && (
              <div className="space-y-4">
                <div className="rounded-xl border border-zinc-800 bg-[#0c0c10] p-4 space-y-2">
                  <h4 className="text-xs font-bold text-zinc-300">Execution Performance</h4>
                  <div className="text-[11px] font-mono text-zinc-400 space-y-1">
                    <div>Return Code: <span className="text-emerald-400">{result?.return_code ?? 0}</span></div>
                    <div>Status: <span className="text-indigo-400">{result ? "Completed" : "Idle"}</span></div>
                    <div>Kernel: Python 3.10 Data Engine</div>
                  </div>
                </div>

                {result?.stderr && (
                  <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-2">
                    <h4 className="text-xs font-bold text-amber-400">STDERR Warnings</h4>
                    <pre className="text-[11px] font-mono text-amber-300/80 whitespace-pre-wrap">{result.stderr}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
