"use client";

import { useState } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import {
  Plus, MessageSquare, Folder, FolderOpen, Search, Trash2,
  LogOut, Sun, Moon, Cpu, ChevronDown, User, Database,
  BarChart3, Brain, FileText, Sparkles, Terminal, Mail,
  Calendar, Activity, ChevronRight, ChevronLeft, Edit2
} from "lucide-react";

// ─────────────────────────────────────────────
// LEFT ICON NAV BAR — Feature Navigation
// ─────────────────────────────────────────────
const NAV_ITEMS = [
  { view: "chat",      icon: MessageSquare, label: "Chat",           group: "main" },
  { view: "knowledge", icon: Database,      label: "Knowledge Base", group: "main" },
  { view: "analytics", icon: BarChart3,     label: "Analytics",      group: "main" },
  { view: "agents",    icon: Sparkles,      label: "Agents",         group: "studio", badge: "NEW" },
  { view: "sql",       icon: Database,      label: "SQL Studio",     group: "studio" },
  { view: "python",    icon: Terminal,      label: "Python",         group: "studio" },
  { view: "email",     icon: Mail,          label: "Email",          group: "studio" },
  { view: "calendar",  icon: Calendar,      label: "Calendar",       group: "studio" },
  { view: "ml",        icon: Brain,         label: "ML Studio",      group: "ai" },
  { view: "eval",      icon: Activity,      label: "AI Eval",        group: "ai" },
  { view: "report",    icon: FileText,      label: "Reports",        group: "ai" },
];

