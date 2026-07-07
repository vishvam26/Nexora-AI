import axios from "axios";
import { useChatStore } from "../stores/chat-store";
import { User, Workspace, Folder, Conversation, Message, KnowledgeBase, KnowledgeDocument, SemanticChunk } from "../types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://liking-follow-groggy.ngrok-free.dev";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "69420",
  },
});

// Attach Authorization header if token exists in Zustand store
apiClient.interceptors.request.use((config) => {
  const token = useChatStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle unauthorized responses (auto-logout)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useChatStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Authentication
  async register(full_name: string, email: string, password: string): Promise<void> {
    await apiClient.post("/auth/register", { full_name, email, password });
  },

  async login(usernameEmail: string, password: string): Promise<string> {
    const formData = new URLSearchParams();
    formData.append("username", usernameEmail);
    formData.append("password", password);

    const response = await apiClient.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    const token = response.data.access_token;
    useChatStore.getState().setToken(token);
    return token;
  },

  async fetchCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/users/me");
    useChatStore.getState().setUser(response.data);
    return response.data;
  },

  // Workspaces
  async fetchWorkspaces(): Promise<Workspace[]> {
    const response = await apiClient.get<{ workspaces: Workspace[] }>("/workspaces");
    const workspaces = response.data.workspaces || [];
    useChatStore.getState().setWorkspaces(workspaces);
    return workspaces;
  },

  async createWorkspace(name: string): Promise<Workspace> {
    const response = await apiClient.post<Workspace>("/workspaces", { name });
    await this.fetchWorkspaces();
    return response.data;
  },

  // Folders
  async fetchFolders(workspaceId: number): Promise<Folder[]> {
    const response = await apiClient.get<{ folders: Folder[] }>(`/folders?workspace_id=${workspaceId}`);
    const folders = response.data.folders || [];
    useChatStore.getState().setFolders(folders);
    return folders;
  },

  async createFolder(name: string, workspaceId: number): Promise<Folder> {
    const response = await apiClient.post<Folder>("/folders", { name, workspace_id: workspaceId });
    await this.fetchFolders(workspaceId);
    return response.data;
  },

  // Conversations
  async fetchConversations(workspaceId: number): Promise<Conversation[]> {
    const response = await apiClient.get<{ conversations: Conversation[] }>(
      `/conversations?workspace_id=${workspaceId}`
    );
    const conversations = response.data.conversations || [];
    useChatStore.getState().setConversations(conversations);
    return conversations;
  },

  async createConversation(title: string, workspaceId: number, folderId: number | null = null): Promise<Conversation> {
    const response = await apiClient.post<Conversation>("/conversations", {
      title,
      workspace_id: workspaceId,
      folder_id: folderId,
    });
    await this.fetchConversations(workspaceId);
    return response.data;
  },

  async deleteConversation(id: number, workspaceId: number): Promise<void> {
    await apiClient.delete(`/conversations/${id}`);
    await this.fetchConversations(workspaceId);
  },

  async updateConversation(id: number, title: string, workspaceId: number): Promise<Conversation> {
    const response = await apiClient.patch<Conversation>(`/conversations/${id}`, { title });
    await this.fetchConversations(workspaceId);
    return response.data;
  },


  // Messages
  async fetchMessages(conversationId: number): Promise<Message[]> {
    const response = await apiClient.get<{ messages: Message[] }>(`/messages/${conversationId}`);
    const messages = response.data.messages || [];
    useChatStore.getState().setMessages(messages);
    return messages;
  },

  // Chat Streaming
  async streamChat(
    conversationId: number,
    messageText: string,
    workspaceId: number,
    knowledgeBaseId: number | null,
    grounded: boolean,
    onToken: (token: string) => void,
    onSources: (sources: any[]) => void,
    onError: (err: string) => void
  ): Promise<void> {
    const store = useChatStore.getState();
    const token = store.token;

    if (!token) {
      onError("Authentication required");
      return;
    }

    store.setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: messageText,
          workspace_id: workspaceId,
          knowledge_base_id: knowledgeBaseId,
          grounded: grounded
        }),
      });

      if (!response.ok) {
        throw new Error(`Chat stream request failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Response body reader unavailable");
      }

      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith("data: ")) {
            const jsonStr = trimmed.slice(6);
            try {
              const data = JSON.parse(jsonStr);
              if (data.error) {
                onError(data.error);
                return;
              }
              if (data.sources) {
                onSources(data.sources);
              }
              if (data.content) {
                onToken(data.content);
              }
            } catch (e) {
              // Ignore partial JSON parsing errors during transfer
            }
          }
        }
      }
    } catch (err: any) {
      logger.error("Error during streaming execution:", err);
      onError(err.message || "Network request failed");
    } finally {
      store.setIsStreaming(false);
      // Reload conversation history after completion to sync message IDs and timestamps
      await this.fetchMessages(conversationId);
    }
  },

  // Knowledge Bases & RAG Document Upload
  async fetchKnowledgeBases(workspaceId: number): Promise<KnowledgeBase[]> {
    const response = await apiClient.get<KnowledgeBaseListResponse>(`/knowledge/bases?workspace_id=${workspaceId}`);
    const bases = response.data.knowledge_bases || [];
    useChatStore.getState().setKnowledgeBases(bases);
    return bases;
  },

  async createKnowledgeBase(workspaceId: number, title: string, description: string): Promise<KnowledgeBase> {
    // Backend takes workspace_id query param and KnowledgeBaseCreate JSON schema
    const response = await apiClient.post<KnowledgeBase>(`/knowledge/bases?workspace_id=${workspaceId}`, {
      title,
      description,
      icon: "📚",
      color: "#10B981",
      visibility: "private"
    });
    // Refresh the list of knowledge bases
    await this.fetchKnowledgeBases(workspaceId);
    return response.data;
  },

  async deleteKnowledgeBase(workspaceId: number, kbId: number): Promise<void> {
    await apiClient.delete(`/knowledge/bases/${kbId}`);
    await this.fetchKnowledgeBases(workspaceId);
  },

  async fetchDocuments(kbId: number): Promise<KnowledgeDocument[]> {
    const response = await apiClient.get<KnowledgeDocumentListResponse>(`/knowledge/documents?kb_id=${kbId}`);
    const docs = response.data.documents || [];
    useChatStore.getState().setDocuments(docs);
    return docs;
  },

  async deleteDocument(kbId: number, docId: number): Promise<void> {
    await apiClient.delete(`/knowledge/documents/${docId}`);
    await this.fetchDocuments(kbId);
  },

  async uploadDocument(
    kbId: number,
    file: File,
    onProgress: (progress: number) => void
  ): Promise<KnowledgeDocument> {
    const formData = new FormData();
    formData.append("kb_id", kbId.toString());
    formData.append("file", file);

    const response = await apiClient.post<KnowledgeDocument>("/knowledge/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        const total = progressEvent.total || file.size;
        const current = progressEvent.loaded;
        const percent = Math.round((current * 100) / total);
        onProgress(percent);
      },
    });
    // Refresh documents list
    await this.fetchDocuments(kbId);
    return response.data;
  },

  async retrieveSemanticChunks(
    workspaceId: number,
    kbId: number,
    query: string,
    topK: number = 5,
    offset: number = 0,
    fileType: string | null = null,
    startDate: string | null = null,
    endDate: string | null = null,
  ): Promise<RetrievalResponse> {
    const response = await apiClient.post<RetrievalResponse>(
      `/knowledge/retrieve?workspace_id=${workspaceId}`,
      {
        query,
        knowledge_base_id: kbId,
        top_k: topK,
        offset: offset,
        file_type: fileType || null,
        start_date: startDate || null,
        end_date: endDate || null,
      }
    );
    return response.data;
  },
};

// Response models from backend APIs
interface KnowledgeBaseListResponse {
  knowledge_bases: KnowledgeBase[];
  total: number;
}

interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
}

export interface RetrievalResponse {
  query: string;
  results: SemanticChunk[];
  total: number;
}

const logger = {
  error: (msg: string, err: any) => {
    console.error(`[API ERROR] ${msg}`, err);
  },
};
