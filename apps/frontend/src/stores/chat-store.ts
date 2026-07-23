import { create } from "zustand";
import { User, Workspace, Folder, Conversation, Message, KnowledgeBase, KnowledgeDocument } from "../types/chat";

interface ChatState {
  // Authentication
  user: User | null;
  token: string | null;
  
  // Workspaces, Folders & History
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  folders: Folder[];
  conversations: Conversation[];
  activeConversation: Conversation | null;
  messages: Message[];
  
  // UI States
  isStreaming: boolean;
  theme: "light" | "dark";
  sidebarOpen: boolean;
  activeView: "chat" | "knowledge" | "analytics" | "ml" | "report" | "agents" | "sql" | "python" | "email" | "calendar" | "eval" | "admin";





  
  // Knowledge Bases
  knowledgeBases: KnowledgeBase[];
  activeKnowledgeBase: KnowledgeBase | null;
  documents: KnowledgeDocument[];
  
  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  logout: () => void;
  setWorkspaces: (workspaces: Workspace[]) => void;
  setActiveWorkspace: (workspace: Workspace | null) => void;
  setFolders: (folders: Folder[]) => void;
  setConversations: (conversations: Conversation[]) => void;
  setActiveConversation: (convo: Conversation | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateLastMessageContent: (content: string) => void;
  updateLastMessageSources: (sources: any[]) => void;
  setIsStreaming: (streaming: boolean) => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setActiveView: (view: "chat" | "knowledge" | "analytics" | "ml" | "report" | "agents" | "sql" | "python" | "email" | "calendar" | "eval" | "admin") => void;





  setKnowledgeBases: (bases: KnowledgeBase[]) => void;
  setActiveKnowledgeBase: (base: KnowledgeBase | null) => void;
  setDocuments: (docs: KnowledgeDocument[]) => void;
  selectedChatKb: KnowledgeBase | null;
  groundingEnabled: boolean;
  setSelectedChatKb: (kb: KnowledgeBase | null) => void;
  setGroundingEnabled: (enabled: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  // Initial state values
  user: null,
  token: null,
  workspaces: [],
  activeWorkspace: null,
  folders: [],
  conversations: [],
  activeConversation: null,
  messages: [],
  isStreaming: false,
  theme: "dark",
  sidebarOpen: true,
  activeView: "chat",
  knowledgeBases: [],
  activeKnowledgeBase: null,
  documents: [],
  selectedChatKb: null,
  groundingEnabled: true,

  // Setters and action handlers
  setUser: (user) => set({ user }),
  
  setToken: (token) => {
    if (token) {
      localStorage.setItem("nexora_token", token);
    } else {
      localStorage.removeItem("nexora_token");
    }
    set({ token });
  },

  logout: () => {
    localStorage.removeItem("nexora_token");
    set({
      user: null,
      token: null,
      workspaces: [],
      activeWorkspace: null,
      folders: [],
      conversations: [],
      activeConversation: null,
      messages: [],
      isStreaming: false,
      activeView: "chat",
      knowledgeBases: [],
      activeKnowledgeBase: null,
      documents: []
    });
  },

  setWorkspaces: (workspaces) => {
    set((state) => {
      const active = state.activeWorkspace 
        ? workspaces.find((w) => w.id === state.activeWorkspace?.id) || workspaces[0] || null
        : workspaces[0] || null;
      return { workspaces, activeWorkspace: active };
    });
  },

  setActiveWorkspace: (activeWorkspace) => set({ activeWorkspace, activeConversation: null, messages: [] }),

  setFolders: (folders) => set({ folders }),

  setConversations: (conversations) => set({ conversations }),

  setActiveConversation: (activeConversation) => set({ activeConversation }),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  updateLastMessageContent: (content) => set((state) => {
    const newMessages = [...state.messages];
    if (newMessages.length > 0) {
      const lastIndex = newMessages.length - 1;
      newMessages[lastIndex] = {
        ...newMessages[lastIndex],
        content: content
      };
    }
    return { messages: newMessages };
  }),

  updateLastMessageSources: (sources) => set((state) => {
    const newMessages = [...state.messages];
    if (newMessages.length > 0) {
      const lastIndex = newMessages.length - 1;
      newMessages[lastIndex] = {
        ...newMessages[lastIndex],
        sources: sources
      };
    }
    return { messages: newMessages };
  }),

  setIsStreaming: (isStreaming) => set({ isStreaming }),

  setTheme: (theme) => {
    if (typeof window !== "undefined") {
      const root = window.document.documentElement;
      if (theme === "dark") {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    }
    set({ theme });
  },

  toggleTheme: () => set((state) => {
    const nextTheme = state.theme === "dark" ? "light" : "dark";
    if (typeof window !== "undefined") {
      const root = window.document.documentElement;
      if (nextTheme === "dark") {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    }
    return { theme: nextTheme };
  }),

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setActiveView: (activeView) => set({ activeView }),
  
  setKnowledgeBases: (knowledgeBases) => set({ knowledgeBases }),
  
  setActiveKnowledgeBase: (activeKnowledgeBase) => set({ activeKnowledgeBase }),
  
  setDocuments: (documents) => set({ documents }),
  
  setSelectedChatKb: (selectedChatKb) => set({ selectedChatKb }),
  
  setGroundingEnabled: (groundingEnabled) => set({ groundingEnabled }),
}));
