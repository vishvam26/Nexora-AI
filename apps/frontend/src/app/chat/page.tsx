"use client";

import { useEffect, useRef, useState } from "react";
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
import NexoraLoader from "../../components/nexora-loader";
import AdminArea from "../../components/admin-area";
import TeamArea from "../../components/team-area";

export default function ChatPage() {
  const router = useRouter();
  const { token, activeWorkspace, logout, setToken, activeView, theme } = useChatStore();
  const [mounted, setMounted] = useState(false);
  const [initLoading, setInitLoading] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Synchronize document theme class
  useEffect(() => {
    if (typeof window !== "undefined") {
      const root = window.document.documentElement;
      if (theme === "dark") {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    }
  }, [theme]);

  // Initialize token from localStorage on mount
  useEffect(() => {
    const localToken = localStorage.getItem("nexora_token");
    if (localToken) setToken(localToken);
    setMounted(true);
  }, [setToken]);

  // Authentication check
  useEffect(() => {
    if (mounted && !token) router.push("/");
  }, [token, mounted, router]);

  // Initial workspace data
  useEffect(() => {
    if (!token) return;
    const run = async () => {
      try {
        setInitLoading(true);
        await apiService.fetchCurrentUser();
        const workspaces = await apiService.fetchWorkspaces();
        if (workspaces.length === 0) await apiService.createWorkspace("My AI Workspace");
      } catch {
        logout();
        router.push("/");
      } finally {
        setInitLoading(false);
      }
    };
    run();
  }, [token, logout, router]);

  // Fetch workspace assets when active workspace changes
  useEffect(() => {
    if (!token || !activeWorkspace) return;
    const run = async () => {
      try {
        await Promise.all([
          apiService.fetchFolders(activeWorkspace.id),
          apiService.fetchConversations(activeWorkspace.id),
        ]);
      } catch (err) {
        console.error("Error loading workspace assets:", err);
      }
    };
    run();
  }, [token, activeWorkspace]);

  // === Ambient Particle Animation ===
  useEffect(() => {
    if (!mounted || !token || initLoading) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);

    const onResize = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", onResize);

    interface P { x: number; y: number; vx: number; vy: number; r: number; a: number }
    const pts: P[] = Array.from({ length: 50 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      r: Math.random() * 2 + 0.8,
      a: Math.random() * 0.5 + 0.5,
    }));

    const tick = () => {
      ctx.clearRect(0, 0, W, H);
      // connections
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x;
          const dy = pts[i].y - pts[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 160) {
            const op = (0.28 * (1 - d / 160)).toFixed(3);
            ctx.strokeStyle = `rgba(99,102,241,${op})`;
            ctx.lineWidth = 0.7;
            ctx.beginPath();
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.stroke();
          }
        }
      }
      // dots
      for (const p of pts) {
        ctx.fillStyle = `rgba(34,211,238,${p.a})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = W; else if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; else if (p.y > H) p.y = 0;
      }
      animId = requestAnimationFrame(tick);
    };
    tick();
    return () => { window.removeEventListener("resize", onResize); cancelAnimationFrame(animId); };
  }, [mounted, token, initLoading]);

  if (!mounted || !token) return null;
  if (initLoading) return <NexoraLoader message="Loading your workspace..." subMessage="Syncing conversations & knowledge bases" />;

  return (
    <div className="relative flex h-screen w-screen overflow-hidden bg-background text-foreground transition-colors duration-300">
      {/* Futuristic grid backdrop */}
      <div
        className="absolute inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right,var(--grid-line) 1px,transparent 1px),linear-gradient(to bottom,var(--grid-line) 1px,transparent 1px)",
          backgroundSize: "80px 80px",
        }}
      />

      {/* Ambient glow blobs */}
      <div className="absolute top-0 right-0 h-[550px] w-[550px] rounded-full pointer-events-none transition-opacity duration-300"
        style={{ 
          background: "radial-gradient(circle,rgba(99,102,241,0.18) 0%,transparent 70%)", 
          filter: "blur(60px)",
          opacity: theme === "dark" ? 1 : 0.4 
        }} />
      <div className="absolute bottom-0 left-[25%] h-[450px] w-[450px] rounded-full pointer-events-none transition-opacity duration-300"
        style={{ 
          background: "radial-gradient(circle,rgba(6,182,212,0.14) 0%,transparent 70%)", 
          filter: "blur(60px)",
          opacity: theme === "dark" ? 1 : 0.4 
        }} />
      <div className="absolute top-[40%] left-[10%] h-[300px] w-[300px] rounded-full pointer-events-none transition-opacity duration-300"
        style={{ 
          background: "radial-gradient(circle,rgba(139,92,246,0.10) 0%,transparent 70%)", 
          filter: "blur(50px)",
          opacity: theme === "dark" ? 1 : 0.4 
        }} />

      {/* Particle canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 z-0 pointer-events-none"
        style={{ opacity: 0.85 }}
      />

      {/* Sidebar */}
      <div className="relative z-20">
        <ChatSidebar />
      </div>

      {/* Main panel */}
      <div className="relative z-10 flex flex-1 flex-col min-w-0 overflow-hidden">
        {activeView === "chat" ? <ChatArea /> :
          activeView === "knowledge" ? <KnowledgeArea /> :
          activeView === "analytics" ? <AnalyticsArea /> :
          activeView === "report" ? <ReportArea /> :
          activeView === "agents" ? <AgentStudio /> :
          activeView === "sql" ? <SQLStudio /> :
          activeView === "python" ? <PythonStudio /> :
          activeView === "email" ? <EmailStudio /> :
          activeView === "calendar" ? <CalendarStudio /> :
          activeView === "team" ? <TeamArea /> :
          activeView === "eval" ? <EvalDashboard /> :
          activeView === "admin" ? <AdminArea /> :
          <MLArea />}
      </div>
    </div>
  );
}
