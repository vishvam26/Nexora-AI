"use client";

import { useEffect, useState } from "react";
import { apiClient } from "../services/api-service";
import { useChatStore } from "../stores/chat-store";
import {
  Users,
  Settings,
  Key,
  Mail,
  UserPlus,
  ShieldCheck,
  CheckCircle,
  AlertCircle,
  Save,
  Loader2,
  Trash2,
} from "lucide-react";

export default function AdminArea() {
  const { user, theme } = useChatStore();
  const [activeTab, setActiveTab] = useState<"members" | "settings" | "secrets" | "invitations">("members");
  
  // States
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Members list & updates
  const [members, setMembers] = useState<any[]>([]);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editRole, setEditRole] = useState("EMPLOYEE");
  const [editManagerId, setEditManagerId] = useState<number | null>(null);

  // Company Settings
  const [settings, setSettings] = useState<any>({
    default_llm: "gemini-1.5-flash",
    theme: "dark",
    logo: "",
    max_file_size: 10485760,
  });

  // Secrets Manager
  const [secrets, setSecrets] = useState<any[]>([]);
  const [newSecretProvider, setNewSecretProvider] = useState("GEMINI");
  const [newSecretKey, setNewSecretKey] = useState("");

  // Invitations
  const [invitations, setInvitations] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("EMPLOYEE");

  // Notifications helper
  const notify = (msg: string, isError = false) => {
    if (isError) {
      setErrorMsg(msg);
      setTimeout(() => setErrorMsg(null), 4000);
    } else {
      setSuccessMsg(msg);
      setTimeout(() => setSuccessMsg(null), 4000);
    }
  };

  // 1. Fetch Members
  const fetchMembers = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/company/members");
      setMembers(res.data);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to load team members.", true);
    } finally {
      setLoading(false);
    }
  };

  // 2. Fetch Settings
  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/company/settings");
      setSettings(res.data);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to load settings.", true);
    } finally {
      setLoading(false);
    }
  };

  // 3. Fetch Secrets
  const fetchSecrets = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/company/secrets");
      setSecrets(res.data);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to load API keys.", true);
    } finally {
      setLoading(false);
    }
  };

  // 4. Fetch Invitations
  const fetchInvitations = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/company/invitations");
      setInvitations(res.data);
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to load invitations.", true);
    } finally {
      setLoading(false);
    }
  };

  // Load active tab data
  useEffect(() => {
    if (activeTab === "members") fetchMembers();
    if (activeTab === "settings") fetchSettings();
    if (activeTab === "secrets") fetchSecrets();
    if (activeTab === "invitations") fetchInvitations();
  }, [activeTab]);

  // Update Member Role/Hierarchy
  const handleUpdateMember = async (userId: number) => {
    try {
      setLoading(true);
      await apiClient.put(`/company/members/${userId}`, {
        company_role: editRole,
        manager_id: editManagerId === -1 ? null : editManagerId,
      });
      notify("Member hierarchy updated successfully.");
      setEditingUserId(null);
      fetchMembers();
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to update member.", true);
    } finally {
      setLoading(false);
    }
  };

  // Save Settings
  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await apiClient.put("/company/settings", settings);
      notify("Branding and preferences saved.");
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to save settings.", true);
    } finally {
      setLoading(false);
    }
  };

  // Save Secret key
  const handleSaveSecret = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSecretKey.trim()) return;
    try {
      setLoading(true);
      await apiClient.post("/company/secrets", {
        provider: newSecretProvider,
        api_key: newSecretKey,
      });
      notify(`${newSecretProvider} API Key saved securely.`);
      setNewSecretKey("");
      fetchSecrets();
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to save secret key.", true);
    } finally {
      setLoading(false);
    }
  };

  // Send Invitation
  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    try {
      setLoading(true);
      await apiClient.post("/company/invite", {
        email: inviteEmail,
        role: inviteRole,
      });
      notify(`Invitation sent to ${inviteEmail}.`);
      setInviteEmail("");
      fetchInvitations();
    } catch (err: any) {
      notify(err.response?.data?.detail || "Failed to send invitation.", true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-950/80 backdrop-blur-md p-6 text-slate-100 overflow-y-auto">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between border-b border-slate-800/80 pb-6 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="h-6 w-6 text-sky-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Enterprise Console
            </h1>
          </div>
          <p className="text-sm text-slate-400">
            Manage company members, branding settings, token invitations, and secure provider API credentials.
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-3">
          <span className="text-xs bg-slate-800 px-3 py-1 rounded-full text-slate-300 font-semibold border border-slate-700">
            Role: <span className="text-sky-400">{user?.company_role || "EMPLOYEE"}</span>
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        
        {/* Navigation Sidebar */}
        <div className="flex flex-row lg:flex-col w-full lg:w-64 bg-slate-900/60 border border-slate-800 rounded-xl p-2 gap-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab("members")}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === "members"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Team Hierarchy</span>
          </button>
          
          <button
            onClick={() => setActiveTab("settings")}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === "settings"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            }`}
          >
            <Settings className="h-4 w-4" />
            <span>Tenancy Settings</span>
          </button>
          
          <button
            onClick={() => setActiveTab("secrets")}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === "secrets"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            }`}
          >
            <Key className="h-4 w-4" />
            <span>Secrets & API Keys</span>
          </button>
          
          <button
            onClick={() => setActiveTab("invitations")}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              activeTab === "invitations"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            }`}
          >
            <Mail className="h-4 w-4" />
            <span>Token Invites</span>
          </button>
        </div>

        {/* Content Panel Area */}
        <div className="flex-1 w-full bg-slate-900/40 border border-slate-800 rounded-xl p-6 relative">
          
          {/* Notifications */}
          {successMsg && (
            <div className="mb-4 flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-sm">
              <CheckCircle className="h-4 w-4" />
              <span>{successMsg}</span>
            </div>
          )}
          {errorMsg && (
            <div className="mb-4 flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Loading Indicator Overlay */}
          {loading && (
            <div className="absolute top-4 right-4 flex items-center gap-2 text-xs text-slate-500">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Loading...</span>
            </div>
          )}

          {/* TAB CONTENT: Members Team Directory */}
          {activeTab === "members" && (
            <div>
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-white">Team Hierarchy Directory</h2>
                <p className="text-xs text-slate-400">View team members and configure reporting managers to define access hierarchy rules.</p>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="min-w-full divide-y divide-slate-800">
                  <thead className="bg-slate-900/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Member Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Email Address</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Company Role</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">Reports To</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-300 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 bg-slate-900/10">
                    {members.map((m) => (
                      <tr key={m.id} className="hover:bg-slate-850/50 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-slate-200">{m.full_name}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{m.email}</td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-300">
                          {editingUserId === m.id ? (
                            <select
                              value={editRole}
                              onChange={(e) => setEditRole(e.target.value)}
                              className="bg-slate-800 border border-slate-700 text-sm rounded px-2 py-1 text-slate-200"
                            >
                              <option value="OWNER">OWNER</option>
                              <option value="ADMIN">ADMIN</option>
                              <option value="EMPLOYEE">EMPLOYEE</option>
                            </select>
                          ) : (
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                              m.company_role === "OWNER" ? "bg-purple-500/15 text-purple-400" :
                              m.company_role === "ADMIN" ? "bg-amber-500/15 text-amber-400" : "bg-slate-800 text-slate-400"
                            }`}>
                              {m.company_role}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-300">
                          {editingUserId === m.id ? (
                            <select
                              value={editManagerId || -1}
                              onChange={(e) => setEditManagerId(parseInt(e.target.value))}
                              className="bg-slate-800 border border-slate-700 text-sm rounded px-2 py-1 text-slate-200 max-w-[150px]"
                            >
                              <option value={-1}>No Manager</option>
                              {members
                                .filter((u) => u.id !== m.id)
                                .map((u) => (
                                  <option key={u.id} value={u.id}>{u.full_name}</option>
                                ))}
                            </select>
                          ) : (
                            <span className="text-slate-400 text-xs font-medium">
                              {m.manager_name || "— (Top Hierarchical Leader)"}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                          {editingUserId === m.id ? (
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleUpdateMember(m.id)}
                                className="bg-sky-500 hover:bg-sky-600 px-3 py-1 rounded text-xs text-white font-semibold transition"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => setEditingUserId(null)}
                                className="bg-slate-800 hover:bg-slate-750 px-3 py-1 rounded text-xs text-slate-300 transition"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => {
                                setEditingUserId(m.id);
                                setEditRole(m.company_role);
                                setEditManagerId(m.manager_id);
                              }}
                              className="text-xs text-sky-400 hover:text-sky-300 underline font-semibold transition"
                            >
                              Edit Position
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB CONTENT: Tenancy Settings */}
          {activeTab === "settings" && (
            <form onSubmit={handleSaveSettings} className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white">Tenancy Preference Configs</h2>
                <p className="text-xs text-slate-400">Update logo theme and system-wide default configs for user profiles.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Default Model Engine</label>
                  <select
                    value={settings.default_llm}
                    onChange={(e) => setSettings({ ...settings, default_llm: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  >
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Ultra Fast)</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro (Highly Intelligent)</option>
                    <option value="gpt-4o">OpenAI GPT-4o (Production Adaptive)</option>
                    <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Branding Theme</label>
                  <select
                    value={settings.theme}
                    onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  >
                    <option value="dark">Sky Blue Cyberpunk (Dark)</option>
                    <option value="light">Vanilla Minimal (Light)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Custom Logo Link</label>
                  <input
                    type="text"
                    placeholder="https://example.com/logo.png"
                    value={settings.logo || ""}
                    onChange={(e) => setSettings({ ...settings, logo: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Max File Size Limit (Bytes)</label>
                  <input
                    type="number"
                    value={settings.max_file_size}
                    onChange={(e) => setSettings({ ...settings, max_file_size: parseInt(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-800">
                <button
                  type="submit"
                  className="flex items-center gap-2 bg-sky-500 hover:bg-sky-600 text-white font-semibold text-sm rounded-lg px-4 py-2.5 transition"
                >
                  <Save className="h-4 w-4" />
                  Save Branding Settings
                </button>
              </div>
            </form>
          )}

          {/* TAB CONTENT: Secrets & API Keys */}
          {activeTab === "secrets" && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white">External Secrets Manager</h2>
                <p className="text-xs text-slate-400">Configure provider keys (OpenAI, Anthropic, Gemini). Keys are AES-256 encrypted before persistence.</p>
              </div>

              {/* Secret Create Form */}
              <form onSubmit={handleSaveSecret} className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg flex flex-col md:flex-row items-end gap-4">
                <div className="flex-1 space-y-2 w-full">
                  <label className="text-xs font-semibold text-slate-300">API Provider</label>
                  <select
                    value={newSecretProvider}
                    onChange={(e) => setNewSecretProvider(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  >
                    <option value="GEMINI">Google Gemini</option>
                    <option value="OPENAI">OpenAI</option>
                    <option value="ANTHROPIC">Anthropic Claude</option>
                  </select>
                </div>

                <div className="flex-[2] space-y-2 w-full">
                  <label className="text-xs font-semibold text-slate-300">API Secret Key</label>
                  <input
                    type="password"
                    placeholder="Enter API key string"
                    value={newSecretKey}
                    onChange={(e) => setNewSecretKey(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  />
                </div>

                <button
                  type="submit"
                  className="flex items-center gap-2 bg-sky-500 hover:bg-sky-600 text-white font-semibold text-sm rounded-lg px-4 py-2.5 transition w-full md:w-auto shrink-0"
                >
                  Save API Key
                </button>
              </form>

              {/* Secrets List */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Configured Secrets</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {secrets.length === 0 ? (
                    <div className="p-4 border border-slate-800/80 rounded-lg text-center text-slate-500 text-sm col-span-2">
                      No external secret API keys configured yet.
                    </div>
                  ) : (
                    secrets.map((sec) => (
                      <div key={sec.id} className="p-4 border border-slate-800 rounded-lg flex items-center justify-between bg-slate-900/20">
                        <div className="flex items-center gap-3">
                          <Key className="h-5 w-5 text-emerald-400" />
                          <div>
                            <p className="text-sm font-semibold text-slate-200">{sec.provider}</p>
                            <p className="text-xs text-slate-500">AES-256 Encrypted</p>
                          </div>
                        </div>
                        <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold">
                          Active
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB CONTENT: Invitations */}
          {activeTab === "invitations" && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white">Token Invitation Console</h2>
                <p className="text-xs text-slate-400">Invite new team members to sign up under your company. Tokens automatically expire in 7 days.</p>
              </div>

              {/* Invite Form */}
              <form onSubmit={handleSendInvite} className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg flex flex-col md:flex-row items-end gap-4">
                <div className="flex-1 space-y-2 w-full">
                  <label className="text-xs font-semibold text-slate-300">Invite Email Address</label>
                  <input
                    type="email"
                    placeholder="employee@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                    required
                  />
                </div>

                <div className="flex-1 space-y-2 w-full">
                  <label className="text-xs font-semibold text-slate-300">Company Role Assignment</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200"
                  >
                    <option value="EMPLOYEE">EMPLOYEE</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="flex items-center gap-2 bg-sky-500 hover:bg-sky-600 text-white font-semibold text-sm rounded-lg px-4 py-2.5 transition w-full md:w-auto shrink-0"
                >
                  <UserPlus className="h-4 w-4" />
                  Send Invitation
                </button>
              </form>

              {/* Invitations List */}
              <div className="space-y-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pending Token Links</h3>
                <div className="overflow-x-auto border border-slate-800 rounded-lg">
                  <table className="min-w-full divide-y divide-slate-800">
                    <thead className="bg-slate-900/50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-slate-400 uppercase">Invited Email</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-slate-400 uppercase">Role</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-slate-400 uppercase">Token Code</th>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-slate-400 uppercase">Expires At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-slate-900/10">
                      {invitations.length === 0 ? (
                        <tr>
                          <td colSpan={4} className="px-4 py-4 text-center text-slate-500 text-sm">
                            No pending invitations found.
                          </td>
                        </tr>
                      ) : (
                        invitations.map((inv) => (
                          <tr key={inv.id} className="hover:bg-slate-850/50">
                            <td className="px-4 py-2.5 whitespace-nowrap text-sm text-slate-250 font-semibold">{inv.email}</td>
                            <td className="px-4 py-2.5 whitespace-nowrap text-xs text-slate-400">{inv.role}</td>
                            <td className="px-4 py-2.5 whitespace-nowrap text-xs text-sky-400 font-mono select-all select-none hover:text-sky-300">
                              {inv.token}
                            </td>
                            <td className="px-4 py-2.5 whitespace-nowrap text-xs text-slate-500">
                              {new Date(inv.expires_at).toLocaleString()}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
