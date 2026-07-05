"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "../../stores/chat-store";
import { apiService } from "../../services/api-service";
import ChatSidebar from "../../components/chat-sidebar";
import ChatArea from "../../components/chat-area";
import KnowledgeArea from "../../components/knowledge-area";
import AnalyticsArea from "../../components/analytics-area";
import MLArea from "../../components/ml-area";
import ReportArea from "../../components/report-area";
import AgentStudio from "../../components/agent-studio";
import SQLStudio from "../../components/sql-studio";
import PythonStudio from "../../components/python-studio";
import EmailStudio from "../../components/email-studio";
import CalendarStudio from "../../components/calendar-studio";
import EvalDashboard from "../../components/eval-dashboard";
import { Loader2 } from "lucide-react";






export default function ChatPage() {
  const router = useRouter();
  const { token, activeWorkspace, logout, setToken, activeView } = useChatStore();
  const [mounted, setMounted] = useState(false);
  const [initLoading, setInitLoading] = useState(true);

  // Initialize token from localStorage on mount
  useEffect(() => {
    const localToken = localStorage.getItem("nexora_token");
    if (localToken) {
      setToken(localToken);
    }
    setMounted(true);
  }, [setToken]);

  // Authentication check
  useEffect(() => {
    if (mounted && !token) {
      router.push("/");
    }
  }, [token, mounted, router]);

  // Initial core workspace data fetching
  useEffect(() => {
    if (!token) return;

    const initializeWorkspaceData = async () => {
      try {
        setInitLoading(true);
        // Fetch current user details
        await apiService.fetchCurrentUser();
        // Fetch all workspaces belonging to the user
        const workspaces = await apiService.fetchWorkspaces();
        
        // If workspaces are available, let the activeWorkspace trigger subsequent loads
        if (workspaces.length === 0) {
          // If no workspaces exist, create a default workspace automatically
          await apiService.createWorkspace("My AI Workspace");
        }
      } catch (err) {
        console.error("Initialization failed:", err);
        // In case of token expiration or network failure, trigger logout
        logout();
        router.push("/");
      } finally {
        setInitLoading(false);
      }
    };

    initializeWorkspaceData();
  }, [token, logout, router]);

  // Handle active workspace changes to fetch child folders and conversations
  useEffect(() => {
    if (!token || !activeWorkspace) return;

    const fetchWorkspaceAssets = async () => {
      try {
        await Promise.all([
          apiService.fetchFolders(activeWorkspace.id),
          apiService.fetchConversations(activeWorkspace.id)
        ]);
      } catch (err) {
        console.error("Error loading workspace assets:", err);
      }
    };

    fetchWorkspaceAssets();
  }, [token, activeWorkspace]);

  if (!mounted || !token) {
    return null; // Don't render layout if not authorized or not mounted yet
  }

  if (initLoading) {
    return (
      <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#09090b] text-[#f4f4f5]">
        <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
        <p className="mt-4 text-sm text-zinc-400 font-medium tracking-wide">
          Syncing workspace nodes...
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* 1. Left Sidebar - Navigation & History */}
      <ChatSidebar />

      {/* 2. Main Workspace Panel */}
      {activeView === "chat" ? (
        <ChatArea />
      ) : activeView === "knowledge" ? (
        <KnowledgeArea />
      ) : activeView === "analytics" ? (
        <AnalyticsArea />
      ) : activeView === "report" ? (
        <ReportArea />
      ) : activeView === "agents" ? (
        <AgentStudio />
      ) : activeView === "sql" ? (
        <SQLStudio />
      ) : activeView === "python" ? (
        <PythonStudio />
      ) : activeView === "email" ? (
        <EmailStudio />
      ) : activeView === "calendar" ? (
        <CalendarStudio />
      ) : activeView === "eval" ? (
        <EvalDashboard />
      ) : (
        <MLArea />
      )}
    </div>





  );
}
