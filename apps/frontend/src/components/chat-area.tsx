"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import ChatMessage from "./chat-message";
import { 
  Send, Paperclip, ChevronLeft, Cpu, 
  RefreshCw, AlertCircle, BookOpen, X,
  Zap, Database, Code2, FileText, Brain, Sparkles
} from "lucide-react";

const PROMPT_CARDS = [
  { icon: Code2, label: "REST API with FastAPI", desc: "Generate a fully documented endpoint", prompt: "Write a production-ready REST API with FastAPI including Pydantic models, error handling and JWT auth.", color: "indigo" },
  { icon: Brain, label: "PEFT & QLoRA Fine-tuning", desc: "Explain local adaptation models", prompt: "Explain PEFT and QLoRA fine-tuning for LLMs in detail with code examples.", color: "violet" },
  { icon: FileText, label: "Technical PRD Template", desc: "Draft layout for model evaluation", prompt: "Draft a technical PRD for tracking model metrics, evaluation pipelines and validation queues.", color: "cyan" },
  { icon: Database, label: "Database Schema Design", desc: "Create relational tables", prompt: "Design a normalized relational database schema for a multi-tenant SaaS platform with roles.", color: "emerald" },
];

const COLOR_MAP: Record<string, { border: string; bg: string; icon: string; glow: string }> = {
  indigo: { border: "border-indigo-500/20", bg: "bg-indigo-500/5", icon: "text-indigo-400", glow: "hover:shadow-[0_0_20px_rgba(99,102,241,0.12)]" },
  violet: { border: "border-violet-500/20", bg: "bg-violet-500/5", icon: "text-violet-400", glow: "hover:shadow-[0_0_20px_rgba(139,92,246,0.12)]" },
  cyan:   { border: "border-cyan-500/20",   bg: "bg-cyan-500/5",   icon: "text-cyan-400",   glow: "hover:shadow-[0_0_20px_rgba(6,182,212,0.12)]"   },
  emerald:{ border: "border-emerald-500/20",bg: "bg-emerald-500/5",icon: "text-emerald-400",glow: "hover:shadow-[0_0_20px_rgba(16,185,129,0.12)]" },
};

