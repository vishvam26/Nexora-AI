"use client";

import { useState, useEffect } from "react";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import {
  Users, CheckSquare, Activity, Sparkles, Plus, Clock,
  AlertCircle, CheckCircle2, UserPlus, Shield, UserCheck,
  Search, ArrowRight, RefreshCw, BarChart2, Mail, Layers
} from "lucide-react";

export default function TeamArea() {
  const { activeWorkspace } = useChatStore();
  const [activeTab, setActiveTab] = useState<"tasks" | "members" | "activity">("tasks");

  // Tasks State
  const [tasks, setTasks] = useState<any[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(false);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState("MEDIUM");
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [loadingAI, setLoadingAI] = useState(false);

  // Members State
  const [members, setMembers] = useState<any[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("EDITOR");
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  // Activity State
  const [activities, setActivities] = useState<any[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(false);

  // Initial Fetching
  useEffect(() => {
    if (!activeWorkspace) return;
    loadTasks();
    loadMembers();
    loadActivity();
  }, [activeWorkspace]);

  const loadTasks = async () => {
    if (!activeWorkspace) return;
    try {
      setLoadingTasks(true);
      const data = await apiService.fetchTasks(activeWorkspace.id);
      setTasks(Array.isArray(data) ? data : []);
    } catch {
      setTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  };

  const loadMembers = async () => {
    if (!activeWorkspace) return;
    try {
      setLoadingMembers(true);
      const data = await apiService.fetchWorkspaceMembers(activeWorkspace.id);
      setMembers(Array.isArray(data) ? data : []);
    } catch {
      setMembers([]);
    } finally {
      setLoadingMembers(false);
    }
  };

  const loadActivity = async () => {
    if (!activeWorkspace) return;
    try {
      setLoadingActivities(true);
      const data = await apiService.fetchActivityFeed(activeWorkspace.id);
      setActivities(Array.isArray(data) ? data : []);
    } catch {
      setActivities([]);
    } finally {
      setLoadingActivities(false);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !activeWorkspace) return;
    
    const tempTask: TaskItem = {
      id: Date.now(),
      workspace_id: activeWorkspace.id,
      title: newTaskTitle,
      description: newTaskDesc,
      status: "todo",
      priority: newTaskPriority,
      created_at: new Date().toISOString(),
    };

    // Optimistic UI update
    setTasks(prev => [tempTask, ...prev]);
    setNewTaskTitle("");
    setNewTaskDesc("");
    setShowNewTaskModal(false);

    try {
      await apiService.createTask({
        workspace_id: activeWorkspace.id,
        title: tempTask.title,
        description: tempTask.description,
        priority: tempTask.priority,
      });
      loadTasks();
      loadActivity();
    } catch (err) {
      console.warn("Backend /tasks endpoint unavailable, using local task:", err);
    }
  };

  const handleUpdateStatus = async (taskId: number, newStatus: string) => {
    // Optimistic status update
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
    try {
      await apiService.updateTaskStatus(taskId, newStatus);
      loadActivity();
    } catch (err) {
      console.warn("Backend status update unavailable:", err);
    }
  };

  const handleFetchAiPM = async () => {
    if (!activeWorkspace) return;
    try {
      setLoadingAI(true);
      const data = await apiService.fetchAIPMInsights(activeWorkspace.id);
      setAiInsights(data);
    } catch {
      // Local AI PM Review Summary
      const todoCount = tasks.filter(t => t.status?.toLowerCase() === "todo" || t.status?.toLowerCase() === "pending").length;
      const inProgCount = tasks.filter(t => t.status?.toLowerCase() === "in_progress" || t.status?.toLowerCase() === "work").length;
      const doneCount = tasks.filter(t => t.status?.toLowerCase() === "completed" || t.status?.toLowerCase() === "done").length;
      
      const healthScore = tasks.length > 0 ? Math.round((doneCount / tasks.length) * 100) : 100;

      setAiInsights({
        summary: `Team Health: Excellent. Workspace "${activeWorkspace.name}" has ${tasks.length} active work items (${doneCount} completed, ${inProgCount} in progress, ${todoCount} pending).`,
        recommendations: doneCount === tasks.length 
          ? ["All work items completed! Great team performance.", "Plan next sprint or add new tasks."]
          : ["Focus on completing in-progress items before picking new tasks.", "Ensure team members update task statuses regularly."],
        velocity_score: healthScore,
        risk_level: healthScore > 80 ? "LOW" : "MEDIUM"
      });
    } finally {
      setLoadingAI(false);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim() || !activeWorkspace) return;
    try {
      await apiService.inviteWorkspaceMember(activeWorkspace.id, inviteEmail, inviteRole);
      setInviteSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      setTimeout(() => setInviteSuccess(null), 4000);
      loadMembers();
    } catch (err) {
      console.error("Failed sending invite", err);
    }
  };

  if (!activeWorkspace) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center">
        <Users className="h-12 w-12 text-muted-foreground/50 mb-3" />
        <h3 className="text-lg font-medium">No Active Workspace Selected</h3>
        <p className="text-sm text-muted-foreground max-w-sm mt-1">Select or create a workspace to start collaborating with your team.</p>
      </div>
    );
  }

  const todoTasks = tasks.filter(t => t.status?.toLowerCase() === "todo" || t.status?.toLowerCase() === "pending");
  const inProgressTasks = tasks.filter(t => t.status?.toLowerCase() === "in_progress" || t.status?.toLowerCase() === "inprogress");
  const completedTasks = tasks.filter(t => t.status?.toLowerCase() === "completed" || t.status?.toLowerCase() === "done");

  return (
    <div className="flex flex-1 flex-col h-full overflow-hidden bg-background text-foreground">
      {/* Header Bar */}
      <div className="border-b border-border bg-card/40 px-6 py-4 backdrop-blur flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">V2 TEAM MODE</span>
            <h1 className="text-xl font-bold tracking-tight">{activeWorkspace.name}</h1>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">Team Collaboration & Project Management Space</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("tasks")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "tasks" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-accent text-muted-foreground"
            }`}
          >
            <CheckSquare className="h-3.5 w-3.5" />
            Task Board ({tasks.length})
          </button>
          <button
            onClick={() => setActiveTab("members")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "members" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-accent text-muted-foreground"
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            Members ({members.length})
          </button>
          <button
            onClick={() => setActiveTab("activity")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "activity" ? "bg-primary text-primary-foreground shadow-sm" : "hover:bg-accent text-muted-foreground"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            Activity Feed
          </button>
        </div>
      </div>

      {/* Main Content Body */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* ================= TASKS TAB ================= */}
        {activeTab === "tasks" && (
          <div className="space-y-6">
            {/* Top Toolbar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowNewTaskModal(true)}
                  className="flex items-center gap-2 bg-primary text-primary-foreground text-xs font-medium px-4 py-2 rounded-lg shadow hover:opacity-90 transition"
                >
                  <Plus className="h-4 w-4" /> Add New Task
                </button>
                <button
                  onClick={handleFetchAiPM}
                  disabled={loadingAI}
                  className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs font-medium px-4 py-2 rounded-lg shadow hover:opacity-90 transition disabled:opacity-50"
                >
                  <Sparkles className="h-4 w-4" />
                  {loadingAI ? "Analyzing..." : "AI Project Manager Review"}
                </button>
              </div>

              <button
                onClick={loadTasks}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1.5"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loadingTasks ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            {/* AI Insights Card */}
            {aiInsights && (
              <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-purple-400 font-semibold text-xs">
                    <Sparkles className="h-4 w-4" /> AI PM Analysis Summary
                  </div>
                  <span className="text-[10px] text-muted-foreground">Health Score: {aiInsights.health_score ?? "N/A"}/100</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{aiInsights.summary || "All systems operational. No major bottlenecks detected."}</p>
                {aiInsights.recommendations && aiInsights.recommendations.length > 0 && (
                  <div className="pt-2 border-t border-purple-500/10 space-y-1">
                    <span className="text-[11px] font-medium text-foreground">Actionable Recommendations:</span>
                    <ul className="list-disc list-inside text-xs text-muted-foreground space-y-0.5">
                      {aiInsights.recommendations.map((rec: string, idx: number) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Kanban Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* TODO Column */}
              <div className="rounded-xl border border-border bg-card/70 shadow-sm p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-border/70 pb-2.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <Clock className="h-4 w-4 text-amber-500" /> To Do ({todoTasks.length})
                  </div>
                </div>
                <div className="space-y-3">
                  {todoTasks.map(t => (
                    <TaskCard key={t.id} task={t} onMove={(status) => handleUpdateStatus(t.id, status)} />
                  ))}
                  {todoTasks.length === 0 && <p className="text-xs text-center text-muted-foreground font-medium py-8">No tasks to do</p>}
                </div>
              </div>

              {/* IN PROGRESS Column */}
              <div className="rounded-xl border border-border bg-card/70 shadow-sm p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-border/70 pb-2.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <Activity className="h-4 w-4 text-cyan-500" /> In Progress ({inProgressTasks.length})
                  </div>
                </div>
                <div className="space-y-3">
                  {inProgressTasks.map(t => (
                    <TaskCard key={t.id} task={t} onMove={(status) => handleUpdateStatus(t.id, status)} />
                  ))}
                  {inProgressTasks.length === 0 && <p className="text-xs text-center text-muted-foreground font-medium py-8">No active tasks</p>}
                </div>
              </div>

              {/* COMPLETED Column */}
              <div className="rounded-xl border border-border bg-card/70 shadow-sm p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-border/70 pb-2.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-foreground">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Completed ({completedTasks.length})
                  </div>
                </div>
                <div className="space-y-3">
                  {completedTasks.map(t => (
                    <TaskCard key={t.id} task={t} onMove={(status) => handleUpdateStatus(t.id, status)} />
                  ))}
                  {completedTasks.length === 0 && <p className="text-xs text-center text-muted-foreground font-medium py-8">No finished tasks</p>}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= MEMBERS TAB ================= */}
        {activeTab === "members" && (
          <div className="space-y-6 max-w-4xl">
            {/* Invite Box */}
            <div className="rounded-xl border border-border bg-card p-5 space-y-4">
              <div>
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <UserPlus className="h-4 w-4 text-primary" /> Invite Team Member
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">Collaborators will receive access to this workspace tasks and knowledge base.</p>
              </div>

              {inviteSuccess && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> {inviteSuccess}
                </div>
              )}

              <form onSubmit={handleInviteMember} className="flex gap-3">
                <input
                  type="email"
                  placeholder="colleague@example.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1 bg-background border border-border text-xs px-3.5 py-2 rounded-lg outline-none focus:border-primary"
                  required
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="bg-background border border-border text-xs px-3 py-2 rounded-lg outline-none focus:border-primary"
                >
                  <option value="EDITOR">Editor (Can edit)</option>
                  <option value="ADMIN">Admin (Full control)</option>
                  <option value="VIEWER">Viewer (Read only)</option>
                </select>
                <button type="submit" className="bg-primary text-primary-foreground text-xs font-medium px-4 py-2 rounded-lg hover:opacity-90">
                  Send Invite
                </button>
              </form>
            </div>

            {/* Member List */}
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-muted/20 flex items-center justify-between">
                <span className="text-xs font-semibold text-muted-foreground">Workspace Members ({members.length})</span>
              </div>
              <div className="divide-y divide-border">
                {members.map(m => (
                  <div key={m.id} className="p-4 flex items-center justify-between hover:bg-muted/10">
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                        {m.user?.full_name?.slice(0, 2).toUpperCase() || "U"}
                      </div>
                      <div>
                        <div className="text-xs font-semibold">{m.user?.full_name || "Team Member"}</div>
                        <div className="text-[11px] text-muted-foreground">{m.user?.email || "No email"}</div>
                      </div>
                    </div>
                    <span className="text-[10px] font-medium px-2.5 py-1 rounded-full bg-accent text-accent-foreground border border-border">
                      {m.role || "MEMBER"}
                    </span>
                  </div>
                ))}
                {members.length === 0 && (
                  <div className="p-6 text-center text-xs text-muted-foreground">No extra members yet. Invite someone above!</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ================= ACTIVITY TAB ================= */}
        {activeTab === "activity" && (
          <div className="space-y-4 max-w-3xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan-500" /> Recent Activity Timeline
              </h3>
              <button onClick={loadActivity} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <RefreshCw className={`h-3 w-3 ${loadingActivities ? "animate-spin" : ""}`} /> Refresh
              </button>
            </div>

            <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-border">
              {activities.map((act, idx) => (
                <div key={act.id || idx} className="relative flex gap-4 text-xs items-start pl-8">
                  <div className="absolute left-1.5 top-1.5 h-4 w-4 rounded-full bg-background border-2 border-primary flex items-center justify-center" />
                  <div className="flex-1 bg-card border border-border p-3.5 rounded-xl space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-foreground">{act.actor_name || "User"}</span>
                      <span className="text-muted-foreground">{act.created_at ? new Date(act.created_at).toLocaleTimeString() : "Just now"}</span>
                    </div>
                    <p className="text-muted-foreground text-xs">{act.action} — <span className="text-foreground">{act.details || "No details"}</span></p>
                  </div>
                </div>
              ))}

              {activities.length === 0 && (
                <p className="text-xs text-center text-muted-foreground py-8">No workspace activity logged yet.</p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* New Task Modal */}
      {showNewTaskModal && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md space-y-4 shadow-xl">
            <h3 className="text-sm font-bold">Create New Workspace Task</h3>
            <form onSubmit={handleCreateTask} className="space-y-3 text-xs">
              <div>
                <label className="text-muted-foreground block mb-1">Task Title</label>
                <input
                  type="text"
                  placeholder="e.g., Prepare dataset for ML model"
                  value={newTaskTitle}
                  onChange={(e) => setNewTaskTitle(e.target.value)}
                  className="w-full bg-background border border-border px-3 py-2 rounded-lg outline-none focus:border-primary"
                  required
                />
              </div>

              <div>
                <label className="text-muted-foreground block mb-1">Description (Optional)</label>
                <textarea
                  placeholder="Provide context or guidelines for this task..."
                  value={newTaskDesc}
                  onChange={(e) => setNewTaskDesc(e.target.value)}
                  className="w-full bg-background border border-border px-3 py-2 rounded-lg outline-none focus:border-primary h-20 resize-none"
                />
              </div>

              <div>
                <label className="text-muted-foreground block mb-1">Priority</label>
                <select
                  value={newTaskPriority}
                  onChange={(e) => setNewTaskPriority(e.target.value)}
                  className="w-full bg-background border border-border px-3 py-2 rounded-lg outline-none"
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewTaskModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-muted-foreground hover:bg-accent"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg font-medium">
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function TaskCard({ task, onMove }: { task: any; onMove: (status: string) => void }) {
  const priorityColors: Record<string, string> = {
    LOW: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    MEDIUM: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    HIGH: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    CRITICAL: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  return (
    <div className="bg-card border border-border p-3.5 rounded-lg space-y-2 hover:border-primary/40 transition">
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-xs font-semibold leading-tight">{task.title}</h4>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${priorityColors[task.priority] || priorityColors.MEDIUM}`}>
          {task.priority || "MEDIUM"}
        </span>
      </div>
      {task.description && (
        <p className="text-[11px] text-muted-foreground line-clamp-2">{task.description}</p>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-border/50 text-[10px]">
        <span className="text-muted-foreground">Assigned: {task.assignee?.full_name || "Unassigned"}</span>
        <div className="flex gap-1">
          {task.status !== "TODO" && (
            <button onClick={() => onMove("TODO")} className="px-1.5 py-0.5 rounded bg-muted hover:bg-accent text-muted-foreground">
              Todo
            </button>
          )}
          {task.status !== "IN_PROGRESS" && (
            <button onClick={() => onMove("IN_PROGRESS")} className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20">
              Work
            </button>
          )}
          {task.status !== "COMPLETED" && (
            <button onClick={() => onMove("COMPLETED")} className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20">
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
