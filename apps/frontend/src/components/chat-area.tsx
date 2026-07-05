"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import ChatMessage from "./chat-message";
import { 
  Send, Paperclip, ChevronLeft, Cpu, ShieldAlert,
  ArrowDown, RefreshCw, AlertCircle
} from "lucide-react";

export default function ChatArea() {
  const {
    activeWorkspace,
    activeConversation,
    messages,
    isStreaming,
    sidebarOpen,
    toggleSidebar,
    setActiveConversation,
    addMessage,
    updateLastMessageContent,
    setMessages
  } = useChatStore();

  const [inputVal, setInputVal] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Auto resize textarea height
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
    let isNewConvo = false;

    // 1. Create a new conversation if none is active
    if (!activeConversation) {
      isNewConvo = true;
      try {
        const title = prompt.length > 30 ? `${prompt.slice(0, 30)}...` : prompt;
        const newConvo = await apiService.createConversation(title, activeWorkspace.id);
        setActiveConversation(newConvo);
        convoId = newConvo.id;
      } catch (err: any) {
        console.error("Failed to create conversation:", err);
        setErrorMsg("Failed to start new chat session.");
        return;
      }
    } else {
      convoId = activeConversation.id;
    }

    // 2. Append user message to local state
    const userMessage = {
      id: Date.now(), // temporary ID
      conversation_id: convoId,
      role: "user" as const,
      content: prompt,
      created_at: new Date().toISOString()
    };
    addMessage(userMessage);

    // 3. Append empty assistant message for streaming content
    const assistantMessage = {
      id: Date.now() + 1, // temporary ID
      conversation_id: convoId,
      role: "assistant" as const,
      content: "",
      created_at: new Date().toISOString()
    };
    addMessage(assistantMessage);

    // 4. Stream response
    let accumulatedText = "";
    try {
      await apiService.streamChat(
        convoId,
        prompt,
        activeWorkspace.id,
        (token) => {
          accumulatedText += token;
          updateLastMessageContent(accumulatedText);
        },
        (error) => {
          setErrorMsg(`Error during generation: ${error}`);
        }
      );
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Failed to generate response. Please check backend connection.");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="relative flex h-full flex-1 flex-col bg-background">
      
      {/* Top Header Navigation bar */}
      <header className="flex h-14 items-center justify-between border-b border-border bg-card/50 backdrop-blur px-6">
        <div className="flex items-center gap-3">
          {!sidebarOpen && (
            <button
              onClick={toggleSidebar}
              className="rounded-lg border border-border bg-card p-1.5 hover:bg-zinc-50 dark:hover:bg-zinc-900"
            >
              <ChevronLeft className="h-4 w-4 rotate-180" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-500" />
            <h1 className="text-sm font-semibold tracking-tight">
              {activeConversation ? activeConversation.title : "New Chat"}
            </h1>
          </div>
        </div>
        
        {activeConversation && (
          <div className="text-[10px] bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-semibold px-2 py-0.5 rounded border border-indigo-500/20 uppercase tracking-wide">
            Model: Local Qwen LoRA
          </div>
        )}
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
        {!activeConversation && messages.length === 0 ? (
          /* Welcome Hero Panel */
          <div className="flex h-full flex-col items-center justify-center text-center max-w-[600px] mx-auto space-y-6 mt-[10%]">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-500">
              <Cpu className="h-8 w-8" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Ask Nexora AI anything
              </h2>
              <p className="text-sm text-zinc-400 leading-relaxed">
                Nexora AI is running a fine-tuned causal Qwen model (`vishvam26/nexora-qwen3.5-4b-lora-v1`) locally on your machine. Start writing your prompt below.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-3 w-full mt-4">
              {[
                "Write a REST API with FastAPI in Python",
                "Explain PEFT and QLoRA fine-tuning concept",
                "Draft a technical PRD for model metrics",
                "Create a database schema for user profiles"
              ].map(prompt => (
                <button
                  key={prompt}
                  onClick={() => {
                    setInputVal(prompt);
                    textareaRef.current?.focus();
                  }}
                  className="rounded-xl border border-border bg-card p-3.5 text-left text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:border-indigo-500 hover:text-foreground transition duration-150"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Render chat history bubbles */
          <div className="max-w-[760px] mx-auto space-y-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Error alerts */}
            {errorMsg && (
              <div className="flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
                <AlertCircle className="h-5 w-5 shrink-0 animate-pulse" />
                <div className="flex-1">
                  <span>{errorMsg}</span>
                </div>
                <button 
                  onClick={() => { setErrorMsg(null); handleSend(); }} 
                  className="flex items-center gap-1 text-xs font-semibold underline hover:text-red-300"
                >
                  <RefreshCw className="h-3 w-3" />
                  <span>Retry</span>
                </button>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input panel at bottom */}
      <div className="border-t border-border bg-card/30 backdrop-blur p-4">
        <div className="max-w-[760px] mx-auto relative flex items-end gap-2 rounded-xl border border-border bg-card p-2 shadow-sm transition-all focus-within:border-indigo-500">
          <button className="rounded-lg p-2 text-zinc-400 hover:bg-sidebar-active hover:text-foreground transition" title="Add attachment">
            <Paperclip className="h-4 w-4" />
          </button>
          
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message or paste code snippet..."
            className="flex-1 resize-none bg-transparent py-2.5 px-1.5 text-sm text-foreground outline-none placeholder-zinc-500 min-h-[40px] max-h-[200px]"
            disabled={isStreaming}
          />
          
          <button
            onClick={handleSend}
            disabled={!inputVal.trim() || isStreaming}
            className={`rounded-lg p-2.5 transition ${
              inputVal.trim() && !isStreaming
                ? "bg-primary text-white hover:bg-primary-hover shadow-md"
                : "text-zinc-400 bg-sidebar-active cursor-not-allowed"
            }`}
          >
            {isStreaming ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-400 border-t-transparent"></div>
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
        <div className="text-[10px] text-center text-zinc-500 mt-2.5">
          Nexora AI can make mistakes. Verify critical code and logic.
        </div>
      </div>

    </main>
  );
}
