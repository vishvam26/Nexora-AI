export interface User {
  id: number;
  full_name: string;
  email: string;
}

export interface Workspace {
  id: number;
  name: string;
  owner_id: number;
  disable_exports?: boolean;
}

export interface Folder {
  id: number;
  workspace_id: number;
  name: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  workspace_id: number;
  user_id: number;
  folder_id: number | null;
  title: string;
  summary: string | null;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  updated_at?: string;
  is_deleted?: boolean;
}

export interface ChatFeedback {
  id: number;
  message_id: number;
  thumbs_up: boolean;
  thumbs_down: boolean;
  feedback: string | null;
}

export interface KnowledgeBase {
  id: number;
  uuid: string;
  workspace_id: number;
  title: string;
  description: string | null;
  icon: string;
  color: string;
  visibility: string;
  created_at: string;
}

export interface KnowledgeDocument {
  id: number;
  knowledge_base_id: number;
  filename: string;
  mime_type: string;
  size: number;
  status: "Uploading" | "Processing" | "Completed" | "Failed";
  storage_path: string;
  uploaded_by: number;
  created_at: string;
}
