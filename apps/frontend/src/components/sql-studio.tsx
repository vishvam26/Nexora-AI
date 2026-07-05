"use client";

import { useState, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import {
  Database, Play, Loader2, AlertCircle, CheckCircle2,
  Table, HelpCircle, Columns, ChevronDown, ChevronRight,
  Code, Terminal, Sparkles, Send
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
}

interface QueryResult {
  row_count: number;
  headers: string[];
  rows: Record<string, any>[];
}

export default function SQLStudio() {
  const { token } = useChatStore();

  // Schema state
  const [schema, setSchema] = useState<Record<string, TableColumn[]>>({});
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});
  const [loadingSchema, setLoadingSchema] = useState(true);

  // Editor/Query state
  const [query, setQuery] = useState("SELECT * FROM users LIMIT 10;");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // AI Copilot state
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [generatingQuery, setGeneratingQuery] = useState(false);

  const headers = useCallback(() => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  }), [token]);

  const fetchSchema = useCallback(async () => {
    setLoadingSchema(true);
    try {
      const res = await fetch(`${API_BASE}/mcp/schema`, { headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setSchema(data.schema || {});
        // Auto-expand the first table
        const firstTable = Object.keys(data.schema || {})[0];
        if (firstTable) {
          setExpandedTables({ [firstTable]: true });
        }
      }
    } catch { /* ignore */ }
    setLoadingSchema(false);
  }, [headers]);

  useEffect(() => {
    fetchSchema();
  }, [fetchSchema]);

  const handleRunQuery = async (queryText = query) => {
    if (!queryText.trim()) return;
    setRunning(true);
    setErrorMsg("");
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/mcp/query`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ query: queryText })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Query failed to execute.");
      }
      setResult(data);
    } catch (e: any) {
      setErrorMsg(e.message || "Execution error occurred");
    } finally {
      setRunning(false);
    }
  };

  const handleAICopilot = async () => {
    if (!naturalLanguage.trim()) return;
    setGeneratingQuery(true);
    try {
      // Prompt LLM context info from database tables list
      const tablesList = Object.keys(schema).join(", ");
      const prompt = `Convert this natural language to a clean PostgreSQL SELECT query. DB tables: [${tablesList}]. Query: "${naturalLanguage}". Reply ONLY with the SQL block. No comments, no markdown backticks.`;
      
      // Hit direct chat endpoint to translate query
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          conversation_id: 1, // Broad system fallback conversation
          content: prompt
        })
      });
      const data = await res.json();
      if (res.ok && data.content) {
        const cleanSQL = data.content.replace(/```sql|```/g, "").trim();
        setQuery(cleanSQL);
      }
    } catch { /* ignore */ }
    setGeneratingQuery(false);
  };

  const toggleTable = (table: string) => {
    setExpandedTables(prev => ({ ...prev, [table]: !prev[table] }));
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b] text-[#f4f4f5]">
      {/* ── Left Sidebar: Schema Inspector ─────────────────────────── */}
      <div className="flex w-72 shrink-0 flex-col border-r border-zinc-800 overflow-y-auto">
        <div className="border-b border-zinc-800 px-5 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 border border-indigo-500/30">
              <Database className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Schema Inspector</h2>
              <p className="text-[10px] text-zinc-500">Live database columns</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1.5 p-4">
          {loadingSchema ? (
            <div className="flex items-center gap-2 text-zinc-500 p-2 text-xs">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Loading database columns...
            </div>
          ) : Object.keys(schema).length === 0 ? (
            <div className="text-xs text-zinc-600 p-2">No schema metadata reflected.</div>
          ) : (
            Object.entries(schema).map(([tableName, cols]) => (
              <div key={tableName} className="rounded-lg border border-zinc-900 bg-zinc-950/20 overflow-hidden">
                <button
                  onClick={() => toggleTable(tableName)}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-semibold text-zinc-300 hover:bg-zinc-800/40"
                >
                  <div className="flex items-center gap-2">
                    <Table className="h-3.5 w-3.5 text-zinc-500" />
                    <span>{tableName}</span>
                  </div>
                  {expandedTables[tableName] ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                </button>

                {expandedTables[tableName] && (
                  <div className="border-t border-zinc-900 bg-zinc-950/40 px-3 py-2 flex flex-col gap-1.5">
                    {cols.map(c => (
                      <div key={c.name} className="flex items-center justify-between text-[10px] font-mono text-zinc-400">
                        <span className="flex items-center gap-1">
                          <Columns className="h-2.5 w-2.5 text-zinc-600" />
                          {c.name}
                        </span>
                        <span className="text-zinc-600">{c.type.toLowerCase()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Right Content: Query Editor & Table Sandbox ─────────────── */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Editor Area */}
        <div className="border-b border-zinc-800 bg-zinc-900/30 p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-zinc-400" />
              <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">SQL Sandbox</span>
            </div>
            <button
              onClick={() => handleRunQuery()}
              disabled={running || !query.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              Execute Query
            </button>
          </div>

          <div className="relative rounded-xl border border-zinc-700 bg-zinc-900 overflow-hidden">
            <div className="border-b border-zinc-800 bg-zinc-950 px-4 py-2 flex items-center gap-1.5">
              <Code className="h-3.5 w-3.5 text-indigo-400" />
              <span className="font-mono text-[10px] text-zinc-500">Query Editor (PostgreSQL mode)</span>
            </div>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-[#0d0d0e] p-4 font-mono text-xs text-indigo-200 placeholder:text-zinc-700 focus:outline-none min-h-[100px] resize-y"
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
              placeholder="Ask SQL Copilot (e.g. 'Show table row counts' or 'List recent users')"
              className="flex-1 bg-transparent text-xs text-zinc-200 placeholder:text-zinc-500 focus:outline-none"
            />
            <button
              onClick={handleAICopilot}
              disabled={generatingQuery || !naturalLanguage.trim()}
              className="rounded p-1 text-indigo-400 hover:bg-indigo-500/10 disabled:opacity-30"
            >
              {generatingQuery ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Results Area */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">
          {errorMsg && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              <p className="text-xs text-red-300">{errorMsg}</p>
            </div>
          )}

          {result ? (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-semibold text-zinc-300">
                  Execution Complete ({result.row_count} rows found)
                </span>
              </div>

              {/* Data Table */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 overflow-hidden max-w-full">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 bg-zinc-900 text-zinc-500">
                        {result.headers.map((h) => (
                          <th key={h} className="px-4 py-3 font-semibold font-mono text-[10px]">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800 font-mono text-[10px]">
                      {result.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-zinc-800/10 text-zinc-300">
                          {result.headers.map((h) => (
                            <td key={h} className="px-4 py-3 truncate max-w-[200px]" title={String(row[h])}>
                              {row[h] === null ? <span className="text-zinc-700">null</span> : String(row[h])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 py-12 text-center text-zinc-500">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800">
                <Terminal className="h-6 w-6 text-zinc-600" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-zinc-300">Query Sandbox Empty</h3>
                <p className="mt-1 max-w-xs text-xs text-zinc-600">
                  Run a SELECT statement above or ask AI Copilot to fetch database columns.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
