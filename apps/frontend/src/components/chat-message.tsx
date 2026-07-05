"use client";

import { useState } from "react";
import { Message } from "../types/chat";
import { Copy, Check, ThumbsUp, ThumbsDown, Cpu, User } from "lucide-react";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState<boolean | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Safe lightweight markdown & code block parsing
  const renderParsedContent = (text: string) => {
    if (!text) return <p className="animate-pulse text-zinc-500 font-medium">Thinking...</p>;

    // Split by code block markers: ```
    const segments = text.split("```");
    
    return segments.map((seg, idx) => {
      const isCode = idx % 2 === 1;

      if (isCode) {
        // Extract language and code content
        const newlineIdx = seg.indexOf("\n");
        let lang = "code";
        let code = seg;
        
        if (newlineIdx !== -1) {
          lang = seg.slice(0, newlineIdx).trim() || "code";
          code = seg.slice(newlineIdx + 1);
        }

        return (
          <div key={idx} className="my-4 overflow-hidden rounded-lg border border-border bg-zinc-950 text-zinc-200">
            {/* Code Block Header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-800 bg-zinc-900/50 text-[10px] uppercase font-bold tracking-wider text-zinc-500">
              <span>{lang}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(code);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="flex items-center gap-1 hover:text-zinc-300 font-semibold"
              >
                {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
            {/* Code Content */}
            <pre className="overflow-x-auto p-4 text-xs font-mono leading-relaxed">
              <code>{code.trim()}</code>
            </pre>
          </div>
        );
      }

      // Parse non-code blocks (paragraphs, bullet lists, tables)
      const lines = seg.split("\n");
      const elements: React.ReactNode[] = [];
      let listItems: string[] = [];
      
      lines.forEach((line, lineIdx) => {
        const trimmed = line.trim();

        // 1. Parse bullet points
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          listItems.push(trimmed.slice(2));
          return;
        }

        // If list items exist but current line is not a list item, flush the list
        if (listItems.length > 0) {
          elements.push(
            <ul key={`list-${lineIdx}`} className="list-disc pl-5 my-3 space-y-1 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
              {listItems.map((item, itemIdx) => (
                <li key={itemIdx}>{item}</li>
              ))}
            </ul>
          );
          listItems = [];
        }

        // 2. Parse headers
        if (trimmed.startsWith("### ")) {
          elements.push(
            <h4 key={lineIdx} className="text-sm font-bold tracking-tight text-foreground mt-4 mb-2">
              {trimmed.slice(4)}
            </h4>
          );
          return;
        }
        if (trimmed.startsWith("## ")) {
          elements.push(
            <h3 key={lineIdx} className="text-base font-bold tracking-tight text-foreground mt-5 mb-2.5">
              {trimmed.slice(3)}
            </h3>
          );
          return;
        }
        if (trimmed.startsWith("# ")) {
          elements.push(
            <h2 key={lineIdx} className="text-lg font-bold tracking-tight text-foreground mt-6 mb-3">
              {trimmed.slice(2)}
            </h2>
          );
          return;
        }

        // 3. Parse tables
        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
          // Simplistic table parse (split by '|')
          const cells = trimmed.split("|").slice(1, -1).map(c => c.trim());
          const isSeparator = cells.every(c => c.startsWith("-") || c.startsWith(":"));
          
          if (!isSeparator) {
            elements.push(
              <div key={lineIdx} className="overflow-x-auto my-3 rounded-lg border border-border bg-card">
                <table className="min-w-full divide-y divide-border text-xs">
                  <tbody className="divide-y divide-border bg-card">
                    <tr className="hover:bg-zinc-50/50 dark:hover:bg-zinc-900/50">
                      {cells.map((cell, cellIdx) => (
                        <td key={cellIdx} className="px-4 py-2.5 font-medium whitespace-nowrap text-zinc-700 dark:text-zinc-300">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            );
          }
          return;
        }

        // 4. Default paragraph rendering
        if (trimmed) {
          elements.push(
            <p key={lineIdx} className="text-sm leading-relaxed text-zinc-700 dark:text-zinc-300 my-2">
              {trimmed}
            </p>
          );
        }
      });

      // Final flush for list items
      if (listItems.length > 0) {
        elements.push(
          <ul key={`list-end`} className="list-disc pl-5 my-3 space-y-1 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
            {listItems.map((item, itemIdx) => (
              <li key={itemIdx}>{item}</li>
            ))}
          </ul>
        );
      }

      return <div key={idx}>{elements}</div>;
    });
  };

  return (
    <div className={`flex w-full gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
      
      {/* 1. Logo Icons */}
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-500">
          <Cpu className="h-4.5 w-4.5" />
        </div>
      )}

      {/* 2. Message Bubble Shell */}
      <div className={`flex flex-col max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Username/Role with timestamp */}
        <div className="flex items-center gap-2 mb-1.5 text-[10px] text-zinc-400">
          <span className="font-semibold text-zinc-500 dark:text-zinc-400">
            {isUser ? "You" : "Nexora AI"}
          </span>
          <span>&bull;</span>
          <span>{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>

        {/* Bubble body content */}
        <div className={`rounded-2xl px-4 py-2.5 shadow-sm transition-colors duration-150 ${
          isUser 
            ? "bg-primary text-white" 
            : "bg-card border border-border text-foreground"
        }`}>
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="space-y-1">
              {renderParsedContent(message.content)}
            </div>
          )}
        </div>

        {/* Action icons bar for AI answers */}
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
                onClick={() => setLiked(true)} 
                className={`p-1 hover:bg-sidebar-active rounded transition ${liked === true ? "text-green-500" : ""}`}
                title="Like response"
              >
                <ThumbsUp className="h-3 w-3" />
              </button>
              <button 
                onClick={() => setLiked(false)} 
                className={`p-1 hover:bg-sidebar-active rounded transition ${liked === false ? "text-red-500" : ""}`}
                title="Dislike response"
              >
                <ThumbsDown className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}
      </div>

      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          <User className="h-4.5 w-4.5" />
        </div>
      )}

    </div>
  );
}
