"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "../../stores/chat-store";
import { apiService } from "../../services/api-service";
import { LogIn, UserPlus, ShieldAlert, Eye, EyeOff, Lock, Mail, User, Cpu, ChevronRight, Activity, Globe, Compass, ArrowLeft } from "lucide-react";

// ── Boid interface for 3D bird animation ────────────────────────────
interface Boid {
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
  wingPhase: number; wingSpeed: number;
  size: number; color: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { token, setToken } = useChatStore();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });

  // Authentication States
  const [mounted, setMounted] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const localToken = localStorage.getItem("nexora_token");
    if (localToken) setToken(localToken);
    setMounted(true);
  }, [setToken]);

  useEffect(() => {
    if (mounted && token) router.push("/chat");
  }, [token, mounted, router]);

  // ── 3D Boids Canvas Background ─────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);
    const onResize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
    window.addEventListener("resize", onResize);

    const boids: Boid[] = Array.from({ length: 45 }, () => {
      const a = Math.random() * Math.PI * 2;
      const s = 1.0 + Math.random() * 1.6;
      return {
        x: (Math.random() - 0.5) * W * 0.9,
        y: (Math.random() - 0.5) * H * 0.9,
        z: Math.random() * 300 - 150,
        vx: Math.cos(a) * s, vy: Math.sin(a) * s,
        vz: (Math.random() - 0.5) * 1.0,
        wingPhase: Math.random() * Math.PI * 2,
        wingSpeed: 0.12 + Math.random() * 0.08,
        size: 3.0 + Math.random() * 1.6,
        color: Math.random() > 0.4 ? "rgba(99,102,241,0.65)" : "rgba(34,211,238,0.55)",
      };
    });

    const focal = 300;

    const onMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX - W / 2, y: e.clientY - H / 2, active: true };
    };
    const onMouseLeave = () => { mouseRef.current.active = false; };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseleave", onMouseLeave);

    const tick = () => {
      ctx.clearRect(0, 0, W, H);

      if (mouseRef.current.active) {
        const mx = mouseRef.current.x + W / 2, my = mouseRef.current.y + H / 2;
        const g = ctx.createRadialGradient(mx, my, 20, mx, my, 400);
        g.addColorStop(0, "rgba(99,102,241,0.06)");
        g.addColorStop(1, "rgba(9,9,11,0)");
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
      }

      boids.forEach((b) => {
        let avgVx = 0, avgVy = 0, avgVz = 0, avgX = 0, avgY = 0, avgZ = 0;
        let closeDx = 0, closeDy = 0, closeDz = 0, n = 0;

        boids.forEach((o) => {
          if (o === b) return;
          const dx = o.x - b.x, dy = o.y - b.y, dz = o.z - b.z;
          const d = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (d < 150) {
            avgVx += o.vx; avgVy += o.vy; avgVz += o.vz;
            avgX += o.x; avgY += o.y; avgZ += o.z; n++;
            if (d < 35) { closeDx -= dx * (2.0 / (d + 0.1)); closeDy -= dy * (2.0 / (d + 0.1)); closeDz -= dz * (2.0 / (d + 0.1)); }
          }
        });

        if (n > 0) {
          b.vx += ((avgVx / n) - b.vx) * 0.025 + ((avgX / n) - b.x) * 0.0006;
          b.vy += ((avgVy / n) - b.vy) * 0.025 + ((avgY / n) - b.y) * 0.0006;
          b.vz += ((avgVz / n) - b.vz) * 0.025 + ((avgZ / n) - b.z) * 0.0006;
        }

        b.vx += closeDx * 0.12; b.vy += closeDy * 0.12; b.vz += closeDz * 0.12;

        if (mouseRef.current.active) {
          const mdx = mouseRef.current.x - b.x, mdy = mouseRef.current.y - b.y;
          const md = Math.sqrt(mdx * mdx + mdy * mdy);
          if (md < 350) { b.vx += mdx * 0.0008; b.vy += mdy * 0.0008; }
        }

        const spd = Math.sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz);
        const maxS = 2.8;
        if (spd > maxS) { b.vx = (b.vx / spd) * maxS; b.vy = (b.vy / spd) * maxS; b.vz = (b.vz / spd) * maxS; }

        b.x += b.vx; b.y += b.vy; b.z += b.vz; b.wingPhase += b.wingSpeed;

        const bx = W / 2 + 120, by = H / 2 + 120;
        if (b.x > bx) b.x = -bx; else if (b.x < -bx) b.x = bx;
        if (b.y > by) b.y = -by; else if (b.y < -by) b.y = by;
        if (b.z > 200) b.z = -150; else if (b.z < -150) b.z = 200;

        const scale = focal / (focal + b.z);
        const px = W / 2 + b.x * scale, py = H / 2 + b.y * scale;
        const s2d = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
        const dx = b.vx / (s2d + 0.01), dy = b.vy / (s2d + 0.01);
        const nx = -dy, ny = dx;
        const sz = b.size * scale;
        const ws = sz * (1.3 + Math.sin(b.wingPhase) * 0.7);

        ctx.beginPath();
        ctx.moveTo(px + dx * sz * 2.2, py + dy * sz * 2.2);
        ctx.lineTo(px - dx * sz * 0.4 + nx * ws, py - dy * sz * 0.4 + ny * ws);
        ctx.lineTo(px - dx * sz * 0.5, py - dy * sz * 0.5);
        ctx.lineTo(px - dx * sz * 0.4 - nx * ws, py - dy * sz * 0.4 - ny * ws);
        ctx.closePath();

        const op = Math.max(0.12, Math.min(0.85, (b.z + 150) / 350));
        ctx.fillStyle = b.color.replace("0.65", op.toFixed(2)).replace("0.55", op.toFixed(2));
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px - dx * sz * 1.5, py - dy * sz * 1.5);
        ctx.strokeStyle = `rgba(99,102,241,${(op * 0.22).toFixed(2)})`;
        ctx.lineWidth = 0.9 * scale;
        ctx.stroke();
      });

      animId = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseleave", onMouseLeave);
      cancelAnimationFrame(animId);
    };
  }, []);

  if (!mounted) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password || (isRegister && (!fullName || !confirmPassword))) { setError("Please fill in all fields."); return; }
    if (isRegister && password !== confirmPassword) { setError("Passwords do not match."); return; }
    setLoading(true);
    try {
      if (isRegister) { await apiService.register(fullName, email, password); await apiService.login(email, password); }
      else { await apiService.login(email, password); }
      await apiService.fetchCurrentUser();
      router.push("/chat");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Authentication failed. Please verify your credentials.");
    } finally { setLoading(false); }
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col lg:flex-row items-center justify-center bg-[#09090b] text-[#f4f4f5] select-none overflow-hidden font-outfit">

      {/* Floating Back to Home button */}
      <button 
        onClick={() => router.push("/")}
        className="absolute top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 rounded-full border border-zinc-800 bg-[#09090b]/50 hover:bg-zinc-900 text-xs font-bold text-zinc-400 hover:text-white transition-all shadow-lg hover:border-zinc-700 backdrop-blur-md"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Home
      </button>

      {/* ── 3D Boids Canvas Background ─────────────────────────────── */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Background ambient glowing spheres */}
      <div className="absolute top-1/4 left-1/4 h-[700px] w-[700px] rounded-full bg-indigo-600/8 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-[500px] w-[500px] rounded-full bg-cyan-600/5 blur-[120px] pointer-events-none" />

      {/* Futuristic Grid Overlay */}
      <div className="absolute inset-0 z-0 bg-[linear-gradient(to_right,#1f1f23_1px,transparent_1px),linear-gradient(to_bottom,#1f1f23_1px,transparent_1px)] bg-[size:5rem_5rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-10 pointer-events-none" />

      {/* ── Main Layout Split Grid ─────────────────────────────────── */}
      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col lg:flex-row items-center justify-between gap-12 px-6 py-12 md:px-12">
        
        {/* ── Left Side: Interactive Branding / Cyber-Bird ─────────── */}
        <div className="flex flex-1 flex-col text-center lg:text-left justify-center space-y-6">
          
          {/* Version Pill */}
          <div className="mx-auto lg:mx-0 inline-flex w-fit items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-[10px] font-bold tracking-[0.2em] text-indigo-400 uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
            Nexora Console Access Portal
          </div>

          <h1 className="font-playfair text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl leading-[1.1]" style={{ fontFamily: "'Playfair Display', serif" }}>
            Unlock <br />
            <span className="text-glow bg-gradient-to-r from-indigo-450 via-violet-300 to-cyan-300 bg-clip-text text-transparent">
              intelligent automation.
            </span>
          </h1>

          <p className="mt-4 max-w-md text-xs leading-relaxed text-zinc-400 mx-auto lg:mx-0">
            Sign in to access your local QLoRA fine-tuning sandbox, grounded RAG collections, multi-agent workspaces, and real-time evaluation matrices.
          </p>

          {/* Quick Metrics row */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-6 pt-4 text-zinc-500">
            <div className="flex items-center gap-2">
              <Activity className="h-4.5 w-4.5 text-indigo-400" />
              <span className="text-[11px] font-semibold tracking-wider uppercase text-zinc-400">94% Accuracy</span>
            </div>
            <div className="flex items-center gap-2">
              <Globe className="h-4.5 w-4.5 text-cyan-400" />
              <span className="text-[11px] font-semibold tracking-wider uppercase text-zinc-400">100% Grounded</span>
            </div>
            <div className="flex items-center gap-2">
              <Compass className="h-4.5 w-4.5 text-violet-400" />
              <span className="text-[11px] font-semibold tracking-wider uppercase text-zinc-400">QLoRA Ready</span>
            </div>
          </div>
          
          {/* Animated Bird Vector illustration */}
          <div className="hidden lg:block relative h-40 w-40 opacity-20 origin-center animate-pulse pointer-events-none">
            <svg viewBox="0 0 100 100" fill="none" className="h-full w-full">
              <path d="M 50 10 L 60 40 L 55 70 L 45 70 L 40 40 Z" fill="url(#left-bird-grad)" />
              <path d="M 50 40 Q 20 20 10 40 Q 30 45 50 50 Z" fill="url(#left-bird-grad)" />
              <path d="M 50 40 Q 80 20 90 40 Q 70 45 50 50 Z" fill="url(#left-bird-grad)" />
              <defs>
                <linearGradient id="left-bird-grad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="100%" stopColor="#6366f1" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* ── Right Side: Glassmorphic Floating Console Card ───────── */}
        <div className="relative w-full max-w-[440px] rounded-2xl glass border-indigo-500/15 shadow-[0_0_60px_rgba(99,102,241,0.08)] backdrop-blur-2xl">
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/25 to-transparent rounded-t-2xl" />

          <div className="absolute -top-4.5 left-1/2 -translate-x-1/2">
            <div className="flex items-center gap-2 rounded-full border border-indigo-500/20 bg-[#09090b] px-4 py-1.5 shadow-xl">
              <div className="flex h-5 w-5 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500">
                <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" className="h-3 w-3">
                  <path d="M12 2L2 22l10-6 10 6L12 2z" />
                </svg>
              </div>
              <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-300 uppercase">Nexora AI</span>
            </div>
          </div>

          <div className="px-8 py-10 pt-12 md:px-10">
            <div className="mb-6">
              <h2 className="text-xl font-bold tracking-tight text-white font-playfair md:text-2xl" style={{ fontFamily: "'Playfair Display', serif" }}>
                {isRegister ? "Sign Up" : "Sign In"}
              </h2>
              <p className="mt-1.5 text-xs text-zinc-500">
                {isRegister ? "Create a new Nexora AI account to get started." : "Welcome back! Please enter your details."}
              </p>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400 animate-fade-in-up">
                <ShieldAlert className="h-4.5 w-4.5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div className="space-y-1.5">
                  <label className="block text-[9px] font-bold uppercase tracking-wider text-zinc-500">Full Name</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-650" />
                    <input 
                      type="text" 
                      value={fullName} 
                      onChange={(e) => setFullName(e.target.value)} 
                      placeholder="Vishvam Prajapati" 
                      disabled={loading}
                      className="input-glow w-full rounded-xl border border-zinc-800 bg-zinc-950/60 py-2.5 pl-10 pr-4 text-sm text-white placeholder-zinc-700 outline-none transition" 
                    />
                  </div>
                </div>
              )}

              <div className="space-y-1.5">
                <label className="block text-[9px] font-bold uppercase tracking-wider text-zinc-500">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-650" />
                  <input 
                    type="email" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    placeholder="name@enterprise.ai" 
                    disabled={loading}
                    className="input-glow w-full rounded-xl border border-zinc-800 bg-zinc-950/60 py-2.5 pl-10 pr-4 text-sm text-white placeholder-zinc-700 outline-none transition" 
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-[9px] font-bold uppercase tracking-wider text-zinc-500">Password</label>
                  {!isRegister && (
                    <button 
                      type="button" 
                      onClick={() => setError("Password reset is not configured for this enterprise node. Please contact your system administrator.")}
                      className="text-[10px] text-indigo-400 hover:text-indigo-300 transition"
                    >
                      Forgot Password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-655" />
                  <input 
                    type={showPassword ? "text" : "password"} 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)} 
                    placeholder="••••••••" 
                    disabled={loading}
                    className="input-glow w-full rounded-xl border border-zinc-800 bg-zinc-950/60 py-2.5 pl-10 pr-10 text-sm text-white placeholder-zinc-700 outline-none transition" 
                  />
                  <button 
                    type="button" 
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400 transition"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {isRegister && (
                <div className="space-y-1.5">
                  <label className="block text-[9px] font-bold uppercase tracking-wider text-zinc-500">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-655" />
                    <input 
                      type={showConfirmPassword ? "text" : "password"} 
                      value={confirmPassword} 
                      onChange={(e) => setConfirmPassword(e.target.value)} 
                      placeholder="••••••••" 
                      disabled={loading}
                      className="input-glow w-full rounded-xl border border-zinc-800 bg-zinc-950/60 py-2.5 pl-10 pr-10 text-sm text-white placeholder-zinc-700 outline-none transition" 
                    />
                    <button 
                      type="button" 
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-zinc-400 transition"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}

              <button 
                type="submit" 
                disabled={loading}
                className="btn-primary relative flex w-full items-center justify-center gap-2 rounded-xl py-3 text-xs font-bold tracking-wider uppercase transition mt-2 disabled:opacity-40"
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : isRegister ? (
                  <><UserPlus className="h-4 w-4" /><span>Sign Up</span></>
                ) : (
                  <><LogIn className="h-4 w-4" /><span>Sign In</span></>
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-xs text-zinc-500">
              {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
              <button 
                onClick={() => { setError(null); setIsRegister(!isRegister); }} 
                disabled={loading}
                className="font-bold text-indigo-400 hover:text-indigo-300 transition focus:outline-none"
              >
                {isRegister ? "Sign In" : "Sign Up"}
              </button>
            </div>

          </div>
        </div>

      </div>

      <div className="absolute bottom-4 left-6 text-[10px] text-zinc-700 tracking-wider hidden md:block">
        © 2026 Nexora AI · RAG & Fine-Tuning Console Port
      </div>
      <div className="absolute bottom-4 right-6 text-[10px] text-zinc-700 tracking-widest uppercase hidden md:block">
        SECURE NODE V1.0.0
      </div>
    </div>
  );
}
