"use client";

import React, { useState, useEffect, useRef } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { KnowledgeBase, KnowledgeDocument } from "../types/chat";
import { 
  UploadCloud, FileText, Trash2, Plus, Database, 
  CheckCircle2, XCircle, Loader2, RefreshCw, File, 
  BookOpen, FolderOpen, ArrowLeft
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

  const [kbTitle, setKbTitle] = useState("");
  const [kbDesc, setKbDesc] = useState("");
  const [isCreatingKB, setIsCreatingKB] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll for document status updates if any are in "Processing" or "Uploading" state
  useEffect(() => {
    if (!activeKnowledgeBase) return;

    // Load initial documents
    setIsLoadingDocs(true);
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

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-[#09090b] text-[#f4f4f5]">
      {/* Left Panel: Knowledge Bases List */}
      <div className="w-[320px] flex-shrink-0 border-r border-zinc-800 bg-zinc-950 flex flex-col justify-between">
        <div className="p-6 overflow-y-auto flex-1">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-indigo-500" />
              <h2 className="text-lg font-bold text-white">Knowledge Bases</h2>
            </div>
            <button 
              onClick={() => setIsCreatingKB(true)}
              className="p-1.5 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 hover:text-indigo-300 transition"
              title="Create Knowledge Base"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {isCreatingKB && (
            <form onSubmit={handleCreateKB} className="mb-6 p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">
                  Name
                </label>
                <input 
                  type="text" 
                  value={kbTitle}
                  onChange={(e) => setKbTitle(e.target.value)}
                  placeholder="e.g. Finance Data Q1"
                  required
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white placeholder-zinc-600 outline-none focus:border-indigo-500 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">
                  Description
                </label>
                <textarea 
                  value={kbDesc}
                  onChange={(e) => setKbDesc(e.target.value)}
                  placeholder="What is this knowledge base for?"
                  rows={2}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white placeholder-zinc-600 outline-none focus:border-indigo-500 transition resize-none"
                />
              </div>
              <div className="flex gap-2 justify-end text-xs">
                <button 
                  type="button"
                  onClick={() => setIsCreatingKB(false)}
                  className="px-3 py-1.5 rounded-lg border border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition"
                >
                  Create
                </button>
              </div>
            </form>
          )}

          <div className="space-y-2">
            {knowledgeBases.length === 0 ? (
              <p className="text-sm text-zinc-500 text-center py-8">No knowledge bases yet. Click + to add one.</p>
            ) : (
              knowledgeBases.map((kb) => (
                <div 
                  key={kb.id}
                  onClick={() => setActiveKnowledgeBase(kb)}
                  className={`group flex items-center justify-between p-3.5 rounded-xl border cursor-pointer transition ${
                    activeKnowledgeBase?.id === kb.id 
                      ? "border-indigo-500/50 bg-indigo-500/5 text-white" 
                      : "border-zinc-800/60 bg-zinc-900/20 hover:bg-zinc-900/40 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-xl shrink-0">{kb.icon || "📚"}</span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate leading-tight">{kb.title}</p>
                      {kb.description && (
                        <p className="text-xs text-zinc-500 truncate mt-0.5">{kb.description}</p>
                      )}
                    </div>
                  </div>
                  <button 
                    onClick={(e) => handleDeleteKB(kb.id, e)}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-500/10 text-zinc-500 hover:text-red-400 transition"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Back to Chat view Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950/40">
          <button 
            onClick={() => setActiveView("chat")}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-zinc-800 bg-zinc-900/40 hover:bg-zinc-900 text-sm font-semibold text-zinc-300 hover:text-white transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Chat Workspace
          </button>
        </div>
      </div>

      {/* Right Panel: Selected KB documents workspace */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-zinc-900/10">
        {activeKnowledgeBase ? (
          <div className="p-8 max-w-5xl w-full mx-auto space-y-8">
            {/* Header info */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-800/80 pb-6">
              <div>
                <div className="flex items-center gap-3">
                  <span className="text-3xl">{activeKnowledgeBase.icon || "📚"}</span>
                  <h1 className="text-2xl font-bold text-white tracking-tight">{activeKnowledgeBase.title}</h1>
                </div>
                {activeKnowledgeBase.description && (
                  <p className="text-zinc-400 text-sm mt-1.5 leading-relaxed">{activeKnowledgeBase.description}</p>
                )}
              </div>
              <div className="flex items-center gap-3 bg-zinc-900/60 border border-zinc-800 px-4 py-2 rounded-xl text-xs text-zinc-400">
                <div className="flex flex-col text-right">
                  <span className="font-semibold text-white">{documents.length} Files</span>
                  <span>Indexed Context</span>
                </div>
              </div>
            </div>

            {/* Drag & Drop upload component */}
            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition ${
                isDragging 
                  ? "border-indigo-500 bg-indigo-500/5 text-white scale-[0.99]" 
                  : "border-zinc-800 bg-zinc-950/30 hover:bg-zinc-950/50 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <input 
                type="file" 
                multiple
                ref={fileInputRef}
                onChange={(e) => e.target.files && handleFiles(e.target.files)}
                className="hidden" 
              />
              <UploadCloud className="h-10 w-10 text-zinc-500 group-hover:text-indigo-400 mb-4 transition" />
              <h3 className="text-base font-semibold text-white mb-1.5">Drag & Drop Files Here</h3>
              <p className="text-xs text-zinc-500 text-center max-w-sm mb-1 leading-normal">
                Supports parallel uploading of CSV, Excel (.xlsx, .xls), PDF, DOCX, TXT, MD, HTML, and Images.
              </p>
              <p className="text-[10px] text-zinc-600">Files up to 50MB</p>
            </div>

            {/* Active Upload Queue */}
            {uploadQueue.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Upload Queue</h3>
                <div className="grid gap-3 grid-cols-1 md:grid-cols-2">
                  {uploadQueue.map((item) => (
                    <div key={item.id} className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/40 flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-800">
                        <File className="h-5 w-5 text-zinc-400" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-semibold text-white truncate pr-2">{item.name}</span>
                          <span className="text-zinc-500 shrink-0">{item.progress}%</span>
                        </div>
                        {/* Progress bar */}
                        <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
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
                      {item.status === "completed" && <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />}
                      {item.status === "failed" && <XCircle className="h-5 w-5 text-red-500 shrink-0" />}
                      {item.status === "uploading" && <Loader2 className="h-4 w-4 text-indigo-500 animate-spin shrink-0" />}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Uploaded Documents List */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Uploaded Documents</h3>
                {isLoadingDocs && <Loader2 className="h-4 w-4 text-zinc-500 animate-spin" />}
              </div>

              {documents.length === 0 ? (
                <div className="text-center py-16 border border-zinc-800/80 bg-zinc-950/20 rounded-2xl">
                  <FileText className="h-12 w-12 text-zinc-700 mx-auto mb-4" />
                  <h4 className="text-sm font-semibold text-zinc-400">No documents uploaded yet</h4>
                  <p className="text-xs text-zinc-600 mt-1">Upload files above to compile knowledge for this base.</p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/20">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-zinc-800 text-xs font-semibold text-zinc-500 uppercase tracking-wider bg-zinc-950/40">
                        <th className="py-4 px-6">Filename</th>
                        <th className="py-4 px-6">Mime Type</th>
                        <th className="py-4 px-6">Size</th>
                        <th className="py-4 px-6">Status</th>
                        <th className="py-4 px-6 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/80 text-zinc-300">
                      {documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-zinc-900/20 transition-colors">
                          <td className="py-3.5 px-6 font-medium text-white truncate max-w-xs">
                            <div className="flex items-center gap-2.5">
                              <FileText className="h-4 w-4 shrink-0 text-indigo-400" />
                              <span className="truncate">{doc.filename}</span>
                            </div>
                          </td>
                          <td className="py-3.5 px-6 text-zinc-500 truncate max-w-[150px]" title={doc.mime_type}>
                            {doc.mime_type}
                          </td>
                          <td className="py-3.5 px-6 text-zinc-400 font-mono text-xs">
                            {formatSize(doc.size)}
                          </td>
                          <td className="py-3.5 px-6">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium leading-none ${
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
                              className="p-1.5 rounded-lg hover:bg-red-500/10 text-zinc-500 hover:text-red-400 transition"
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
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-sm mx-auto">
            <div className="h-16 w-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-indigo-500 border border-indigo-500/20 mb-6">
              <Database className="h-8 w-8" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2">Select a Knowledge Base</h2>
            <p className="text-zinc-500 text-xs leading-relaxed mb-6">
              Choose an existing Knowledge Base from the sidebar, or create a new one to begin uploading documents, extracting text, and parsing structured tables.
            </p>
            <button 
              onClick={() => setIsCreatingKB(true)}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2.5 px-4 rounded-xl transition"
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
