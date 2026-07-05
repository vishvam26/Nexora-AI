"use client";

import { useState } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { 
  Plus, MessageSquare, Folder, FolderOpen, Search, Pin, 
  Archive, Trash2, LogOut, Sun, Moon, Settings, Cpu,
  ChevronDown, ChevronRight, User, MoreVertical, Database,
  BarChart3, Brain
} from "lucide-react";

export default function ChatSidebar() {
  const {
    user,
    workspaces,
    activeWorkspace,
    folders,
    conversations,
    activeConversation,
    theme,
    sidebarOpen,
    setActiveWorkspace,
    setActiveConversation,
    setMessages,
    toggleTheme,
    logout,
    activeView,
    setActiveView
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [showWorkspaceMenu, setShowWorkspaceMenu] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Record<number, boolean>>({});
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");

  if (!sidebarOpen) return null;

  // Filters conversations based on search text
  const filteredConversations = conversations.filter(c => 
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group conversations by folder
  const conversationsByFolder: Record<number | "root", typeof conversations> = { root: [] };
  filteredConversations.forEach(c => {
    if (c.folder_id) {
      if (!conversationsByFolder[c.folder_id]) {
        conversationsByFolder[c.folder_id] = [];
      }
      conversationsByFolder[c.folder_id].push(c);
    } else {
      conversationsByFolder.root.push(c);
    }
  });

  const handleNewChat = () => {
    setActiveConversation(null);
    setMessages([]);
  };

  const handleSelectConversation = async (convo: typeof conversations[0]) => {
    setActiveConversation(convo);
    try {
      await apiService.fetchMessages(convo.id);
    } catch (e) {
      console.error("Error loading chat messages:", e);
    }
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;
    try {
      await apiService.createWorkspace(newWorkspaceName);
      setNewWorkspaceName("");
      setIsCreatingWorkspace(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim() || !activeWorkspace) return;
    try {
      await apiService.createFolder(newFolderName, activeWorkspace.id);
      setNewFolderName("");
      setIsCreatingFolder(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteConversation = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!activeWorkspace) return;
    if (confirm("Are you sure you want to delete this conversation?")) {
      try {
        await apiService.deleteConversation(id, activeWorkspace.id);
        if (activeConversation?.id === id) {
          handleNewChat();
        }
      } catch (err) {
        console.error(err);
      }
    }
  };

  const toggleFolder = (folderId: number) => {
    setExpandedFolders(prev => ({ ...prev, [folderId]: !prev[folderId] }));
  };

  return (
    <aside className="z-20 flex h-full w-[260px] flex-col border-r border-border bg-sidebar-bg text-foreground transition-all duration-200">
      
      {/* 1. Workspace Selector */}
      <div className="relative border-b border-border p-4">
        <button
          onClick={() => setShowWorkspaceMenu(!showWorkspaceMenu)}
          className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm font-semibold shadow-sm transition hover:bg-zinc-50 dark:hover:bg-zinc-900"
        >
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-indigo-500" />
            <span className="truncate">{activeWorkspace?.name || "Select Workspace"}</span>
          </div>
          <ChevronDown className="h-4 w-4 text-zinc-500" />
        </button>

        {showWorkspaceMenu && (
          <div className="absolute top-[calc(100%-8px)] left-4 right-4 z-30 rounded-lg border border-border bg-card p-2 shadow-lg">
            <div className="max-h-[160px] overflow-y-auto space-y-1">
              {workspaces.map(w => (
                <button
                  key={w.id}
                  onClick={() => {
                    setActiveWorkspace(w);
                    setShowWorkspaceMenu(false);
                  }}
                  className={`w-full rounded-md px-3 py-2 text-left text-xs font-medium transition ${
                    activeWorkspace?.id === w.id
                      ? "bg-sidebar-active text-indigo-600 dark:text-indigo-400 font-semibold"
                      : "hover:bg-zinc-50 dark:hover:bg-zinc-900"
                  }`}
                >
                  {w.name}
                </button>
              ))}
            </div>

            <div className="border-t border-border mt-2 pt-2">
              {isCreatingWorkspace ? (
                <form onSubmit={handleCreateWorkspace} className="flex gap-2">
                  <input
                    type="text"
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                    placeholder="Workspace Name"
                    className="w-full rounded border border-border bg-background px-2 py-1 text-xs outline-none focus:border-indigo-500"
                  />
                  <button type="submit" className="rounded bg-indigo-600 px-2 py-1 text-xs font-semibold text-white">
                    Save
                  </button>
                </form>
              ) : (
                <button
                  onClick={() => setIsCreatingWorkspace(true)}
                  className="flex w-full items-center gap-2 px-2 py-1 text-left text-xs font-semibold text-indigo-600 dark:text-indigo-400"
                >
                  <Plus className="h-3 w-3" />
                  <span>New Workspace</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 2. New Chat & Search Actions */}
      <div className="space-y-3 p-4">
        <button
          onClick={handleNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-hover active:scale-[0.98]"
        >
          <Plus className="h-4 w-4" />
          <span>New Chat</span>
        </button>

        <div className="relative">
          <Search className="absolute top-2.5 left-3 h-4 w-4 text-zinc-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full rounded-lg border border-border bg-card pl-9 pr-4 py-2 text-xs outline-none transition focus:border-indigo-500"
          />
        </div>
      </div>

      {/* 3. Folder & Conversations Tree List */}
      <div className="flex-1 overflow-y-auto px-3 space-y-4">
        
        {/* Folders Section */}
        {folders.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 px-2 mb-2">
              Folders
            </div>
            {folders.map(folder => {
              const isExpanded = expandedFolders[folder.id];
              const folderConvos = conversationsByFolder[folder.id] || [];

              return (
                <div key={folder.id} className="space-y-1">
                  <button
                    onClick={() => toggleFolder(folder.id)}
                    className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-xs text-zinc-600 dark:text-zinc-400 hover:bg-sidebar-active hover:text-foreground"
                  >
                    <div className="flex items-center gap-2">
                      {isExpanded ? <FolderOpen className="h-4 w-4" /> : <Folder className="h-4 w-4" />}
                      <span className="truncate font-medium">{folder.name}</span>
                    </div>
                    {isExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                  </button>

                  {isExpanded && (
                    <div className="border-l border-border ml-4 pl-2 space-y-1">
                      {folderConvos.length === 0 ? (
                        <div className="py-1.5 px-2 text-[10px] text-zinc-400">Empty Folder</div>
                      ) : (
                        folderConvos.map(convo => (
                          <div
                            key={convo.id}
                            onClick={() => handleSelectConversation(convo)}
                            className={`group flex items-center justify-between rounded-md px-2.5 py-1.5 text-xs cursor-pointer transition ${
                              activeConversation?.id === convo.id
                                ? "bg-sidebar-active text-indigo-600 dark:text-indigo-400 font-semibold"
                                : "text-zinc-600 dark:text-zinc-400 hover:bg-sidebar-active hover:text-foreground"
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                              <span className="truncate">{convo.title}</span>
                            </div>
                            <button
                              onClick={(e) => handleDeleteConversation(convo.id, e)}
                              className="hidden group-hover:block hover:text-red-500"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Conversations (Outside Folders) Section */}
        <div className="space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 px-2 mb-2">
            Conversations
          </div>
          {conversationsByFolder.root && conversationsByFolder.root.length > 0 ? (
            conversationsByFolder.root.map(convo => (
              <div
                key={convo.id}
                onClick={() => handleSelectConversation(convo)}
                className={`group flex items-center justify-between rounded-lg px-2.5 py-2 text-xs cursor-pointer transition ${
                  activeConversation?.id === convo.id
                    ? "bg-sidebar-active text-indigo-600 dark:text-indigo-400 font-semibold"
                    : "text-zinc-600 dark:text-zinc-400 hover:bg-sidebar-active hover:text-foreground"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <span className="truncate">{convo.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(convo.id, e)}
                  className="hidden group-hover:block hover:text-red-500"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          ) : (
            <div className="py-2 px-2 text-xs text-zinc-400 italic">No chats started</div>
          )}
        </div>
      </div>

      {/* 4. Settings, Folders creation & Theme Toggles */}
      <div className="border-t border-border p-4 space-y-3">
        {isCreatingFolder ? (
          <form onSubmit={handleCreateFolder} className="flex gap-2">
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder Name"
              className="w-full rounded border border-border bg-background px-2.5 py-1 text-xs outline-none"
            />
            <button type="submit" className="rounded bg-indigo-600 px-2 py-1 text-xs font-semibold text-white">
              Add
            </button>
          </form>
        ) : (
          <button
            onClick={() => setIsCreatingFolder(true)}
            className="flex w-full items-center gap-2 text-xs font-medium text-zinc-500 hover:text-foreground"
          >
            <Folder className="h-4 w-4" />
            <span>Create Folder</span>
          </button>
        )}

        <div className="space-y-1">
          <button
            onClick={() => setActiveView("chat")}
            className={`flex w-full items-center gap-2 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeView === "chat" 
                ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/10" 
                : "text-zinc-500 hover:text-zinc-400"
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Chat Workspace</span>
          </button>
          
          <button
            onClick={() => setActiveView("knowledge")}
            className={`flex w-full items-center gap-2 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeView === "knowledge" 
                ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/10" 
                : "text-zinc-500 hover:text-zinc-400"
            }`}
          >
            <Database className="h-4 w-4" />
            <span>Knowledge Base</span>
          </button>

          <button
            onClick={() => setActiveView("analytics")}
            className={`flex w-full items-center gap-2 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeView === "analytics" 
                ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/10" 
                : "text-zinc-500 hover:text-zinc-400"
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            <span>Analytics Engine</span>
          </button>

          <button
            onClick={() => setActiveView("ml")}
            className={`flex w-full items-center gap-2 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeView === "ml" 
                ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/10" 
                : "text-zinc-500 hover:text-zinc-400"
            }`}
          >
            <Brain className="h-4 w-4" />
            <span>ML Studio</span>
          </button>
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-2 text-xs font-medium text-zinc-500 hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>

        {/* User Profile details */}
        <div className="flex items-center justify-between border-t border-border pt-3 mt-3">
          <div className="flex items-center gap-2 truncate">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
              <User className="h-4 w-4" />
            </div>
            <div className="truncate">
              <div className="truncate text-xs font-semibold leading-none">{user?.full_name || "Active User"}</div>
              <div className="truncate text-[10px] text-zinc-400 mt-1">{user?.email}</div>
            </div>
          </div>
          <button onClick={logout} className="hover:text-red-500 transition" title="Log Out">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
