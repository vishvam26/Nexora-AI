"use client";

import { useState } from "react";
import { Message } from "../types/chat";
import { Copy, Check, ThumbsUp, ThumbsDown, Cpu, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChatStore } from "../stores/chat-store";

interface ChatMessageProps {
  message: Message;
  previousMessage?: Message;
}

export default function ChatMessage({ message, previousMessage }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState<boolean | null>(null);
  const token = useChatStore((state) => state.token);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (isUp: boolean) => {
    let comment: string | null = null;
    if (!isUp) {
      const response = window.prompt("Why did you dislike this response? (Optional comment):");
      if (response === null) return; // User cancelled
      comment = response;
    } else {
      comment = "Thumbs up";
    }

    setLiked(isUp);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const payload = {
        message_id: message.id,
        thumbs_up: isUp,
        thumbs_down: !isUp,
        feedback_text: comment,
        response_time_ms: 1500,
        original_query: previousMessage?.content || "What is Nexora AI platform?",
        context_chunks: message.sources?.map(src => 
          `File: ${src.filename}, Page: ${src.page}, Section: ${src.section}, Match: ${src.confidence}%`
        ) || [],
        prompt_text: null
      };

      const res = await fetch(`${API_BASE}/eval/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "69420",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("Failed to submit feedback to server.");
      }
      
      alert(isUp ? "Feedback submitted! Thank you." : "Dislike feedback submitted! The query has been sent to the Human Review Queue.");
    } catch (err) {
      console.error("Feedback submit failed:", err);
    }
  };

  return (
    <div className={`flex w-full gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
      
      {/* AI Avatar */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-500">
          <Cpu className="h-4 w-4" />
        </div>
      )}

      {/* Message Bubble */}
      <div className={`flex flex-col max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Role + Timestamp */}
        <div className="flex items-center gap-2 mb-1.5 text-[10px] text-zinc-400">
          <span className="font-semibold text-zinc-500 dark:text-zinc-400">
            {isUser ? "You" : "Nexora AI"}
          </span>
          <span>&bull;</span>
          <span>{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
        </div>

        {/* Bubble Body */}
        <div className={`rounded-2xl px-4 py-3 shadow-sm transition-colors duration-150 ${
          isUser
            ? "bg-primary text-white"
            : "bg-card border border-border text-foreground"
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              {!message.content ? (
                <p className="animate-pulse text-zinc-500 font-medium text-sm">Thinking...</p>
              ) : (
                <div className="prose prose-sm prose-zinc dark:prose-invert max-w-none
                  prose-headings:font-bold prose-headings:text-foreground prose-headings:mt-4 prose-headings:mb-2
                  prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-h4:text-sm
                  prose-p:text-sm prose-p:leading-relaxed prose-p:my-1.5 prose-p:text-zinc-300
                  prose-li:text-sm prose-li:text-zinc-300 prose-li:my-0.5
                  prose-ul:pl-5 prose-ul:my-2 prose-ol:pl-5 prose-ol:my-2
                  prose-strong:text-zinc-100 prose-strong:font-semibold
                  prose-em:text-zinc-300
                  prose-code:text-indigo-300 prose-code:bg-zinc-900 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono
                  prose-pre:bg-zinc-950 prose-pre:border prose-pre:border-zinc-800 prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto
                  prose-blockquote:border-l-indigo-500 prose-blockquote:text-zinc-400 prose-blockquote:italic
                  prose-table:text-sm prose-th:text-zinc-300 prose-td:text-zinc-400
                  prose-hr:border-zinc-800
                ">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Custom code block with copy button
                      pre({ children, ...props }) {
                        return (
                          <div className="relative my-4 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
                            <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/60 text-[10px] uppercase font-bold tracking-wider text-zinc-500">
                              <span>code</span>
                              <CopyCodeButton content={String(children)} />
                            </div>
                            <pre {...props} className="overflow-x-auto p-4 text-xs font-mono leading-relaxed text-zinc-200">
                              {children}
                            </pre>
                          </div>
                        );
                      },
                      // Inline code
                      code({ inline, children, ...props }: any) {
                        if (inline) {
                          return (
                            <code {...props} className="text-indigo-300 bg-zinc-900 px-1.5 py-0.5 rounded text-xs font-mono">
                              {children}
                            </code>
                          );
                        }
                        return <code {...props}>{children}</code>;
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}

              {/* RAG Citations */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 pt-3.5 border-t border-zinc-800 space-y-2">
                  <p className="text-[10px] uppercase font-bold tracking-wider text-zinc-500 flex items-center gap-1.5">
                    <span>📚 Retrieved References</span>
                    <span className="text-zinc-700">•</span>
                    <span className="text-emerald-500/85">Grounded Context</span>
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {message.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-zinc-800 bg-zinc-950/40 text-[11px] text-zinc-400 hover:text-zinc-200 transition"
                        title={`${src.filename} | Section: ${src.section || "General"}`}
                      >
                        <span className="font-bold text-indigo-400">[{sIdx + 1}]</span>
                        <span className="truncate max-w-[120px] font-medium">{src.filename}</span>
                        <span className="text-zinc-700">•</span>
                        <span>Page {src.page}</span>
                        <span className="text-zinc-700">•</span>
                        <span className="text-emerald-500 font-mono font-semibold">
                          {src.confidence}% Match
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Action Bar */}
        {!isUser && message.content && (
          <div className="flex items-center gap-3 mt-1.5 text-zinc-400 px-1">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-zinc-300 transition text-[10px]"
              title="Copy answer"
            >
              {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
              <span>{copied ? "Copied!" : "Copy"}</span>
            </button>
            <div className="flex items-center gap-1 border-l border-border pl-3">
              <button
                onClick={() => handleFeedback(true)}
                className={`p-1 hover:bg-zinc-800 rounded transition ${liked === true ? "text-green-500" : ""}`}
                title="Like response"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>
              <button
                onClick={() => handleFeedback(false)}
                className={`p-1 hover:bg-zinc-800 rounded transition ${liked === false ? "text-red-500" : ""}`}
                title="Dislike response"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}

// Helper component for copy button inside code blocks
function CopyCodeButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="flex items-center gap-1 hover:text-zinc-300 font-semibold"
    >
      {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
      <span>{copied ? "Copied" : "Copy"}</span>
    </button>
  );
}
