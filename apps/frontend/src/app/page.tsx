"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { LogIn, UserPlus, ShieldAlert, Cpu } from "lucide-react";

export default function WelcomePage() {
  const router = useRouter();
  const { token, logout, setToken } = useChatStore();
  
  // Local states
  const [mounted, setMounted] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Initialize token from localStorage on mount
  useEffect(() => {
    const localToken = localStorage.getItem("nexora_token");
    if (localToken) {
      setToken(localToken);
    }
    setMounted(true);
  }, [setToken]);

  // If token is already present, redirect straight to chat
  useEffect(() => {
    if (mounted && token) {
      router.push("/chat");
    }
  }, [token, mounted, router]);

  if (!mounted) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!email || !password || (isRegister && !fullName)) {
      setError("Please fill in all fields.");
      setLoading(false);
      return;
    }

    try {
      if (isRegister) {
        // Sign Up Flow
        await apiService.register(fullName, email, password);
        // Automatically trigger log in after successful sign up
        await apiService.login(email, password);
      } else {
        // Sign In Flow
        await apiService.login(email, password);
      }
      
      // Fetch user profile info
      await apiService.fetchCurrentUser();
      router.push("/chat");
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || 
        "Authentication failed. Please verify your credentials."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-[#09090b] text-[#f4f4f5]">
      {/* Decorative background grid and glowing circles */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#1f1f23_1px,transparent_1px),linear-gradient(to_bottom,#1f1f23_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-30"></div>
      <div className="absolute top-[20%] left-[10%] z-0 h-[400px] w-[400px] rounded-full bg-indigo-500/10 blur-[120px]"></div>
      <div className="absolute bottom-[20%] right-[10%] z-0 h-[400px] w-[400px] rounded-full bg-purple-500/10 blur-[120px]"></div>

      <div className="z-10 flex w-full max-w-[1000px] overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/50 backdrop-blur-xl shadow-2xl md:min-h-[600px]">
        {/* Left Pane - Brand Promo */}
        <div className="relative hidden w-1/2 flex-col justify-between bg-gradient-to-br from-zinc-900 to-zinc-950 p-12 border-r border-zinc-800/80 md:flex">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 shadow-lg shadow-indigo-600/30">
              <Cpu className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">Nexora AI</span>
          </div>

          <div className="space-y-4">
            <h1 className="text-3xl font-bold leading-tight text-white">
              Enterprise AI & Fine-Tuning Workspace
            </h1>
            <p className="text-sm leading-relaxed text-zinc-400">
              Train local language models, orchestrate hybrid search RAG pipelines, generate synthetic dataset projects, and deploy custom intelligent agents in one unified environment.
            </p>
          </div>

          <div className="text-xs text-zinc-500">
            &copy; 2026 Nexora-AI. MIT License.
          </div>
        </div>

        {/* Right Pane - Forms */}
        <div className="flex w-full flex-col justify-center px-8 py-12 md:w-1/2 md:px-12">
          <div className="mb-8 text-center md:text-left">
            <h2 className="text-2xl font-bold tracking-tight text-white">
              {isRegister ? "Create an Account" : "Welcome Back"}
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              {isRegister 
                ? "Sign up to begin fine-tuning models and building workspaces." 
                : "Sign in to access your workspaces and chats."}
            </p>
          </div>

          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
              <ShieldAlert className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  disabled={loading}
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@nexora.ai"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950/50 px-4 py-3 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 outline-none transition hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-500/50 active:scale-[0.98]"
              disabled={loading}
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
              ) : isRegister ? (
                <>
                  <UserPlus className="h-4 w-4" />
                  <span>Sign Up</span>
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-zinc-400">
            {isRegister ? "Already have an account?" : "New to Nexora AI?"}{" "}
            <button
              onClick={() => {
                setError(null);
                setIsRegister(!isRegister);
              }}
              className="font-semibold text-indigo-400 hover:text-indigo-300 outline-none focus:underline"
              disabled={loading}
            >
              {isRegister ? "Sign In" : "Create one here"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
