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
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
    !c.title.toLowerCase().startsWith("system ")
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
          LEFT NARROW ICON BAR — Feature Navigation (Nexora Glass Design)
      ══════════════════════════════════════════════ */}
      <aside className="relative flex h-full w-[60px] flex-col items-center border-r py-3 gap-1 overflow-hidden" style={{ borderColor: "rgba(255,255,255,0.05)", background: "rgba(9,9,11,0.75)", backdropFilter: "blur(20px)" }}>
        {/* Left edge glow accent */}
        <div className="absolute left-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-indigo-600/30 to-transparent" />

        {/* Nexora Bird Logo */}
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 shadow-lg shadow-indigo-600/30 mb-2 shrink-0">
          <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" className="h-4.5 w-4.5">
            <path d="M12 2L2 22l10-6 10 6L12 2z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        <div className="w-7 border-b border-zinc-800/60 mb-1" />

        {/* Main group */}
        {groupedNav.main.map(item => (
          <NavIcon key={item.view} item={item} activeView={activeView}
            setActiveView={setActiveView} hovered={hoveredNav}
            setHovered={setHoveredNav} />
        ))}

        <div className="w-7 border-b border-zinc-800/60 my-1" />

        {/* Studio group */}
        {groupedNav.studio.map(item => (
          <NavIcon key={item.view} item={item} activeView={activeView}
            setActiveView={setActiveView} hovered={hoveredNav}
            setHovered={setHoveredNav} />
        ))}

        <div className="w-7 border-b border-zinc-800/60 my-1" />

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
          className="flex h-9 w-9 items-center justify-center rounded-lg text-zinc-600 hover:text-indigo-400 hover:bg-indigo-500/10 transition-all mb-1"
          title={theme === "dark" ? "Light Mode" : "Dark Mode"}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* User avatar / Logout */}
        <button
          onClick={logout}
          title={`Logout (${user?.email || ''})`}
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-800/60 border border-zinc-700/40 text-zinc-400 hover:bg-red-500/15 hover:text-red-400 hover:border-red-500/20 transition-all"
        >
          <User className="h-4 w-4" />
        </button>
      </aside>

      {/* ═══════════════════════════════════════════════
          RIGHT CONVERSATION PANEL — Chat History
          Only shown when activeView === "chat"
      ══════════════════════════════════════════════ */}
      {activeView === "chat" && (
        <aside className={`relative flex h-full flex-col text-foreground transition-all duration-200 ${convPanelOpen ? "w-[240px]" : "w-0 overflow-hidden"}`} style={{ borderRight: "1px solid rgba(255,255,255,0.05)", background: "rgba(9,9,11,0.65)", backdropFilter: "blur(20px)" }}>

          {/* Panel toggle button */}
          <button
            onClick={() => setConvPanelOpen(!convPanelOpen)}
            className="absolute -right-3 top-6 z-30 flex h-6 w-6 items-center justify-center rounded-full text-zinc-500 hover:text-indigo-400 shadow-lg transition-all"
            style={{ background: "rgba(9,9,11,0.9)", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            {convPanelOpen ? <ChevronLeft className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          </button>

          {convPanelOpen && (
            <>
              {/* Workspace Selector */}
              <div className="relative border-b border-zinc-900 p-3">
                <button
                  onClick={() => setShowWorkspaceMenu(!showWorkspaceMenu)}
                  className="flex w-full items-center justify-between rounded-xl border border-zinc-800 bg-zinc-950/60 px-3.5 py-2.5 text-xs font-semibold shadow-sm transition hover:bg-zinc-900"
                >
                  <span className="truncate">{activeWorkspace?.name || "Select Workspace"}</span>
                  <ChevronDown className="h-3.5 w-3.5 text-zinc-500 shrink-0 ml-1" />
                </button>

                {showWorkspaceMenu && (
                  <div className="absolute top-[calc(100%-6px)] left-3 right-3 z-30 rounded-xl border border-zinc-800 bg-zinc-950 p-2 shadow-2xl animate-fade-in-up">
                    <div className="max-h-[140px] overflow-y-auto space-y-1">
                      {workspaces.map(w => (
                        <button key={w.id}
                          onClick={() => { setActiveWorkspace(w); setShowWorkspaceMenu(false); }}
                          className={`w-full rounded-lg px-3 py-2 text-left text-xs font-semibold transition ${
                            activeWorkspace?.id === w.id
                              ? "bg-indigo-500/10 text-indigo-400 font-semibold"
                              : "hover:bg-zinc-900 text-zinc-400"
                          }`}
                        >{w.name}</button>
                      ))}
                    </div>
                    <div className="border-t border-zinc-850 mt-2 pt-2">
                      {isCreatingWorkspace ? (
                        <form onSubmit={handleCreateWorkspace} className="flex gap-1.5">
                          <input type="text" value={newWorkspaceName}
                            onChange={e => setNewWorkspaceName(e.target.value)}
                            placeholder="Workspace name"
                            className="w-full rounded-lg border border-zinc-800 bg-[#09090b] px-2.5 py-1.5 text-xs text-white placeholder-zinc-700 outline-none focus:border-indigo-500/40"
                          />
                          <button type="submit" className="rounded-lg bg-indigo-650 px-3 py-1.5 text-xs font-bold text-white">+</button>
                        </form>
                      ) : (
                        <button onClick={() => setIsCreatingWorkspace(true)}
                          className="flex w-full items-center gap-2 px-2 py-1.5 text-xs font-semibold text-indigo-450 hover:text-indigo-400">
                          <Plus className="h-3 w-3" /> New Workspace
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* New Chat Button + Search */}
              <div className="space-y-2.5 p-3 border-b border-zinc-900">
                <button
                  onClick={handleNewChat}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 py-2.5 text-xs font-bold tracking-wider text-white shadow-lg shadow-indigo-900/30 transition hover:from-indigo-550 hover:to-indigo-650 active:scale-[0.98]"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>NEW CHAT</span>
                </button>

                <div className="relative">
                  <Search className="absolute top-3 left-3 h-3.5 w-3.5 text-zinc-550" />
                  <input type="text" value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search sessions..."
                    className="w-full rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-650 outline-none transition"
                    style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}
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
                            <div className="border-l border-zinc-800 ml-4 pl-2 space-y-0.5">
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
                <div className="space-y-1.5 p-3">
                  <div className="flex items-center justify-between px-1 py-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-550">Conversations</span>
                    <button
                      onClick={() => setIsCreatingFolder(!isCreatingFolder)}
                      className="text-[10px] text-indigo-450 hover:text-indigo-400 font-bold tracking-wide uppercase"
                      title="Create Folder"
                    >
                      + Folder
                    </button>
                  </div>

                  {isCreatingFolder && (
                    <form onSubmit={handleCreateFolder} className="flex gap-1.5 px-1 mb-2 animate-fade-in-up">
                      <input type="text" value={newFolderName}
                        onChange={e => setNewFolderName(e.target.value)}
                        placeholder="Folder name"
                        className="w-full rounded-lg border border-zinc-800 bg-[#09090b] px-2.5 py-1 text-[10px] text-white placeholder-zinc-700 outline-none focus:border-indigo-500/40"
                      />
                      <button type="submit" className="rounded-lg bg-indigo-650 px-2 py-1 text-[10px] font-bold text-white">+</button>
                    </form>
                  )}

                  <div className="space-y-1">
                    {conversationsByFolder.root.length > 0
                      ? conversationsByFolder.root.map(convo => (
                        <ConvoItem key={convo.id} convo={convo}
                          active={activeConversation?.id === convo.id}
                          onSelect={() => handleSelectConversation(convo)}
                          onDelete={e => handleDeleteConversation(convo.id, e)}
                        />
                      ))
                      : <div className="py-2.5 px-3 text-[10px] text-zinc-600 italic">No chats in workspace yet</div>
                    }
                  </div>
                </div>
              </div>

              {/* User footer */}
              <div className="border-t border-zinc-900 bg-zinc-950/20 p-3.5 z-10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5 truncate">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-750 text-white font-bold text-[10px]">
                      {user?.full_name ? user.full_name[0].toUpperCase() : "U"}
                    </div>
                    <div className="truncate text-left">
                      <div className="truncate text-[11px] font-semibold text-white">{user?.full_name || "User"}</div>
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
    <div className="relative group/nav" onMouseEnter={() => setHovered(item.view)} onMouseLeave={() => setHovered(null)}>
      {/* Glowing vertical line indicator */}
      <div className={`absolute left-[-12px] top-1/2 -translate-y-1/2 w-1.5 h-6 rounded-r bg-gradient-to-b from-indigo-400 to-violet-500 transition-all duration-300 ${
        isActive ? "opacity-100 scale-y-100" : "opacity-0 scale-y-50 group-hover/nav:opacity-40 group-hover/nav:scale-y-75"
      }`} style={{ boxShadow: "0 0 10px rgba(99, 102, 241, 0.8)" }} />

      <button
        onClick={() => setActiveView(item.view)}
        className={`relative flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-300 ${
          isActive
            ? "bg-gradient-to-br from-indigo-550 to-violet-750 text-white shadow-lg shadow-indigo-600/30 border border-indigo-500/30"
            : "text-zinc-500 hover:bg-indigo-500/10 hover:text-indigo-400 border border-transparent"
        }`}
      >
        <Icon className="h-4.5 w-4.5" />
        {item.badge && (
          <span className="absolute -top-1 -right-1 rounded-full bg-cyan-500 px-1 py-0.5 text-[5px] font-black text-[#09090b] tracking-wider uppercase animate-pulse">
            {item.badge}
          </span>
        )}
      </button>
      {/* Tooltip */}
      {hovered === item.view && (
        <div className="absolute left-12 top-1/2 -translate-y-1/2 z-50 whitespace-nowrap rounded-lg bg-zinc-950 border border-zinc-800 px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase text-zinc-350 shadow-2xl animate-fade-in">
          {item.label}
          <div className="absolute left-[-4px] top-1/2 -translate-y-1/2 border-4 border-transparent border-r-zinc-950" />
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
      className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs cursor-pointer transition-all border ${
        active
          ? "border-indigo-500/25 bg-indigo-500/5 text-indigo-400 font-semibold"
          : "border-transparent text-zinc-450 hover:bg-zinc-900/40 hover:text-zinc-200"
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
          className="w-full bg-zinc-950 border border-indigo-500/40 rounded-lg px-2 py-1 text-xs text-foreground outline-none focus:border-indigo-550"
          onClick={e => e.stopPropagation()}
        />
      ) : (
        <>
          <div className="flex items-center gap-2 truncate">
            <MessageSquare className={`h-3.5 w-3.5 shrink-0 ${active ? "text-indigo-400" : "text-zinc-550 group-hover:text-zinc-400"}`} />
            <span className="truncate">{convo.title}</span>
          </div>
          <div className="hidden group-hover:flex items-center gap-1.5 shrink-0 ml-1.5">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
              }}
              className="hover:text-indigo-400 p-0.5"
              title="Rename Chat"
            >
              <Edit2 className="h-3 w-3 text-zinc-500 hover:text-indigo-400" />
            </button>
            <button
              onClick={onDelete}
              className="hover:text-red-500 p-0.5"
              title="Delete Chat"
            >
              <Trash2 className="h-3 w-3 text-zinc-500 hover:text-red-400" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}


