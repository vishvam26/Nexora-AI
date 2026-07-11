"use client";

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import ChatMessage from "./chat-message";
import { 
  Send, Paperclip, ChevronLeft, Cpu, 
  RefreshCw, AlertCircle, BookOpen, X
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
    updateLastMessageSources,
    setMessages,
    knowledgeBases,
    selectedChatKb,
    setSelectedChatKb,
    groundingEnabled,
    setGroundingEnabled
  } = useChatStore();

  const [inputVal, setInputVal] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [kbSelectorOpen, setKbSelectorOpen] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch knowledge bases if workspace active
  useEffect(() => {
    if (activeWorkspace) {
      apiService.fetchKnowledgeBases(activeWorkspace.id);
    }
  }, [activeWorkspace]);

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

    // 2. Append user message
    const userMessage = {
      id: Date.now(),
      conversation_id: convoId,
      role: "user" as const,
      content: prompt,
      created_at: new Date().toISOString()
    };
    addMessage(userMessage);

    // 3. Append empty assistant message
    const assistantMessage = {
      id: Date.now() + 1,
      conversation_id: convoId,
      role: "assistant" as const,
      content: "",
      created_at: new Date().toISOString()
    };
    addMessage(assistantMessage);

    // 4. Stream response using active Grounding configs
    let accumulatedText = "";
    try {
      await apiService.streamChat(
        convoId,
        prompt,
        activeWorkspace.id,
        groundingEnabled ? (selectedChatKb?.id || null) : null,
        groundingEnabled,
        (token) => {
          accumulatedText += token;
          updateLastMessageContent(accumulatedText);
        },
        (sources) => {
          updateLastMessageSources(sources);
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
    <main className="relative flex h-full flex-1 flex-col bg-[#09090b]">
      
      {/* Top Header Navigation bar */}
      <header className="flex h-14 items-center justify-between border-b border-zinc-800 bg-zinc-950/50 backdrop-blur px-6">
        <div className="flex items-center gap-3">
          {!sidebarOpen && (
            <button
              onClick={toggleSidebar}
              className="rounded-lg border border-zinc-800 bg-zinc-950 p-1.5 hover:bg-zinc-900 text-zinc-400 hover:text-white transition"
            >
              <ChevronLeft className="h-4 w-4 rotate-180" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-500" />
            <h1 className="text-sm font-semibold text-white tracking-tight">
              {activeConversation ? activeConversation.title : "New Chat"}
            </h1>
          </div>
        </div>
        
        {activeConversation && (
          <div className="text-[10px] bg-indigo-500/10 text-indigo-400 font-semibold px-2 py-0.5 rounded border border-indigo-500/20 uppercase tracking-wide">
            Model: Local Qwen LoRA
          </div>
        )}
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-6">
        {!activeConversation && messages.length === 0 ? (
          /* Welcome Hero Panel */
          <div className="flex h-full flex-col items-center justify-center text-center max-w-[600px] mx-auto space-y-6 mt-[8%]">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-500">
              <Cpu className="h-8 w-8" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-white">
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
                  className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3.5 text-left text-xs font-semibold text-zinc-400 hover:border-indigo-500 hover:text-white transition duration-150"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Render chat history bubbles */
          <div className="max-w-[760px] mx-auto space-y-6">
            {messages.map((msg, idx) => (
              <ChatMessage 
                key={msg.id} 
                message={msg} 
                previousMessage={idx > 0 ? messages[idx - 1] : undefined} 
              />
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
      <div className="border-t border-zinc-850 bg-zinc-950/40 backdrop-blur p-4">
        <div className="max-w-[760px] mx-auto space-y-3">
          
          {/* Grounding Toggle & KB Selector Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-zinc-900/30 p-2.5 rounded-xl border border-zinc-850/80">
            <div className="flex items-center gap-3">
              {/* Grounding switch */}
              <button 
                onClick={() => setGroundingEnabled(!groundingEnabled)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition font-semibold ${
                  groundingEnabled 
                    ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" 
                    : "border-zinc-800 bg-zinc-950 text-zinc-500 hover:text-zinc-400"
                }`}
              >
                <div className={`h-2 w-2 rounded-full ${groundingEnabled ? "bg-emerald-500 animate-pulse" : "bg-zinc-600"}`} />
                Grounded Mode: {groundingEnabled ? "ON" : "OFF"}
              </button>

              {/* Selected KB badge */}
              {groundingEnabled && (
                <div className="relative">
                  {selectedChatKb ? (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-indigo-500/25 bg-indigo-500/5 text-indigo-400">
                      <span className="text-sm leading-none shrink-0">{selectedChatKb.icon}</span>
                      <span className="font-semibold truncate max-w-[150px]">{selectedChatKb.title}</span>
                      <button 
                        onClick={() => setSelectedChatKb(null)}
                        className="p-0.5 rounded hover:bg-indigo-500/10 text-indigo-400/70 hover:text-indigo-400 transition"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ) : (
                    <button 
                      onClick={() => setKbSelectorOpen(!kbSelectorOpen)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 bg-zinc-950 hover:bg-zinc-900 text-zinc-400 hover:text-zinc-300 transition"
                    >
                      <BookOpen className="h-3.5 w-3.5" />
                      <span>Select Knowledge Source</span>
                    </button>
                  )}

                  {/* KB Selector Dropdown */}
                  {kbSelectorOpen && (
                    <div className="absolute bottom-full left-0 mb-2 w-64 rounded-xl border border-zinc-800 bg-zinc-950 p-2 shadow-2xl z-50 space-y-1">
                      <p className="text-[10px] font-bold text-zinc-500 px-2 py-1.5 uppercase tracking-wider">
                        Available Bases ({knowledgeBases.length})
                      </p>
                      {knowledgeBases.length === 0 ? (
                        <p className="text-[10px] text-zinc-600 px-2 py-2">No bases. Add some in Database tab.</p>
                      ) : (
                        knowledgeBases.map((kb) => (
                          <button
                            key={kb.id}
                            onClick={() => {
                              setSelectedChatKb(kb);
                              setKbSelectorOpen(false);
                            }}
                            className="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-zinc-900 text-left text-zinc-300 hover:text-white transition"
                          >
                            <span className="text-base shrink-0">{kb.icon}</span>
                            <span className="font-semibold truncate">{kb.title}</span>
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
            {groundingEnabled && !selectedChatKb && (
              <span className="text-[10px] text-zinc-500 italic">Select a source above to restrict AI context answers.</span>
            )}
            {groundingEnabled && selectedChatKb && (
              <span className="text-[10px] text-emerald-500/80 font-semibold tracking-wide uppercase">Fully Grounded</span>
            )}
          </div>

          {/* Text Input Block */}
          <div className="relative flex items-end gap-2 rounded-xl border border-zinc-850 bg-zinc-950 p-2 shadow-sm focus-within:border-indigo-500/60 transition">
            <button 
              onClick={() => setKbSelectorOpen(!kbSelectorOpen)}
              className="rounded-lg p-2 text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300 transition" 
              title="Select Knowledge Base"
            >
              <Paperclip className="h-4 w-4" />
            </button>
            
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                groundingEnabled && selectedChatKb 
                  ? `Ask a question grounded on "${selectedChatKb.title}"...`
                  : "Ask a question..."
              }
              className="flex-1 resize-none bg-transparent py-2.5 px-1.5 text-sm text-white placeholder-zinc-500 outline-none min-h-[40px] max-h-[200px]"
              disabled={isStreaming}
            />
            
            <button
              onClick={handleSend}
              disabled={!inputVal.trim() || isStreaming}
              className={`rounded-lg p-2.5 transition ${
                inputVal.trim() && !isStreaming
                  ? "bg-indigo-600 text-white hover:bg-indigo-500 shadow-md"
                  : "text-zinc-600 bg-zinc-900 cursor-not-allowed"
              }`}
            >
              {isStreaming ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>

        </div>
        <div className="text-[10px] text-center text-zinc-600 mt-2.5">
          Nexora AI can make mistakes. Verify critical code and logic.
        </div>
      </div>

    </main>
  );
}