export default function ChatArea() {
  const {
    activeWorkspace, activeConversation, messages,
    isStreaming, sidebarOpen, toggleSidebar,
    setActiveConversation, addMessage, updateLastMessageContent,
    updateLastMessageSources, knowledgeBases,
    selectedChatKb, setSelectedChatKb, groundingEnabled, setGroundingEnabled
  } = useChatStore();

  const [inputVal, setInputVal] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [kbSelectorOpen, setKbSelectorOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [displayText, setDisplayText] = useState("");
  const fullText = "How can Nexora AI help you?";

  useEffect(() => {
    let index = 0;
    setDisplayText("");
    const interval = setInterval(() => {
      setDisplayText(fullText.slice(0, index + 1));
      index++;
      if (index >= fullText.length) {
        clearInterval(interval);
      }
    }, 50);
    return () => clearInterval(interval);
  }, [activeConversation]);

  useEffect(() => {
    if (activeWorkspace) apiService.fetchKnowledgeBases(activeWorkspace.id);
  }, [activeWorkspace]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputVal]);

  const handleSend = async () => {
    if (!inputVal.trim() || isStreaming || !activeWorkspace) return;
    const prompt = inputVal.trim();
    setInputVal("");
    setErrorMsg(null);

    let convoId: number;
    if (!activeConversation) {
      try {
        const title = prompt.length > 30 ? `${prompt.slice(0, 30)}...` : prompt;
        const newConvo = await apiService.createConversation(title, activeWorkspace.id);
        setActiveConversation(newConvo);
        convoId = newConvo.id;
      } catch {
        setErrorMsg("Failed to start new chat session.");
        return;
      }
    } else {
      convoId = activeConversation.id;
    }

    const userMsg = { id: Date.now(), conversation_id: convoId, role: "user" as const, content: prompt, created_at: new Date().toISOString() };
    addMessage(userMsg);
    const asstMsg = { id: Date.now() + 1, conversation_id: convoId, role: "assistant" as const, content: "", created_at: new Date().toISOString() };
    addMessage(asstMsg);

    let accumulated = "";
    try {
      await apiService.streamChat(
        convoId, prompt, activeWorkspace.id,
        groundingEnabled ? (selectedChatKb?.id || null) : null,
        groundingEnabled,
        (token) => { accumulated += token; updateLastMessageContent(accumulated); },
        (sources) => { updateLastMessageSources(sources); },
        (error) => { setErrorMsg(`Error during generation: ${error}`); }
      );
    } catch {
      setErrorMsg("Failed to generate response. Check backend connection.");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const isEmptyState = !activeConversation && messages.length === 0;

  return (
    <main className="relative flex h-full flex-col" style={{ background: "transparent" }}>

      {/* ── Top Header ── */}
      <header className="flex h-14 shrink-0 items-center justify-between px-6 z-10"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(9,9,11,0.5)", backdropFilter: "blur(16px)" }}>
        <div className="flex items-center gap-3">
          {!sidebarOpen && (
            <button onClick={toggleSidebar}
              className="rounded-lg p-1.5 text-zinc-500 hover:text-white transition-all hover:bg-white/5"
              style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
              <ChevronLeft className="h-4 w-4 rotate-180" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md border"
              style={{ background: "linear-gradient(135deg,rgba(34,211,238,0.15),rgba(99,102,241,0.08))", borderColor: "rgba(34,211,238,0.25)" }}>
              {/* Original Skyblue Bird Logo ^ */}
              <svg viewBox="0 0 100 100" fill="none" className="h-4.5 w-4.5 filter drop-shadow-[0_0_4px_rgba(34,211,238,0.4)]">
                <path d="M 50 10 L 60 40 L 55 70 L 45 70 L 40 40 Z" fill="url(#header-bird-grad)" />
                <path d="M 50 40 Q 20 20 10 40 Q 30 45 50 50 Z" fill="url(#header-bird-grad)" />
                <path d="M 50 40 Q 80 20 90 40 Q 70 45 50 50 Z" fill="url(#header-bird-grad)" />
                <defs>
                  <linearGradient id="header-bird-grad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#22d3ee" />
                    <stop offset="100%" stopColor="#6366f1" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1 className="text-sm font-semibold text-zinc-200 tracking-tight">
              {activeWorkspace?.name || "Workspace"}
              <span className="mx-1.5 text-zinc-700">·</span>
              <span className="text-zinc-400 font-normal">{activeConversation ? activeConversation.title : "New Chat"}</span>
            </h1>
          </div>
        </div>

        {activeConversation && (
          <div className="flex items-center gap-1.5 text-[10px] font-semibold tracking-widest uppercase"
            style={{ padding: "3px 10px", borderRadius: 8, background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.18)", color: "#a5b4fc" }}>
            <Zap className="h-2.5 w-2.5" />
            Local Qwen LoRA
          </div>
        )}
      </header>

      {/* ── Messages / Empty State ── */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {isEmptyState ? (
          /* ─ Welcome Screen ─ */
          <div className="flex h-full flex-col items-center justify-start text-center max-w-[600px] mx-auto space-y-8 select-none pt-14 md:pt-16 pb-8">

            {/* Animated badge */}
            <div className="relative mt-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl border"
                style={{
                  background: "linear-gradient(135deg,rgba(34,211,238,0.15),rgba(99,102,241,0.08))",
                  borderColor: "rgba(34,211,238,0.25)",
                  boxShadow: "0 0 40px rgba(34,211,238,0.15), 0 0 80px rgba(99,102,241,0.05)",
                }}>
                {/* Original Skyblue Bird Logo ^ */}
                <svg viewBox="0 0 100 100" fill="none" className="h-12 w-12 animate-pulse filter drop-shadow-[0_0_12px_rgba(34,211,238,0.4)]">
                  <path d="M 50 10 L 60 40 L 55 70 L 45 70 L 40 40 Z" fill="url(#chat-bird-grad)" />
                  <path d="M 50 40 Q 20 20 10 40 Q 30 45 50 50 Z" fill="url(#chat-bird-grad)" />
                  <path d="M 50 40 Q 80 20 90 40 Q 70 45 50 50 Z" fill="url(#chat-bird-grad)" />
                  <defs>
                    <linearGradient id="chat-bird-grad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#22d3ee" />
                      <stop offset="100%" stopColor="#6366f1" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              {/* Outer rings */}
              <div className="absolute inset-[-12px] rounded-3xl animate-ping opacity-10"
                style={{ border: "1px solid rgba(34,211,238,0.4)" }} />
              <div className="absolute inset-[-24px] rounded-[2rem] animate-ping opacity-5"
                style={{ border: "1px solid rgba(99,102,241,0.3)", animationDelay: "0.5s" }} />
            </div>

            {/* Headline */}
            <div className="space-y-3">
              {(() => {
                const len = displayText.length;
                const isDone = len === fullText.length;
                let content;
                if (len <= 8) {
                  content = <span>{displayText}</span>;
                } else if (len <= 17) {
                  content = (
                    <>
                      How can{" "}
                      <span style={{ background: "linear-gradient(90deg,#818cf8,#c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                        {displayText.slice(8)}
                      </span>
                    </>
                  );
                } else {
                  content = (
                    <>
                      How can{" "}
                      <span style={{ background: "linear-gradient(90deg,#818cf8,#c084fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                        Nexora AI
                      </span>
                      {displayText.slice(17)}
                    </>
                  );
                }
                return (
                  <h2 className="text-3xl font-bold tracking-tight text-white" style={{ fontFamily: "'Playfair Display', serif" }}>
                    {content}
                    {!isDone && <span className="animate-pulse text-indigo-400 ml-1">|</span>}
                  </h2>
                );
              })()}
              <p className="text-sm text-zinc-500 max-w-md mx-auto leading-relaxed">
                Running a fine-tuned Qwen model locally. Ground answers in custom files, train ML classifiers, or trigger background agents.
              </p>
            </div>

            {/* Capability badges */}
            <div className="flex flex-wrap justify-center gap-2">
              {["RAG Grounding", "QLoRA Fine-tuned", "Streaming", "Local Inference"].map(tag => (
                <span key={tag} className="text-[10px] font-semibold tracking-wider uppercase px-2.5 py-1 rounded-full"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", color: "#71717a" }}>
                  {tag}
                </span>
              ))}
            </div>

            {/* Prompt cards */}
            <div className="grid grid-cols-2 gap-3 w-full">
              {PROMPT_CARDS.map(card => {
                const c = COLOR_MAP[card.color];
                const Icon = card.icon;
                return (
                  <button key={card.label}
                    onClick={() => { setInputVal(card.prompt); textareaRef.current?.focus(); }}
                    className={`group rounded-xl p-4 text-left transition-all duration-300 ${c.border} ${c.bg} ${c.glow} hover:translate-y-[-2px]`}
                    style={{ border: `1px solid`, background: "rgba(255,255,255,0.02)", backdropFilter: "blur(8px)" }}>
                    <div className="flex items-start gap-3">
                      <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${c.bg} ${c.border}`}
                        style={{ border: "1px solid" }}>
                        <Icon className={`h-3.5 w-3.5 ${c.icon}`} />
                      </div>
                      <div>
                        <div className={`text-xs font-semibold text-zinc-300 group-hover:${c.icon} transition-colors`}>{card.label}</div>
                        <div className="text-[10px] text-zinc-600 mt-0.5">{card.desc}</div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Sparkle hint */}
            <div className="flex items-center gap-2 text-[11px] text-zinc-600">
              <Sparkles className="h-3 w-3 text-indigo-500/50" />
              <span>Click a card or type below to begin</span>
            </div>
          </div>

        ) : (
          /* ─ Chat Messages ─ */
          <div className="max-w-[760px] mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <ChatMessage key={msg.id} message={msg} previousMessage={idx > 0 ? messages[idx - 1] : undefined} />
            ))}
            {errorMsg && (
              <div className="flex items-center gap-3 rounded-xl p-4 text-sm text-red-400"
                style={{ background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.15)" }}>
                <AlertCircle className="h-4 w-4 shrink-0 animate-pulse" />
                <span className="flex-1">{errorMsg}</span>
                <button onClick={() => { setErrorMsg(null); handleSend(); }}
                  className="flex items-center gap-1 text-xs font-semibold underline hover:text-red-300">
                  <RefreshCw className="h-3 w-3" /> Retry
                </button>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Bottom Input Panel ── */}
      <div className="shrink-0 px-6 pb-4 pt-3 z-10"
        style={{ borderTop: "1px solid rgba(255,255,255,0.05)", background: "rgba(9,9,11,0.6)", backdropFilter: "blur(20px)" }}>
        <div className="max-w-[760px] mx-auto space-y-2.5">

          {/* Grounding / KB bar */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {/* Grounding toggle */}
              <button onClick={() => setGroundingEnabled(!groundingEnabled)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                style={{
                  border: `1px solid ${groundingEnabled ? "rgba(16,185,129,0.25)" : "rgba(255,255,255,0.06)"}`,
                  background: groundingEnabled ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.02)",
                  color: groundingEnabled ? "#34d399" : "#52525b",
                }}>
                <div className={`h-1.5 w-1.5 rounded-full ${groundingEnabled ? "bg-emerald-400 animate-pulse" : "bg-zinc-600"}`} />
                Grounded Mode: {groundingEnabled ? "ON" : "OFF"}
              </button>

              {/* KB selector */}
              {groundingEnabled && (
                <div className="relative">
                  {selectedChatKb ? (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                      style={{ border: "1px solid rgba(99,102,241,0.25)", background: "rgba(99,102,241,0.1)", color: "var(--indigo)" }}>
                      <span>{selectedChatKb.icon}</span>
                      <span className="truncate max-w-[130px]">{selectedChatKb.title}</span>
                      <button onClick={() => setSelectedChatKb(null)} className="ml-1 opacity-60 hover:opacity-100 transition">
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => setKbSelectorOpen(!kbSelectorOpen)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition border"
                      style={{ borderColor: "var(--border)", background: "var(--input-bg)", color: "var(--text-secondary)" }}>
                      <BookOpen className="h-3.5 w-3.5" />
                      Select Knowledge Source
                    </button>
                  )}
                  {kbSelectorOpen && (
                    <div className="absolute bottom-full left-0 mb-2 w-60 rounded-xl p-2 shadow-2xl z-50 space-y-0.5 border"
                      style={{ background: "var(--input-bg)", borderColor: "var(--border)", backdropFilter: "blur(20px)" }}>
                      <p className="text-[9px] font-bold text-zinc-500 px-2 py-1.5 uppercase tracking-wider">
                        Bases ({knowledgeBases.length})
                      </p>
                      {knowledgeBases.length === 0 ? (
                        <p className="text-[10px] text-zinc-500 px-2 py-2">No bases found. Add in Knowledge tab.</p>
                      ) : knowledgeBases.map(kb => (
                        <button key={kb.id} onClick={() => { setSelectedChatKb(kb); setKbSelectorOpen(false); }}
                          className="w-full flex items-center gap-2 p-2 rounded-lg text-left text-zinc-400 hover:text-indigo-400 hover:bg-indigo-500/10 transition"
                          style={{ background: "transparent" }}>
                          <span className="text-sm">{kb.icon}</span>
                          <span className="text-xs font-semibold truncate">{kb.title}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            {groundingEnabled && !selectedChatKb && (
              <span className="text-[10px] text-zinc-600 italic">Select a source above to restrict AI context.</span>
            )}
            {groundingEnabled && selectedChatKb && (
              <span className="text-[10px] font-bold tracking-widest uppercase text-emerald-500/70">● Fully Grounded</span>
            )}
          </div>

          {/* Textarea input */}
          <div className="relative flex items-end gap-2 rounded-2xl p-2.5 transition-all duration-200 border"
            style={{
              background: "var(--input-bg)",
              borderColor: "var(--input-border)",
              backdropFilter: "blur(12px)",
            }}
            onFocus={() => {}}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "var(--primary)"; (e.currentTarget as HTMLDivElement).style.boxShadow = "var(--glow-indigo)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "var(--input-border)"; (e.currentTarget as HTMLDivElement).style.boxShadow = "none"; }}>

            <button onClick={() => setKbSelectorOpen(!kbSelectorOpen)}
              className="rounded-xl p-2 text-zinc-550 hover:text-indigo-400 transition-colors"
              title="Select Knowledge Base">
              <Paperclip className="h-4 w-4" />
            </button>

            <textarea ref={textareaRef} rows={1} value={inputVal}
              onChange={e => setInputVal(e.target.value)} onKeyDown={handleKeyDown}
              placeholder={groundingEnabled && selectedChatKb ? `Ask about "${selectedChatKb.title}"...` : "Ask a question..."}
              className="flex-1 resize-none bg-transparent py-2 px-1.5 text-sm outline-none min-h-[38px] max-h-[200px]"
              style={{ caretColor: "var(--primary)", color: "var(--text-primary)" }}
              disabled={isStreaming}
            />

            <button onClick={handleSend} disabled={!inputVal.trim() || isStreaming}
              className="rounded-xl p-2.5 transition-all duration-200"
              style={{
                background: inputVal.trim() && !isStreaming ? "linear-gradient(135deg,var(--primary),var(--violet))" : "var(--border)",
                boxShadow: inputVal.trim() && !isStreaming ? "var(--glow-indigo-strong)" : "none",
                color: inputVal.trim() && !isStreaming ? "#fff" : "var(--text-muted)",
                cursor: inputVal.trim() && !isStreaming ? "pointer" : "not-allowed",
              }}>
              {isStreaming ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>

          <p className="text-[10px] text-center text-zinc-700">
            Nexora AI can make mistakes. Verify critical code and logic.
          </p>
        </div>
      </div>
    </main>
  );
}
