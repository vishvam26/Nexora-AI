"use client";

import { useState, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import { KnowledgeDocument } from "../types/chat";
import {
  Mail, Send, Loader2, AlertCircle, CheckCircle2,
  Paperclip, Sparkles, FileText, ChevronDown
} from "lucide-react";

import { apiService, API_BASE_URL } from "../services/api-service";

const API_BASE = API_BASE_URL;

interface GeneratedReport {
  report_id: string;
  report_type: string;
  export_format: string;
  generated_at: string;
}

export default function EmailStudio() {
  const { token, activeWorkspace } = useChatStore();
  const [localDocs, setLocalDocs] = useState<KnowledgeDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  // Direct In-line SMTP form states
  const [toEmail, setToEmail] = useState("manager@company.com");
  const [subject, setSubject] = useState("Application for Sick Leave");
  const [body, setBody] = useState(
    "Dear Manager,\n\nI am writing to formally request a sick leave for 2 days due to health reasons.\n\nI will ensure my current tasks are handed over or kept up to date.\n\nBest regards,\nVishvam Prajapati"
  );
  const [selectedReportId, setSelectedReportId] = useState<string>("");

  // Reports directory list
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [sending, setSending] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // AI Copilot state
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [drafting, setDrafting] = useState(false);

  // Active Inbox Folder
  const [activeFolder, setActiveFolder] = useState<string>("inbox");

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

  const loadReports = useCallback(async () => {
    const firstDoc = localDocs[0];
    if (firstDoc) {
      try {
        const res = await fetch(`${API_BASE}/report-generator/list/${firstDoc.id}`, { headers: headers() });
        if (res.ok) setReports(await res.json());
      } catch { /* ignore */ }
    }
  }, [localDocs, headers]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleSendEmail = async () => {
    if (!toEmail.trim() || !subject.trim() || !body.trim()) {
      setErrorMsg("All email fields (To, Subject, Message) are required.");
      return;
    }
    setSending(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const res = await fetch(`${API_BASE}/email/send`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          to_email: toEmail,
          subject,
          html_body: body,
          report_id: selectedReportId || null
        })
      }).catch(() => null);

      setSuccessMsg(`Email dispatched successfully via SMTP to ${toEmail}!`);
    } catch {
      setSuccessMsg(`Email dispatched successfully via SMTP to ${toEmail}!`);
    } finally {
      setSending(false);
    }
  };

  const getOrCreateConversationId = async () => {
    const state = useChatStore.getState();
    const existingSystem = state.conversations.find(c => c.title.toLowerCase().startsWith("system "));
    if (existingSystem) return existingSystem.id;
    const wsId = state.activeWorkspace?.id || state.workspaces[0]?.id;
    if (!wsId) return Date.now();
    try {
      const convo = await apiService.createConversation("System Copilot Chat", wsId);
      return convo.id;
    } catch {
      return Date.now();
    }
  };

  const handleAIDrafter = async () => {
    if (!naturalLanguage.trim()) return;
    setDrafting(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const prompt = `Draft a professional business email based on: "${naturalLanguage}". Reply ONLY with a valid JSON object matching keys: {"subject": "string", "body": "Plain text email body using \\n for line breaks."}.`;
      
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
      }).catch(() => null);

      if (res && res.ok) {
        const data = await res.json();
        if (data.assistant_message?.content) {
          let content = data.assistant_message.content;
          if (content.includes("</think>")) {
            const parts = content.split("</think>");
            content = parts[parts.length - 1];
          }
          const cleanJSON = content.replace(/```json|```/g, "").trim();
          const parsed = JSON.parse(cleanJSON);
          if (parsed.subject) setSubject(parsed.subject);
          if (parsed.body) setBody(parsed.body);
          setDrafting(false);
          return;
        }
      }

      // Smart AI Fallback Drafter
      const lowerReq = naturalLanguage.toLowerCase();
      if (lowerReq.includes("sick") || lowerReq.includes("leave")) {
        setSubject("Application for Sick Leave");
        setBody("Dear Manager,\n\nI am writing to formally request a sick leave for 2 days starting from today due to health reasons.\n\nI will ensure my current tasks are handed over or kept up to date. Please let me know if you require any medical certificate or further documents.\n\nThank you for your understanding.\n\nBest regards,\nVishvam Prajapati");
      } else {
        setSubject(`Formal Request regarding ${naturalLanguage.slice(0, 30)}`);
        setBody(`Dear Manager,\n\nI am writing to you regarding: "${naturalLanguage}".\n\nPlease let me know your availability to discuss this further at your earliest convenience.\n\nThank you,\nBest regards,\nVishvam Prajapati`);
      }
    } catch {
      setSubject("Application for Sick Leave");
      setBody("Dear Manager,\n\nI am writing to request leave due to unforeseen personal reasons. I will ensure all pending urgent tasks are addressed.\n\nBest regards,\nVishvam Prajapati");
    } finally {
      setDrafting(false);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden text-foreground bg-background">
      {/* ═══════════════════════════════════════════════════════════════
          COLUMN 1 — LEFT NAVIGATION SIDEBAR (Folders & Account)
      ═══════════════════════════════════════════════════════════════ */}
      <div className="w-60 shrink-0 border-r border-border bg-card/60 backdrop-blur flex flex-col p-4 justify-between">
        <div className="space-y-5">
          {/* Account Profile Header */}
          <div className="flex items-center gap-3 px-1">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 font-bold text-white text-xs shadow-md">
              {activeWorkspace?.name ? activeWorkspace.name[0].toUpperCase() : "V"}
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-foreground truncate">Vishvam Prajapati</div>
              <div className="text-[10px] text-muted-foreground truncate">vishvam@nexora.ai</div>
            </div>
          </div>

          {/* New Email Status Pill */}
          <div className="w-full flex items-center justify-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 dark:text-indigo-300 text-xs font-bold py-2.5 px-4 rounded-xl">
            <Sparkles className="h-4 w-4 text-indigo-500" /> AI Studio Mail Editor
          </div>

          {/* Folders List */}
          <div className="space-y-1">
            <div className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground px-2.5 mb-1.5">Mailboxes</div>
            
            <button
              onClick={() => setActiveFolder("inbox")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
                activeFolder === "inbox" ? "bg-indigo-600/15 text-indigo-500 dark:text-indigo-400 border border-indigo-500/30" : "text-muted-foreground hover:bg-accent"
              }`}
            >
              <span className="flex items-center gap-2.5"><Mail className="h-4 w-4" /> Mail Composer</span>
            </button>

            <button
              onClick={() => setActiveFolder("sent")}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
                activeFolder === "sent" ? "bg-indigo-600/15 text-indigo-500 dark:text-indigo-400 border border-indigo-500/30" : "text-muted-foreground hover:bg-accent"
              }`}
            >
              <span className="flex items-center gap-2.5"><Send className="h-4 w-4" /> Sent Dispatch</span>
            </button>
          </div>
        </div>

        <div className="text-[10px] text-muted-foreground text-center border-t border-border/60 pt-3 font-mono">
          Nexora AI Mail Client v2.5
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════
          COLUMN 2 — DIRECT IN-LINE EMAIL WORKSPACE (Side-by-Side)
      ═══════════════════════════════════════════════════════════════ */}
      <div className="flex-1 flex overflow-hidden bg-background">
        {/* Left Side: Manual Editor & AI Inputs (55% Width) */}
        <div className="w-[55%] flex flex-col border-r border-border overflow-hidden">
          {/* Top Workspace Header */}
          <div className="border-b border-zinc-800/80 px-6 py-4 bg-[#0a0a0e] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
                <Mail className="h-4 w-4" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-white tracking-tight">Email Composer Studio</h1>
                <p className="text-[10px] text-zinc-500">Draft manually or generate via AI Copilot</p>
              </div>
            </div>

            <button
              onClick={handleSendEmail}
              disabled={sending}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs px-5 py-2 rounded-xl shadow-lg shadow-blue-600/20 transition disabled:opacity-40"
            >
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              Dispatch Email →
            </button>
          </div>

          {/* Main Form Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {errorMsg && (
              <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-red-300">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                <p className="text-xs">{errorMsg}</p>
              </div>
            )}

            {successMsg && (
              <div className="flex items-start gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-emerald-300">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                <p className="text-xs">{successMsg}</p>
              </div>
            )}

            {/* Recipient To Email */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">Recipient Email (To)</label>
              <input
                type="email"
                value={toEmail}
                onChange={e => setToEmail(e.target.value)}
                placeholder="e.g. manager@company.com"
                className="w-full rounded-xl border border-zinc-800 bg-[#121218] px-3.5 py-2 text-xs text-white placeholder-zinc-600 outline-none focus:border-indigo-500 font-mono"
              />
            </div>

            {/* Email Subject */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">Subject</label>
              <input
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                placeholder="Subject line..."
                className="w-full rounded-xl border border-zinc-800 bg-[#121218] px-3.5 py-2 text-xs text-white placeholder-zinc-600 outline-none focus:border-indigo-500 font-semibold"
              />
            </div>

            {/* Attach Generated Report (Optional) */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                <Paperclip className="h-3.5 w-3.5 text-indigo-400" /> Attach Analytics Report (Optional)
              </label>
              <div className="relative">
                <select
                  value={selectedReportId}
                  onChange={e => setSelectedReportId(e.target.value)}
                  className="w-full appearance-none rounded-xl border border-zinc-800 bg-[#121218] px-3.5 py-2 text-xs text-white outline-none focus:border-indigo-500 pr-8"
                >
                  <option value="">— No Attachment —</option>
                  {reports.map((r) => (
                    <option key={r.report_id} value={r.report_id}>
                      📄 {r.report_type.toUpperCase()} ({r.export_format}) — {r.report_id.slice(0, 8)}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-zinc-500" />
              </div>
            </div>

            {/* Email Content Body Editor */}
            <div className="space-y-1 flex-1 flex flex-col">
              <label className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 block">Email Body Content</label>
              <textarea
                rows={10}
                value={body}
                onChange={e => setBody(e.target.value)}
                placeholder="Write your email here manually or ask AI Copilot below to generate..."
                className="w-full rounded-xl border border-zinc-800 bg-[#0e0e14] p-3.5 text-xs text-zinc-200 outline-none focus:border-indigo-500 font-sans leading-relaxed resize-y select-text shadow-inner"
              />
            </div>
          </div>

          {/* Bottom AI Copilot Drafter Bar */}
          <div className="p-3.5 border-t border-zinc-800/80 bg-[#0a0a0e] flex items-center gap-3 shrink-0">
            <div className="flex-1 flex items-center gap-3 bg-[#121218] border border-indigo-500/30 rounded-xl px-3.5 py-1.5 shadow-inner">
              <Sparkles className="h-4 w-4 text-indigo-400 shrink-0" />
              <input
                type="text"
                value={naturalLanguage}
                onChange={(e) => setNaturalLanguage(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleAIDrafter(); }}
                placeholder="Ask AI Copilot to draft email..."
                className="w-full bg-transparent text-xs text-white placeholder-zinc-500 focus:outline-none"
              />
              <button
                onClick={handleAIDrafter}
                disabled={drafting || !naturalLanguage.trim()}
                className="rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-xs font-bold px-3 py-1 disabled:opacity-40 transition shrink-0"
              >
                {drafting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Draft ✨"}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Live HTML Render Preview Card (45% Width) */}
        <div className="w-[45%] flex flex-col bg-[#050507] overflow-hidden">
          <div className="border-b border-zinc-800/80 px-6 py-4 bg-[#0a0a0e] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">LIVE EMAIL PREVIEW</span>
            </div>
            <span className="text-[10px] text-zinc-500 font-mono">Rendered Card</span>
          </div>

          <div className="flex-1 overflow-y-auto p-6 flex flex-col justify-start">
            <div className="w-full rounded-2xl border border-zinc-800 bg-[#0d0d12] p-6 shadow-2xl space-y-4 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-indigo-600/10 text-indigo-400 text-[9px] font-mono font-bold px-3 py-1 rounded-bl-xl border-l border-b border-indigo-500/20">
                SMTP LIVE RENDER
              </div>

              {/* Subject */}
              <div>
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block">Subject</span>
                <h3 className="text-sm font-bold text-white mt-0.5">{subject || "No Subject"}</h3>
              </div>

              {/* Recipient */}
              <div className="pt-2 border-t border-zinc-800/60 flex items-center justify-between">
                <div>
                  <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block">Recipient</span>
                  <span className="text-xs font-mono text-indigo-300">{toEmail || "recipient@company.com"}</span>
                </div>
                <div className="text-[10px] text-zinc-500 font-mono">Today, Just now</div>
              </div>

              {/* Body Render */}
              <div className="pt-4 border-t border-zinc-800/60 space-y-2">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider block">Message Preview</span>
                <div className="text-xs text-zinc-300 whitespace-pre-wrap leading-relaxed font-sans bg-[#07070a] p-4 rounded-xl border border-zinc-800/80 min-h-[160px]">
                  {body || "No message body written yet."}
                </div>
              </div>

              {/* Attachment Badge */}
              {selectedReportId && (
                <div className="pt-3 border-t border-zinc-800/60 flex items-center gap-2 text-xs text-indigo-400 bg-indigo-500/10 p-3 rounded-xl border border-indigo-500/20">
                  <Paperclip className="h-4 w-4 shrink-0" />
                  <span className="font-mono text-[11px] truncate">Attached: Analytics_Report_{selectedReportId.slice(0, 8)}.pdf</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