export default function ChatSidebar() {
  const {
    user, workspaces, activeWorkspace, folders, conversations,
    activeConversation, theme, sidebarOpen,
    setActiveWorkspace, setActiveConversation, setMessages,
    toggleTheme, logout, activeView, setActiveView
  } = useChatStore();

  const [searchQuery, setSearchQuery]             = useState("");
  const [showWorkspaceMenu, setShowWorkspaceMenu] = useState(false);
  const [expandedFolders, setExpandedFolders]     = useState<Record<number, boolean>>({});
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName]   = useState("");
  const [isCreatingFolder, setIsCreatingFolder]   = useState(false);
  const [newFolderName, setNewFolderName]         = useState("");
  // Conversation panel open/close (right panel)
  const [convPanelOpen, setConvPanelOpen]         = useState(true);
  // Tooltip shown on icon hover
  const [hoveredNav, setHoveredNav]               = useState<string | null>(null);

  const filteredConversations = conversations.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const conversationsByFolder: Record<number | "root", typeof conversations> = { root: [] };
  filteredConversations.forEach(c => {
    if (c.folder_id) {
      if (!conversationsByFolder[c.folder_id]) conversationsByFolder[c.folder_id] = [];
      conversationsByFolder[c.folder_id].push(c);
    } else {
      conversationsByFolder.root.push(c);
    }
  });

  const handleNewChat = () => { setActiveConversation(null); setMessages([]); };

  const handleSelectConversation = async (convo: typeof conversations[0]) => {
    setActiveConversation(convo);
    try { await apiService.fetchMessages(convo.id); } catch {}
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;
    try {
      await apiService.createWorkspace(newWorkspaceName);
      setNewWorkspaceName(""); setIsCreatingWorkspace(false);
    } catch {}
  };

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim() || !activeWorkspace) return;
    try {
      await apiService.createFolder(newFolderName, activeWorkspace.id);
      setNewFolderName(""); setIsCreatingFolder(false);
    } catch {}
  };

  const handleDeleteConversation = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!activeWorkspace) return;
    if (confirm("Delete this conversation?")) {
      try {
        await apiService.deleteConversation(id, activeWorkspace.id);
        if (activeConversation?.id === id) handleNewChat();
      } catch {}
    }
  };

  const toggleFolder = (folderId: number) =>
    setExpandedFolders(prev => ({ ...prev, [folderId]: !prev[folderId] }));

  const groupedNav = {
    main:   NAV_ITEMS.filter(n => n.group === "main"),
    studio: NAV_ITEMS.filter(n => n.group === "studio"),
    ai:     NAV_ITEMS.filter(n => n.group === "ai"),
  };

  if (!sidebarOpen) return null;

  return (
    <div className="z-20 flex h-full">

      {/* ═══════════════════════════════════════════════
          LEFT NARROW ICON BAR — Feature Navigation
      ══════════════════════════════════════════════ */}
      <aside className="flex h-full w-[60px] flex-col items-center border-r border-border bg-zinc-950 py-3 gap-1">

        {/* Logo */}
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 shadow-lg shadow-indigo-600/30 mb-2">
          <Cpu className="h-5 w-5 text-white" />
        </div>

        <div className="w-8 border-b border-zinc-800 mb-1" />

        {/* Main group */}
        {groupedNav.main.map(item => (
          <NavIcon key={item.view} item={item} activeView={activeView}
            setActiveView={setActiveView} hovered={hoveredNav}
            setHovered={setHoveredNav} />
        ))}

        <div className="w-8 border-b border-zinc-800 my-1" />

        {/* Studio group */}
        {groupedNav.studio.map(item => (
          <NavIcon key={item.view} item={item} activeView={activeView}
            setActiveView={setActiveView} hovered={hoveredNav}
            setHovered={setHoveredNav} />
        ))}

        <div className="w-8 border-b border-zinc-800 my-1" />

        {/* AI group */}
        {groupedNav.ai.map(item => (
          <NavIcon key={item.view} item={item} activeView={activeView}
            setActiveView={setActiveView} hovered={hoveredNav}
            setHovered={setHoveredNav} />
        ))}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition"
          title={theme === "dark" ? "Light Mode" : "Dark Mode"}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* User avatar */}
        <button
          onClick={logout}
          title="Logout"
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800 text-zinc-300 hover:bg-red-500/20 hover:text-red-400 transition mt-1"
        >
          <User className="h-4 w-4" />
        </button>
      </aside>

      {/* ═══════════════════════════════════════════════
          RIGHT CONVERSATION PANEL — Chat History
          Only shown when activeView === "chat"
      ══════════════════════════════════════════════ */}
      {activeView === "chat" && (
        <aside className={`relative flex h-full flex-col border-r border-border bg-sidebar-bg text-foreground transition-all duration-200 ${convPanelOpen ? "w-[240px]" : "w-0 overflow-hidden"}`}>

          {/* Panel toggle button */}
          <button
            onClick={() => setConvPanelOpen(!convPanelOpen)}
            className="absolute -right-3 top-6 z-30 flex h-6 w-6 items-center justify-center rounded-full border border-border bg-card text-zinc-400 hover:text-white shadow"
          >
            {convPanelOpen ? <ChevronLeft className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>

          {convPanelOpen && (
            <>
              {/* Workspace Selector */}
              <div className="relative border-b border-border p-3">
                <button
                  onClick={() => setShowWorkspaceMenu(!showWorkspaceMenu)}
                  className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-xs font-semibold shadow-sm transition hover:bg-zinc-900"
                >
                  <span className="truncate">{activeWorkspace?.name || "Select Workspace"}</span>
                  <ChevronDown className="h-3.5 w-3.5 text-zinc-500 shrink-0 ml-1" />
                </button>

                {showWorkspaceMenu && (
                  <div className="absolute top-[calc(100%-6px)] left-3 right-3 z-30 rounded-lg border border-border bg-card p-2 shadow-lg">
                    <div className="max-h-[140px] overflow-y-auto space-y-1">
                      {workspaces.map(w => (
                        <button key={w.id}
                          onClick={() => { setActiveWorkspace(w); setShowWorkspaceMenu(false); }}
                          className={`w-full rounded-md px-3 py-1.5 text-left text-xs font-medium transition ${
                            activeWorkspace?.id === w.id
                              ? "bg-sidebar-active text-indigo-400 font-semibold"
                              : "hover:bg-zinc-900 text-zinc-400"
                          }`}
                        >{w.name}</button>
                      ))}
                    </div>
                    <div className="border-t border-border mt-2 pt-2">
                      {isCreatingWorkspace ? (
                        <form onSubmit={handleCreateWorkspace} className="flex gap-1">
                          <input type="text" value={newWorkspaceName}
                            onChange={e => setNewWorkspaceName(e.target.value)}
                            placeholder="Workspace name"
                            className="w-full rounded border border-border bg-background px-2 py-1 text-xs outline-none focus:border-indigo-500"
                          />
                          <button type="submit" className="rounded bg-indigo-600 px-2 py-1 text-xs font-bold text-white">+</button>
                        </form>
                      ) : (
                        <button onClick={() => setIsCreatingWorkspace(true)}
                          className="flex w-full items-center gap-2 px-2 py-1 text-xs font-semibold text-indigo-400">
                          <Plus className="h-3 w-3" /> New Workspace
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* New Chat Button + Search */}
              <div className="space-y-2 p-3">
                <button
                  onClick={handleNewChat}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-primary-hover active:scale-[0.98]"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>New Chat</span>
                </button>

                <div className="relative">
                  <Search className="absolute top-2.5 left-2.5 h-3.5 w-3.5 text-zinc-400" />
                  <input type="text" value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search..."
                    className="w-full rounded-lg border border-border bg-card pl-8 pr-3 py-1.5 text-xs outline-none transition focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Conversations List */}
              <div className="flex-1 overflow-y-auto px-2 space-y-3 pb-2">

                {/* Folders */}
                {folders.length > 0 && (
                  <div className="space-y-0.5">
                    <div className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 px-2 py-1">Folders</div>
                    {folders.map(folder => {
                      const isExpanded = expandedFolders[folder.id];
                      const folderConvos = conversationsByFolder[folder.id] || [];
                      return (
                        <div key={folder.id}>
                          <button onClick={() => toggleFolder(folder.id)}
                            className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-[11px] text-zinc-400 hover:bg-sidebar-active hover:text-foreground"
                          >
                            <div className="flex items-center gap-1.5">
                              {isExpanded ? <FolderOpen className="h-3.5 w-3.5" /> : <Folder className="h-3.5 w-3.5" />}
                              <span className="truncate font-medium">{folder.name}</span>
                            </div>
                            {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                          </button>
                          {isExpanded && (
                            <div className="border-l border-border ml-4 pl-2 space-y-0.5">
                              {folderConvos.length === 0
                                ? <div className="py-1 px-2 text-[10px] text-zinc-500">Empty</div>
                                : folderConvos.map(convo => (
                                  <ConvoItem key={convo.id} convo={convo}
                                    active={activeConversation?.id === convo.id}
                                    onSelect={() => handleSelectConversation(convo)}
                                    onDelete={e => handleDeleteConversation(convo.id, e)}
                                  />
                                ))
                              }
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Root Conversations */}
                <div className="space-y-0.5">
                  <div className="flex items-center justify-between px-2 py-1">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-500">Conversations</span>
                    <button
                      onClick={() => setIsCreatingFolder(!isCreatingFolder)}
                      className="text-[9px] text-zinc-500 hover:text-indigo-400 font-semibold"
                      title="Create Folder"
                    >
                      + Folder
                    </button>
                  </div>

                  {isCreatingFolder && (
                    <form onSubmit={handleCreateFolder} className="flex gap-1 px-2 mb-1">
                      <input type="text" value={newFolderName}
                        onChange={e => setNewFolderName(e.target.value)}
                        placeholder="Folder name"
                        className="w-full rounded border border-border bg-background px-2 py-1 text-[10px] outline-none focus:border-indigo-500"
                      />
                      <button type="submit" className="rounded bg-indigo-600 px-2 py-1 text-[10px] font-bold text-white">+</button>
                    </form>
                  )}

                  {conversationsByFolder.root.length > 0
                    ? conversationsByFolder.root.map(convo => (
                      <ConvoItem key={convo.id} convo={convo}
                        active={activeConversation?.id === convo.id}
                        onSelect={() => handleSelectConversation(convo)}
                        onDelete={e => handleDeleteConversation(convo.id, e)}
                      />
                    ))
                    : <div className="py-2 px-2 text-[10px] text-zinc-500 italic">No chats yet</div>
                  }
                </div>
              </div>

              {/* User footer */}
              <div className="border-t border-border p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 truncate">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-zinc-300">
                      <User className="h-3.5 w-3.5" />
                    </div>
                    <div className="truncate">
                      <div className="truncate text-[11px] font-semibold">{user?.full_name || "User"}</div>
                      <div className="truncate text-[9px] text-zinc-500">{user?.email}</div>
                    </div>
                  </div>
                  <button onClick={logout} className="hover:text-red-500 transition shrink-0" title="Logout">
                    <LogOut className="h-3.5 w-3.5 text-zinc-500" />
                  </button>
                </div>
              </div>
            </>
          )}
        </aside>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────

function NavIcon({ item, activeView, setActiveView, hovered, setHovered }: any) {
  const Icon = item.icon;
  const isActive = activeView === item.view;
  return (
    <div className="relative" onMouseEnter={() => setHovered(item.view)} onMouseLeave={() => setHovered(null)}>
      <button
        onClick={() => setActiveView(item.view)}
        className={`relative flex h-9 w-9 items-center justify-center rounded-lg transition-all ${
          isActive
            ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30"
            : "text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200"
        }`}
      >
        <Icon className="h-4 w-4" />
        {item.badge && (
          <span className="absolute -top-1 -right-1 rounded-full bg-indigo-500 px-1 text-[6px] font-black text-white">
            {item.badge}
          </span>
        )}
      </button>
      {/* Tooltip */}
      {hovered === item.view && (
        <div className="absolute left-12 top-1/2 -translate-y-1/2 z-50 whitespace-nowrap rounded-md bg-zinc-800 border border-zinc-700 px-2.5 py-1 text-xs font-medium text-zinc-200 shadow-lg pointer-events-none">
          {item.label}
          <div className="absolute left-[-4px] top-1/2 -translate-y-1/2 border-4 border-transparent border-r-zinc-800" />
        </div>
      )}
    </div>
  );
}

function ConvoItem({ convo, active, onSelect, onDelete }: any) {
  const { activeWorkspace } = useChatStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(convo.title);

  const handleRename = async () => {
    if (!editTitle.trim() || editTitle === convo.title) {
      setIsEditing(false);
      return;
    }
    try {
      if (activeWorkspace) {
        await apiService.updateConversation(convo.id, editTitle, activeWorkspace.id);
      }
    } catch (err) {
      console.error("Failed to rename conversation:", err);
    } finally {
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleRename();
    } else if (e.key === "Escape") {
      setEditTitle(convo.title);
      setIsEditing(false);
    }
  };

  return (
    <div
      onClick={!isEditing ? onSelect : undefined}
      onDoubleClick={(e) => {
        if (!isEditing) {
          e.stopPropagation();
          setIsEditing(true);
        }
      }}
      className={`group flex items-center justify-between rounded-lg px-2.5 py-1.5 text-[11px] cursor-pointer transition ${
        active
          ? "bg-sidebar-active text-indigo-400 font-semibold"
          : "text-zinc-400 hover:bg-sidebar-active hover:text-foreground"
      }`}
    >
      {isEditing ? (
        <input
          type="text"
          value={editTitle}
          onChange={e => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          autoFocus
          className="w-full bg-zinc-950 border border-indigo-500 rounded px-1.5 py-0.5 text-[11px] text-foreground outline-none"
          onClick={e => e.stopPropagation()}
        />
      ) : (
        <>
          <div className="flex items-center gap-1.5 truncate">
            <MessageSquare className="h-3 w-3 shrink-0" />
            <span className="truncate">{convo.title}</span>
          </div>
          <div className="hidden group-hover:flex items-center gap-1.5 shrink-0">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
              }}
              className="hover:text-indigo-400"
              title="Rename Chat"
            >
              <Edit2 className="h-3 w-3" />
            </button>
            <button
              onClick={onDelete}
              className="hover:text-red-500"
              title="Delete Chat"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

