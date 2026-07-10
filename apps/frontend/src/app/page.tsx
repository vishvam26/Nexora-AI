"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "../stores/chat-store";
import { apiService } from "../services/api-service";
import { LogIn, UserPlus, ShieldAlert, Cpu, Eye, EyeOff, Lock, Mail, User } from "lucide-react";

export default function LampLoginPage() {
  const router = useRouter();
  const { token, setToken } = useChatStore();

  // Lamp & Pull String States
  const [isOn, setIsOn] = useState(false);
  const [isPulling, setIsPulling] = useState(false);

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

  // Initialize token from localStorage on mount
  useEffect(() => {
    const localToken = localStorage.getItem("nexora_token");
    if (localToken) {
      setToken(localToken);
    }
    setMounted(true);
  }, [setToken]);

  // Redirect to chat if logged in
  useEffect(() => {
    if (mounted && token) {
      router.push("/chat");
    }
  }, [token, mounted, router]);

  if (!mounted) {
    return null;
  }

  // Handle String Pull Trigger
  const handleStringPull = () => {
    if (isPulling) return;
    setIsPulling(true);
    // Snap back and toggle lamp state after 150ms
    setTimeout(() => {
      setIsPulling(false);
      setIsOn((prev) => !prev);
    }, 150);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // If lamp is off, guide the user to turn it on
    if (!isOn) {
      setError("Please pull the lamp string to turn on the workspace first!");
      return;
    }

    if (!email || !password || (isRegister && (!fullName || !confirmPassword))) {
      setError("Please fill in all fields.");
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

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
    <div
      className={`relative flex min-h-screen w-full flex-col md:flex-row items-center justify-center px-4 py-12 transition-all duration-1000 select-none overflow-hidden ${
        isOn
          ? "bg-[#0b0a0e] bg-[radial-gradient(circle_at_25%_40%,rgba(245,158,11,0.06)_0%,rgba(11,10,14,1)_70%)]"
          : "bg-[#030303]"
      }`}
    >
      {/* Decorative Grid Behind everything (only shines slightly when light is on) */}
      <div
        className={`absolute inset-0 z-0 bg-[linear-gradient(to_right,#1f1f23_1px,transparent_1px),linear-gradient(to_bottom,#1f1f23_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] transition-opacity duration-1000 ${
          isOn ? "opacity-20" : "opacity-5"
        }`}
      ></div>

      {/* Main Container splits Lamp and Card */}
      <div className="z-10 flex w-full max-w-[1150px] flex-col md:flex-row items-center justify-between gap-12 md:gap-8 px-4 md:px-12 mt-8">
        
        {/* Left Container - Interactive Lamp */}
        <div className="relative flex flex-col h-[380px] w-full max-w-[280px] md:h-[510px] md:max-w-[320px] items-center justify-center">
          {/* Subtle instruction above the lamp */}
          <div className="mb-2 text-center pointer-events-none select-none">
            <p className="text-zinc-500 text-[9px] md:text-[10px] font-semibold tracking-[0.25em] uppercase pulse-animation">
              {isOn ? "PULL STRING TO LOCK WORKSPACE" : "PULL THE STRING TO TOGGLE LOGIN"}
            </p>
          </div>
          <svg
            viewBox="0 0 320 480"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="h-full w-full overflow-visible"
          >
            <defs>
              {/* Radial bulb glow */}
              <radialGradient id="bulb-glow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="25%" stopColor="#fef08a" />
                <stop offset="100%" stopColor="#ca8a04" stopOpacity="0" />
              </radialGradient>

              {/* Volumetric Light Beam Gradient (Soft warm yellow fading out) */}
              <linearGradient id="beam-gradient" x1="0.5" y1="0" x2="0.8" y2="1">
                <stop offset="0%" stopColor="#fde047" stopOpacity="0.22" />
                <stop offset="40%" stopColor="#fef08a" stopOpacity="0.08" />
                <stop offset="100%" stopColor="#eab308" stopOpacity="0" />
              </linearGradient>

              {/* Dark Metallic Gradient for the base and pole */}
              <linearGradient id="metallic" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#27272a" />
                <stop offset="50%" stopColor="#52525b" />
                <stop offset="100%" stopColor="#18181b" />
              </linearGradient>

              {/* Gold Pull Chain/Knob Gradient */}
              <linearGradient id="gold-pull" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#d97706" />
                <stop offset="50%" stopColor="#fbbf24" />
                <stop offset="100%" stopColor="#92400e" />
              </linearGradient>

              {/* Shade Gradients (lit vs unlit) */}
              <linearGradient id="shade-on" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#fef08a" />
                <stop offset="100%" stopColor="#ca8a04" />
              </linearGradient>
              <linearGradient id="shade-off" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1f1f23" />
                <stop offset="100%" stopColor="#09090b" />
              </linearGradient>

              {/* Glow filter */}
              <filter id="glow-filter" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="15" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Volumetric Light Beam (Overflows to wash over the login card on the right) */}
            <g
              className={`transition-all duration-700 ease-in-out origin-top pointer-events-none ${
                isOn ? "opacity-100 scale-100" : "opacity-0 scale-95"
              }`}
            >
              {/* Main wide light beam projecting rightwards */}
              <polygon
                points="90,135 230,135 1200,480 -300,480"
                fill="url(#beam-gradient)"
                filter="url(#glow-filter)"
              />
              {/* Secondary hot-spot beam for center intensity */}
              <polygon
                points="120,135 200,135 800,480 -100,480"
                fill="url(#beam-gradient)"
                opacity="0.5"
              />
            </g>

            {/* Lamp Base */}
            <path
              d="M 110 440 C 110 430, 210 430, 210 440 Z"
              fill="url(#metallic)"
              stroke="#09090b"
              strokeWidth="2"
            />

            {/* Lamp Stand/Pole */}
            <line
              x1="160"
              y1="135"
              x2="160"
              y2="435"
              stroke="url(#metallic)"
              strokeWidth="7"
              strokeLinecap="round"
            />

            {/* Socket base */}
            <rect x="151" y="125" width="18" height="15" fill="#27272a" rx="1" />

            {/* Light Bulb & Ambient Glow (Visible under shade) */}
            <circle
              cx="160"
              cy="146"
              r="22"
              fill="url(#bulb-glow)"
              className={`transition-opacity duration-500 pointer-events-none ${
                isOn ? "opacity-100" : "opacity-0"
              }`}
            />
            <circle
              cx="160"
              cy="146"
              r="8"
              fill="#ffffff"
              className={`transition-opacity duration-300 pointer-events-none ${
                isOn ? "opacity-100" : "opacity-0"
              }`}
            />

            {/* Lamp Shade */}
            <path
              d="M 120 75 L 200 75 L 230 135 L 90 135 Z"
              fill={isOn ? "url(#shade-on)" : "url(#shade-off)"}
              stroke={isOn ? "#fef08a" : "#2e2e33"}
              strokeWidth="1.5"
              className="transition-all duration-300"
            />

            {/* Pull String & Knob */}
            <g
              style={{ transform: isPulling ? "translateY(16px)" : "translateY(0px)" }}
              className="transition-transform duration-150 ease-out"
            >
              {/* String (Chain effect via dasharray) */}
              <line
                x1="185"
                y1="135"
                x2="185"
                y2="235"
                stroke="#52525b"
                strokeWidth="1.5"
                strokeDasharray="2 3"
              />

              {/* Connection loop */}
              <circle cx="185" cy="138" r="2.5" fill="#18181b" />

              {/* Cylindrical Gold/Amber Pull Knob */}
              <rect
                x="181"
                y="235"
                width="8"
                height="22"
                rx="3.5"
                fill="url(#gold-pull)"
                stroke="#78350f"
                strokeWidth="1"
              />
              <circle cx="185" cy="253" r="2.5" fill="#f59e0b" />

              {/* Click target (Spans the lower string for high responsiveness) */}
              <rect
                x="170"
                y="135"
                width="30"
                height="145"
                fill="transparent"
                onClick={handleStringPull}
                className="cursor-pointer select-none"
              />
            </g>
          </svg>

          {/* Little floating text indicator when lamp is off */}
          {!isOn && (
            <div className="absolute top-[260px] left-[200px] text-zinc-500 text-[10px] tracking-wider pointer-events-none select-none animate-bounce flex items-center gap-1">
              <span>← Pull to turn ON</span>
            </div>
          )}
        </div>

        {/* Right Container - Login Form (With Glassmorphic styling matching light source) */}
        <div
          className={`relative w-full max-w-[430px] rounded-2xl border transition-all duration-700 ${
            isOn
              ? "bg-zinc-900/40 border-amber-500/20 shadow-[0_0_50px_rgba(250,204,21,0.1)] backdrop-blur-xl scale-100 opacity-100 pointer-events-auto"
              : "bg-zinc-950/5 border-zinc-900/50 shadow-none scale-[0.97] opacity-10 blur-sm pointer-events-none"
          }`}
        >
          {/* Card Glassmorphic Highlight Line */}
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-500/20 to-transparent"></div>

          <div className="px-8 py-10 md:px-10">
            {/* Header */}
            <div className="mb-8">
              <h2 className="text-xl font-bold tracking-tight text-white md:text-2xl">
                {isRegister ? "Welcome to Nexora AI" : "Welcome Back"}
              </h2>
              <p className="mt-1.5 text-xs md:text-sm text-zinc-400">
                {isRegister
                  ? "Create an account to deploy intelligent agents."
                  : "Sign in to access your workspaces."}
              </p>
            </div>

            {/* Error Message banner */}
            {error && (
              <div className="mb-6 flex items-start gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-3.5 text-xs text-red-400 transition-all duration-300">
                <ShieldAlert className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name input (Sign Up Only) */}
              {isRegister && (
                <div className="space-y-1.5">
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                    Full Name
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
                      <User className="h-4 w-4 text-zinc-500" />
                    </div>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="John Doe"
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-950/40 py-2.5 pl-10 pr-4 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30"
                      disabled={loading || !isOn}
                    />
                  </div>
                </div>
              )}

              {/* Email Address input */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                  Email address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
                    <Mail className="h-4 w-4 text-zinc-500" />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950/40 py-2.5 pl-10 pr-4 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30"
                    disabled={loading || !isOn}
                  />
                </div>
              </div>

              {/* Password input */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                    Password
                  </label>
                  {!isRegister && (
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        setError("Password reset is not configured for this enterprise node.");
                      }}
                      className="text-[11px] text-violet-400 hover:text-violet-300 transition focus:outline-none"
                    >
                      Forgot Password?
                    </a>
                  )}
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
                    <Lock className="h-4 w-4 text-zinc-500" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950/40 py-2.5 pl-10 pr-10 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30"
                    disabled={loading || !isOn}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3 text-zinc-500 hover:text-zinc-300 focus:outline-none"
                    disabled={!isOn}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password input (Sign Up Only) */}
              {isRegister && (
                <div className="space-y-1.5">
                  <label className="block text-[11px] font-semibold uppercase tracking-wider text-zinc-400">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
                      <Lock className="h-4 w-4 text-zinc-500" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-950/40 py-2.5 pl-10 pr-10 text-sm text-white placeholder-zinc-600 outline-none transition focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30"
                      disabled={loading || !isOn}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3 text-zinc-500 hover:text-zinc-300 focus:outline-none"
                      disabled={!isOn}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Primary CTA Submit Button */}
              <button
                type="submit"
                className="relative flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:from-violet-500 hover:to-indigo-500 focus:ring-2 focus:ring-indigo-500/50 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none mt-2"
                disabled={loading || !isOn}
              >
                {loading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                ) : isRegister ? (
                  <>
                    <UserPlus className="h-4 w-4" />
                    <span>SIGN UP</span>
                  </>
                ) : (
                  <>
                    <LogIn className="h-4 w-4" />
                    <span>SIGN IN</span>
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-6 flex items-center">
              <div className="flex-grow border-t border-zinc-800"></div>
              <span className="mx-4 shrink text-[10px] uppercase font-semibold text-zinc-600">or</span>
              <div className="flex-grow border-t border-zinc-800"></div>
            </div>

            {/* Google Authentication */}
            <button
              onClick={() => {
                if (!isOn) return;
                setError("Google Sign-In is temporarily disabled on this enterprise network.");
              }}
              className="flex w-full items-center justify-center gap-2.5 rounded-lg border border-zinc-800 bg-zinc-950/40 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-900/60 focus:outline-none focus:ring-1 focus:ring-zinc-700 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none"
              disabled={loading || !isOn}
            >
              {/* Google G SVG */}
              <svg className="h-4 w-4" viewBox="0 0 24 24" width="24" height="24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  fill="#EA4335"
                />
              </svg>
              <span>Continue with Google</span>
            </button>

            {/* Toggle Sign In vs Register */}
            <div className="mt-8 text-center text-xs md:text-sm text-zinc-400">
              {isRegister ? "Already have an account?" : "New to Nexora AI?"}{" "}
              <button
                onClick={() => {
                  if (!isOn) return;
                  setError(null);
                  setIsRegister(!isRegister);
                }}
                className="font-semibold text-violet-400 hover:text-violet-300 transition focus:outline-none focus:underline"
                disabled={loading || !isOn}
              >
                {isRegister ? "Sign In" : "Create one here"}
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* Floating corner branding info */}
      <div className="absolute bottom-4 left-4 text-[10px] text-zinc-600 select-none pointer-events-none hidden md:block">
        &copy; 2026 Nexora-AI. Enterprise AI Environment.
      </div>
      <div className="absolute bottom-4 right-4 text-[10px] text-zinc-600 select-none pointer-events-none hidden md:block">
        MIT License. Node v1.0.0
      </div>
    </div>
  );
}
