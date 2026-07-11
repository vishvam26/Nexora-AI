"use client";

import React, { useState, useEffect, useRef } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { KnowledgeBase, KnowledgeDocument, SemanticChunk } from "../types/chat";
import { 
  UploadCloud, FileText, Trash2, Plus, Database, 
  CheckCircle2, XCircle, Loader2, RefreshCw, File, 
  ArrowLeft, Search, SlidersHorizontal, Calendar, 
  ChevronLeft, ChevronRight, HelpCircle
} from "lucide-react";

interface UploadQueueItem {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: "uploading" | "completed" | "failed";
  error?: string;
}

export default function KnowledgeArea() {
  const { 
    activeWorkspace, 
    knowledgeBases, 
    activeKnowledgeBase,
    documents,
    setActiveKnowledgeBase,
    setDocuments,
    setActiveView
  } = useChatStore();

  // Navigation and Tab State
  const [activeTab, setActiveTab] = useState<"files" | "search">("files");

  // KB creation forms
  const [kbTitle, setKbTitle] = useState("");
  const [kbDesc, setKbDesc] = useState("");
  const [isCreatingKB, setIsCreatingKB] = useState(false);

  // File Upload Queue State
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Semantic Search State
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(5);
  const [offset, setOffset] = useState(0);
  const [fileTypeFilter, setFileTypeFilter] = useState("");
  const [startDateFilter, setStartDateFilter] = useState("");
  const [endDateFilter, setEndDateFilter] = useState("");
  const [searchResults, setSearchResults] = useState<SemanticChunk[]>([]);
  const [totalHits, setTotalHits] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Poll for document status updates if any are in "Processing" or "Uploading" state
  useEffect(() => {
    if (!activeKnowledgeBase) return;

    // Load initial documents and reset tab/results
    setIsLoadingDocs(true);
    setActiveTab("files");
    setSearchResults([]);
    setUploadQueue([]);
    setQueryText("");
    setOffset(0);
    
    apiService.fetchDocuments(activeKnowledgeBase.id)
      .finally(() => setIsLoadingDocs(false));
  }, [activeKnowledgeBase]);

  useEffect(() => {
    if (!activeKnowledgeBase) return;

    const hasPendingDocs = documents.some(
      (doc) => doc.status === "Uploading" || doc.status === "Processing"
    );

    if (!hasPendingDocs) return;

    // Poll every 3 seconds
    const interval = setInterval(() => {
      apiService.fetchDocuments(activeKnowledgeBase.id);
    }, 3000);

    return () => clearInterval(interval);
  }, [activeKnowledgeBase, documents]);

  // Load knowledge bases on mount or when workspace changes
  useEffect(() => {
    if (activeWorkspace) {
      apiService.fetchKnowledgeBases(activeWorkspace.id);
    }
  }, [activeWorkspace]);

  // Trigger search on pagination (offset) changes
  useEffect(() => {
    if (queryText.trim() && activeKnowledgeBase) {
      executeSearch(true); // run search keeping previous query text
    }
  }, [offset]);

  const handleCreateKB = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !kbTitle.trim()) return;
    try {
      const newKB = await apiService.createKnowledgeBase(
        activeWorkspace.id,
        kbTitle.trim(),
        kbDesc.trim()
      );
      setActiveKnowledgeBase(newKB);
      setKbTitle("");
      setKbDesc("");
      setIsCreatingKB(false);
    } catch (err) {
      console.error("Failed to create knowledge base:", err);
    }
  };

  const handleDeleteKB = async (kbId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!activeWorkspace) return;
    if (confirm("Are you sure you want to delete this Knowledge Base and all its documents?")) {
      try {
        await apiService.deleteKnowledgeBase(activeWorkspace.id, kbId);
        if (activeKnowledgeBase?.id === kbId) {
          setActiveKnowledgeBase(null);
          setDocuments([]);
        }
      } catch (err) {
        console.error("Failed to delete knowledge base:", err);
      }
    }
  };

  const handleDeleteDoc = async (docId: number) => {
    if (!activeKnowledgeBase) return;
    if (confirm("Are you sure you want to delete this document from the Knowledge Base?")) {
      try {
        await apiService.deleteDocument(activeKnowledgeBase.id, docId);
      } catch (err) {
        console.error("Failed to delete document:", err);
      }
    }
  };

  // Upload Logic
  const handleFiles = (files: FileList) => {
    if (!activeKnowledgeBase) return;

    Array.from(files).forEach((file) => {
      const queueId = Math.random().toString(36).substring(7);
      
      const newQueueItem: UploadQueueItem = {
        id: queueId,
        name: file.name,
        size: file.size,
        progress: 0,
        status: "uploading",
      };

      setUploadQueue((prev) => [newQueueItem, ...prev]);

      apiService.uploadDocument(activeKnowledgeBase.id, file, (progress) => {
        setUploadQueue((prev) =>
          prev.map((item) => (item.id === queueId ? { ...item, progress } : item))
        );
      })
      .then(() => {
        setUploadQueue((prev) =>
          prev.map((item) =>
            item.id === queueId ? { ...item, status: "completed", progress: 100 } : item
          )
        );
      })
      .catch((err) => {
        setUploadQueue((prev) =>
          prev.map((item) =>
            item.id === queueId
              ? { ...item, status: "failed", error: err.response?.data?.detail || "Upload failed" }
              : item
          )
        );
      });
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  // Semantic Search execution
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0); // Reset page to 0 on new query submission
    executeSearch(false);
  };

  const executeSearch = async (isPagination: boolean = false) => {
    if (!activeWorkspace || !activeKnowledgeBase || !queryText.trim()) return;

    setIsSearching(true);
    try {
      const data = await apiService.retrieveSemanticChunks(
        activeWorkspace.id,
        activeKnowledgeBase.id,
        queryText.trim(),
        topK,
        isPagination ? offset : 0,
        fileTypeFilter || null,
        startDateFilter || null,
        endDateFilter || null
      );
      setSearchResults(data.results || []);
      setTotalHits(data.total || 0);
    } catch (err) {
      console.error("Vector search failed:", err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Text highlighting processor
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    // Tokenize query words, exclude short noise words
    const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
    if (words.length === 0) return text;

    // Regex escape
    const escapedWords = words.map(w => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
    // Match words as boundaries if possible, otherwise character matching
    const regex = new RegExp(`(${escapedWords.join("|")})`, "gi");

    const parts = text.split(regex);
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-indigo-500/30 text-indigo-200 px-0.5 rounded border border-indigo-500/30 font-medium">
          {part}
        </mark>
      ) : part
    );
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const pageCount = Math.ceil(totalHits / topK);
  const currentPage = Math.floor(offset / topK) + 1;

  return (
    <div className="flex h-full w-full overflow-hidden bg-transparent text-[#f4f4f5]">
      {/* Left Panel: Knowledge Bases List */}
      <div className="w-[320px] flex-shrink-0 border-r border-zinc-900 bg-[#080808]/60 backdrop-blur-md flex flex-col justify-between z-10">
        <div className="p-6 overflow-y-auto flex-1">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-indigo-400" />
              <h2 className="text-base font-bold text-white tracking-tight">Knowledge Bases</h2>
            </div>
            <button 
              onClick={() => setIsCreatingKB(true)}
              className="p-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 hover:text-indigo-300 transition-all border border-indigo-500/10"
              title="Create Knowledge Base"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {isCreatingKB && (
            <form onSubmit={handleCreateKB} className="mb-6 p-4 rounded-xl border border-zinc-800 bg-zinc-900/30 space-y-4 animate-fade-in-up">
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">
                  Name
                </label>
                <input 
                  type="text" 
                  value={kbTitle}
                  onChange={(e) => setKbTitle(e.target.value)}
                  placeholder="e.g. Finance Data Q1"
                  required
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-700 outline-none focus:border-indigo-500/40 transition"
                />
              </div>
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">
                  Description
                </label>
                <textarea 
                  value={kbDesc}
                  onChange={(e) => setKbDesc(e.target.value)}
                  placeholder="What is this knowledge base for?"
                  rows={2}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-white placeholder-zinc-700 outline-none focus:border-indigo-500/40 transition resize-none"
                />
              </div>
              <div className="flex gap-2 justify-end text-[10px]">
                <button 
                  type="button"
                  onClick={() => setIsCreatingKB(false)}
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-3 py-1.5 rounded-lg bg-indigo-650 hover:bg-indigo-550 text-white font-semibold transition"
                >
                  Create
                </button>
              </div>
            </form>
          )}

          <div className="space-y-2">
            {knowledgeBases.length === 0 ? (
              <p className="text-xs text-zinc-650 text-center py-8">No knowledge bases yet. Click + to add one.</p>
            ) : (
              knowledgeBases.map((kb) => (
                <div 
                  key={kb.id}
                  onClick={() => setActiveKnowledgeBase(kb)}
                  className={`group flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition-all ${
                    activeKnowledgeBase?.id === kb.id 
                      ? "border-indigo-500/30 bg-indigo-500/5 text-white" 
                      : "border-zinc-900 bg-zinc-950/20 hover:bg-zinc-900/20 text-zinc-450 hover:text-zinc-200"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-lg shrink-0">{kb.icon || "📚"}</span>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold truncate leading-tight">{kb.title}</p>
                      {kb.description && (
                        <p className="text-[10px] text-zinc-550 truncate mt-0.5">{kb.description}</p>
                      )}
                    </div>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteKB(kb.id, e)}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/15 text-zinc-550 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Back to Chat view Footer */}
        <div className="p-4 border-t border-zinc-900 bg-zinc-950/20">
          <button 
            onClick={() => setActiveView("chat")}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-zinc-800 bg-[#09090b]/40 hover:bg-zinc-900 text-xs font-semibold text-zinc-300 hover:text-white transition-all"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Workspace
          </button>
        </div>
      </div>

      {/* Right Panel: Selected KB dashboard */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-[#09090b]/20 z-0">
        {activeKnowledgeBase ? (
          <div className="p-8 max-w-5xl w-full mx-auto space-y-8 animate-fade-in">
            {/* Header info */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{activeKnowledgeBase.icon || "📚"}</span>
                  <h1 className="text-2xl font-bold text-white tracking-tight font-playfair">{activeKnowledgeBase.title}</h1>
                </div>
                {activeKnowledgeBase.description && (
                  <p className="text-zinc-500 text-xs mt-1.5 leading-relaxed">{activeKnowledgeBase.description}</p>
                )}
              </div>
              
              {/* Tab Navigation */}
              <div className="flex bg-zinc-950 border border-zinc-900 p-1 rounded-xl">
                <button 
                  onClick={() => setActiveTab("files")}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                    activeTab === "files" 
                      ? "bg-indigo-650 text-white shadow-lg shadow-indigo-650/15" 
                      : "text-zinc-450 hover:text-zinc-200"
                  }`}
                >
                  Document Files
                </button>
                <button 
                  onClick={() => setActiveTab("search")}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                    activeTab === "search" 
                      ? "bg-indigo-650 text-white shadow-lg shadow-indigo-650/15" 
                      : "text-zinc-450 hover:text-zinc-200"
                  }`}
                >
                  <Search className="h-3.5 w-3.5" />
                  Semantic Simulator
                </button>
              </div>
            </div>

            {/* TAB 1: Document Upload & Management */}
            {activeTab === "files" && (
              <>
                {/* Drag & Drop upload component */}
                <div 
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all ${
                    isDragging 
                      ? "border-indigo-500 bg-indigo-500/5 text-white scale-[0.99]" 
                      : "border-zinc-800 bg-zinc-950/20 hover:bg-zinc-950/40 hover:border-zinc-700 text-zinc-450 hover:text-zinc-200"
                  }`}
                >
                  <input 
                    type="file" 
                    multiple
                    ref={fileInputRef}
                    onChange={(e) => e.target.files && handleFiles(e.target.files)}
                    className="hidden" 
                  />
                  <UploadCloud className="h-10 w-10 text-zinc-500 mb-4 animate-pulse" />
                  <h3 className="text-sm font-semibold text-white mb-1.5">Drag & Drop Files Here</h3>
                  <p className="text-xs text-zinc-500 text-center max-w-sm mb-1 leading-normal">
                    Supports parallel uploading of CSV, Excel, PDF, DOCX, TXT, MD, HTML, and Images.
                  </p>
                  <p className="text-[10px] text-zinc-650 font-semibold tracking-wider uppercase">Files up to 50MB</p>
                </div>

                {/* Active Upload Queue */}
                {uploadQueue.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Upload Queue</h3>
                    <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
                      {uploadQueue.map((item) => (
                        <div key={item.id} className="p-4 rounded-xl border border-zinc-850 bg-zinc-950/40 flex items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-850">
                            <File className="h-5 w-5 text-zinc-450" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="font-semibold text-white truncate pr-2">{item.name}</span>
                              <span className="text-zinc-500 shrink-0 font-mono">{item.progress}%</span>
                            </div>
                            <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
                              <div 
                                className={`h-full transition-all duration-300 ${
                                  item.status === "failed" ? "bg-red-500" : "bg-indigo-500"
                                }`}
                                style={{ width: `${item.progress}%` }}
                              />
                            </div>
                            {item.error && (
                              <p className="text-[10px] text-red-400 truncate mt-1">{item.error}</p>
                            )}
                          </div>
                          {item.status === "completed" && <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />}
                          {item.status === "failed" && <XCircle className="h-5 w-5 text-red-400 shrink-0" />}
                          {item.status === "uploading" && <Loader2 className="h-4 w-4 text-indigo-400 animate-spin shrink-0" />}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Uploaded Documents List */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Uploaded Documents</h3>
                    {isLoadingDocs && <Loader2 className="h-4 w-4 text-zinc-500 animate-spin" />}
                  </div>

                  {documents.length === 0 ? (
                    <div className="text-center py-16 border border-zinc-900 bg-zinc-950/20 rounded-2xl select-none">
                      <FileText className="h-10 w-10 text-zinc-700 mx-auto mb-4" />
                      <h4 className="text-sm font-semibold text-zinc-400">No documents uploaded yet</h4>
                      <p className="text-xs text-zinc-650 mt-1">Upload files above to compile knowledge for this base.</p>
                    </div>
                  ) : (
                    <div className="overflow-hidden rounded-xl border border-zinc-900 bg-zinc-950/10">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-zinc-900 text-[10px] font-semibold text-zinc-550 uppercase tracking-wider bg-zinc-950/40">
                            <th className="py-4 px-6">Filename</th>
                            <th className="py-4 px-6">Mime Type</th>
                            <th className="py-4 px-6">Size</th>
                            <th className="py-4 px-6">Status</th>
                            <th className="py-4 px-6 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-900/60 text-zinc-350 bg-zinc-950/5">
                          {documents.map((doc) => (
                            <tr key={doc.id} className="hover:bg-zinc-900/20 transition-colors">
                              <td className="py-3.5 px-6 font-medium text-white truncate max-w-xs">
                                <div className="flex items-center gap-2.5">
                                  <FileText className="h-4 w-4 shrink-0 text-indigo-400" />
                                  <span className="truncate" title={doc.filename}>{doc.filename}</span>
                                </div>
                              </td>
                              <td className="py-3.5 px-6 text-zinc-550 truncate max-w-[150px]" title={doc.mime_type}>
                                {doc.mime_type}
                              </td>
                              <td className="py-3.5 px-6 text-zinc-450 font-mono text-[10px]">
                                {formatSize(doc.size)}
                              </td>
                              <td className="py-3.5 px-6">
                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium leading-none ${
                                  doc.status === "Completed" 
                                    ? "bg-green-500/10 text-green-400 border border-green-500/20" 
                                    : doc.status === "Failed"
                                    ? "bg-red-500/10 text-red-400 border border-red-500/20"
                                    : "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                }`}>
                                  {doc.status === "Completed" && <CheckCircle2 className="h-3 w-3" />}
                                  {doc.status === "Failed" && <XCircle className="h-3 w-3" />}
                                  {(doc.status === "Uploading" || doc.status === "Processing") && (
                                    <RefreshCw className="h-3 w-3 animate-spin" />
                                  )}
                                  {doc.status}
                                </span>
                              </td>
                              <td className="py-3.5 px-6 text-right">
                                <button 
                                  onClick={() => handleDeleteDoc(doc.id)}
                                  className="p-1.5 rounded-lg hover:bg-red-500/15 text-zinc-550 hover:text-red-400 transition-all"
                                  title="Delete File"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* TAB 2: Semantic Search Simulator */}
            {activeTab === "search" && (
              <div className="space-y-6">
                <form onSubmit={handleSearchSubmit} className="space-y-4">
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-500" />
                      <input 
                        type="text" 
                        value={queryText}
                        onChange={(e) => setQueryText(e.target.value)}
                        placeholder="Search indexed context (e.g. Sales increase target)..."
                        required
                        className="w-full rounded-xl border border-zinc-800 bg-zinc-950 pl-10 pr-4 py-3.5 text-xs text-white placeholder-zinc-700 outline-none focus:border-indigo-500/40 transition"
                      />
                    </div>
                    <button 
                      type="submit"
                      disabled={isSearching}
                      className="px-6 rounded-xl bg-indigo-650 hover:bg-indigo-550 font-semibold text-white transition-all flex items-center gap-2 text-xs disabled:opacity-55"
                    >
                      {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                      Search
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                      className={`p-3 rounded-xl border transition-all ${
                        showAdvancedFilters 
                          ? "border-indigo-500 bg-indigo-500/5 text-indigo-400" 
                          : "border-zinc-800 hover:bg-zinc-900 text-zinc-500"
                      }`}
                      title="Toggle Filters"
                    >
                      <SlidersHorizontal className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Advanced Filters Drawer */}
                  {showAdvancedFilters && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5 rounded-2xl border border-zinc-850 bg-zinc-950/30 text-[11px] animate-fade-in-up">
                      <div>
                        <label className="block text-zinc-500 uppercase tracking-wider mb-2 font-semibold">Format Filter</label>
                        <select 
                          value={fileTypeFilter}
                          onChange={(e) => setFileTypeFilter(e.target.value)}
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500/40"
                        >
                          <option value="">All Formats</option>
                          <option value="application/pdf">PDF Document</option>
                          <option value="application/vnd.openxmlformats-officedocument.wordprocessingml.document">Word (DOCX)</option>
                          <option value="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">Excel (XLSX)</option>
                          <option value="text/csv">CSV Table</option>
                          <option value="text/plain">Plain Text / MD</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-zinc-500 uppercase tracking-wider mb-2 font-semibold">Start Date</label>
                        <input 
                          type="date" 
                          value={startDateFilter}
                          onChange={(e) => setStartDateFilter(e.target.value)}
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500/40 text-xs"
                        />
                      </div>

                      <div>
                        <label className="block text-zinc-500 uppercase tracking-wider mb-2 font-semibold">Max Results (K)</label>
                        <input 
                          type="number"
                          min="1"
                          max="20"
                          value={topK}
                          onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-white outline-none focus:border-indigo-500/40 font-mono text-xs"
                        />
                      </div>
                    </div>
                  )}
                </form>

                {/* Results Workspace */}
                {isSearching ? (
                  <div className="py-24 text-center">
                    <Loader2 className="h-8 w-8 text-indigo-400 animate-spin mx-auto mb-4" />
                    <p className="text-zinc-500 text-xs">Embedding search query and scanning Qdrant database...</p>
                  </div>
                ) : searchResults.length > 0 ? (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between text-[10px] text-zinc-500 font-semibold uppercase tracking-wider px-1">
                      <span>Matches ({totalHits} chunks found)</span>
                      <span className="font-mono">Page {currentPage} of {pageCount}</span>
                    </div>

                    <div className="space-y-4">
                      {searchResults.map((match) => (
                        <div key={match.chunk_id} className="p-5 rounded-2xl border border-zinc-900 bg-zinc-950/20 hover:border-zinc-800 transition-all flex flex-col gap-3">
                          {/* Match Header */}
                          <div className="flex items-center justify-between gap-4 text-[10px]">
                            <div className="flex items-center gap-2 text-zinc-500">
                              <FileText className="h-4 w-4 text-indigo-400 shrink-0" />
                              <span className="font-semibold text-white truncate max-w-[200px]" title={match.file_name}>
                                {match.file_name}
                              </span>
                              <span className="text-zinc-650">•</span>
                              <span>Page {match.page_number}</span>
                              {match.section_title && (
                                <>
                                  <span className="text-zinc-650">•</span>
                                  <span className="truncate max-w-[150px]">{match.section_title}</span>
                                </>
                              )}
                            </div>
                            
                            {/* Score Badges */}
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/15 font-mono text-[9px] font-bold">
                                Match: {Math.round(match.final_score * 100)}%
                              </span>
                            </div>
                          </div>

                          {/* Matching text body */}
                          <p className="text-zinc-350 text-xs leading-relaxed whitespace-pre-wrap">
                            {highlightText(match.text, queryText)}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Pagination Controls */}
                    {pageCount > 1 && (
                      <div className="flex items-center justify-between border-t border-zinc-900 pt-6 mt-6">
                        <button
                          disabled={offset === 0}
                          onClick={() => setOffset(Math.max(0, offset - topK))}
                          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-950 text-[10px] font-bold tracking-wide uppercase text-zinc-400 hover:text-white transition-all disabled:opacity-40"
                        >
                          <ChevronLeft className="h-4 w-4" />
                          Previous Page
                        </button>
                        <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">
                          Page <strong className="text-white">{currentPage}</strong> / {pageCount}
                        </span>
                        <button
                          disabled={offset + topK >= totalHits}
                          onClick={() => setOffset(offset + topK)}
                          className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-zinc-800 bg-zinc-950 text-[10px] font-bold tracking-wide uppercase text-zinc-400 hover:text-white transition-all disabled:opacity-40"
                        >
                          Next Page
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </div>
                ) : queryText.trim() ? (
                  <div className="py-24 text-center border border-zinc-900 bg-zinc-950/20 rounded-2xl select-none">
                    <HelpCircle className="h-10 w-10 text-zinc-700 mx-auto mb-4" />
                    <h4 className="text-sm font-semibold text-zinc-400">No matching segments found</h4>
                    <p className="text-xs text-zinc-650 mt-1">Try refining your keyword query or reducing similarity constraints.</p>
                  </div>
                ) : (
                  <div className="py-24 text-center border border-zinc-900 bg-zinc-950/20 rounded-2xl select-none">
                    <Search className="h-10 w-10 text-zinc-700 mx-auto mb-4" />
                    <h4 className="text-sm font-semibold text-zinc-400">Search Simulator Ready</h4>
                    <p className="text-xs text-zinc-650 mt-1">Enter a query above to retrieve and test semantic vector context matching.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-sm mx-auto select-none mt-[8%]">
            <div className="h-16 w-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-400 border border-indigo-500/20 mb-6 animate-float">
              <Database className="h-7 w-7" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2 font-playfair">Select a Knowledge Base</h2>
            <p className="text-zinc-550 text-xs leading-relaxed mb-6">
              Choose an existing Knowledge Base from the sidebar, or create a new one to begin uploading documents, extracting text, and parsing structured tables.
            </p>
            <button 
              onClick={() => setIsCreatingKB(true)}
              className="flex items-center gap-2 bg-indigo-650 hover:bg-indigo-550 text-white text-xs font-semibold py-2.5 px-4 rounded-xl transition-all shadow-lg shadow-indigo-900/40"
            >
              <Plus className="h-4 w-4" />
              Create New Base
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


