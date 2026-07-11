"use client";

import { useEffect, useRef, useState } from "react";

interface NexoraLoaderProps {
  message?: string;
  subMessage?: string;
}

export default function NexoraLoader({ 
  message = "Initializing workspace...",
  subMessage = "Syncing models & knowledge nodes"
}: NexoraLoaderProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [progress, setProgress] = useState(0);
  const [textPhase, setTextPhase] = useState(0);

  const loadingMessages = [
    "Initializing workspace...",
    "Loading AI models...",
    "Syncing knowledge nodes...",
    "Connecting to pipeline...",
    "Almost ready...",
  ];

  // Fake progress bar animation
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) { clearInterval(interval); return prev; }
        return prev + Math.random() * 8;
      });
    }, 180);
    return () => clearInterval(interval);
  }, []);

  // Cycle through loading messages
  useEffect(() => {
    const interval = setInterval(() => {
      setTextPhase((prev) => (prev + 1) % loadingMessages.length);
    }, 1200);
    return () => clearInterval(interval);
  }, []);

  // Boids background (smaller, fewer birds for loading screen)
  useEffect(() => {
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

    interface Boid { x: number; y: number; vx: number; vy: number; phase: number; }
    
    const boids: Boid[] = Array.from({ length: 25 }, () => {
      const a = Math.random() * Math.PI * 2;
      const s = 0.8 + Math.random() * 1.5;
      return {
        x: (Math.random() - 0.5) * W,
        y: (Math.random() - 0.5) * H,
        vx: Math.cos(a) * s,
        vy: Math.sin(a) * s,
        phase: Math.random() * Math.PI * 2,
      };
    });

    const tick = () => {
      ctx.clearRect(0, 0, W, H);

      boids.forEach((b) => {
        let avgVx = 0, avgVy = 0, avgX = 0, avgY = 0, closeDx = 0, closeDy = 0, n = 0;
        boids.forEach((o) => {
          if (o === b) return;
          const dx = o.x - b.x, dy = o.y - b.y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 120) {
            avgVx += o.vx; avgVy += o.vy;
            avgX += o.x; avgY += o.y; n++;
            if (d < 35) { closeDx -= dx * (2 / (d + 0.1)); closeDy -= dy * (2 / (d + 0.1)); }
          }
        });
        if (n > 0) {
          b.vx += ((avgVx / n) - b.vx) * 0.02 + ((avgX / n) - b.x) * 0.0004;
          b.vy += ((avgVy / n) - b.vy) * 0.02 + ((avgY / n) - b.y) * 0.0004;
        }
        b.vx += closeDx * 0.12;
        b.vy += closeDy * 0.12;
        const spd = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
        if (spd > 2.5) { b.vx = (b.vx / spd) * 2.5; b.vy = (b.vy / spd) * 2.5; }
        b.x += b.vx; b.y += b.vy; b.phase += 0.14;
        if (b.x > W / 2 + 80) b.x = -W / 2 - 80;
        if (b.x < -W / 2 - 80) b.x = W / 2 + 80;
        if (b.y > H / 2 + 80) b.y = -H / 2 - 80;
        if (b.y < -H / 2 - 80) b.y = H / 2 + 80;

        const s2 = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
        const dx = b.vx / (s2 + 0.01), dy = b.vy / (s2 + 0.01);
        const nx = -dy, ny = dx;
        const px = W / 2 + b.x, py = H / 2 + b.y;
        const sz = 3.2, ws = sz * (1.2 + Math.sin(b.phase) * 0.6);

        ctx.beginPath();
        ctx.moveTo(px + dx * sz * 2, py + dy * sz * 2);
        ctx.lineTo(px - dx * 0.3 + nx * ws, py - dy * 0.3 + ny * ws);
        ctx.lineTo(px - dx * 0.4, py - dy * 0.4);
        ctx.lineTo(px - dx * 0.3 - nx * ws, py - dy * 0.3 - ny * ws);
        ctx.closePath();
        ctx.fillStyle = `rgba(99, 102, 241, ${0.08 + Math.random() * 0.12})`;
        ctx.fill();
      });

      animId = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <div className="relative flex h-screen w-screen flex-col items-center justify-center overflow-hidden bg-[#09090b]">
      {/* Boids background canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Ambient glow blobs */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-indigo-600/6 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-[300px] w-[300px] rounded-full bg-violet-600/5 blur-[100px] pointer-events-none" />

      {/* Main loader content */}
      <div className="relative z-10 flex flex-col items-center gap-8">

        {/* Animated Logo Mark */}
        <div className="relative flex items-center justify-center">
          {/* Outer spinning ring */}
          <svg
            className="absolute h-28 w-28"
            viewBox="0 0 112 112"
            style={{ animation: "nexora-spin 8s linear infinite" }}
          >
            <circle
              cx="56" cy="56" r="50"
              stroke="url(#loader-ring-grad)"
              strokeWidth="1"
              fill="none"
              strokeDasharray="8 20"
            />
            <defs>
              <linearGradient id="loader-ring-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.2" />
              </linearGradient>
            </defs>
          </svg>

          {/* Inner counter-spin ring */}
          <svg
            className="absolute h-20 w-20"
            viewBox="0 0 80 80"
            style={{ animation: "nexora-spin 5s linear infinite reverse" }}
          >
            <circle
              cx="40" cy="40" r="36"
              stroke="rgba(139, 92, 246, 0.3)"
              strokeWidth="1"
              fill="none"
              strokeDasharray="3 14"
            />
          </svg>

          {/* Bird SVG center */}
          <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600/20 to-violet-600/10 border border-indigo-500/20 backdrop-blur-xl" style={{ animation: "float-y 3s ease-in-out infinite" }}>
            {/* Nexora Bird Icon */}
            <svg viewBox="0 0 40 40" className="h-9 w-9" fill="none">
              {/* Bird body */}
              <path d="M 20 4 L 24 16 L 22 30 L 18 30 L 16 16 Z" fill="url(#bird-body-loader)" />
              {/* Left wing */}
              <path d="M 20 16 Q 8 8 4 16 Q 12 18 20 20 Z" fill="url(#bird-left-loader)" opacity="0.9" />
              {/* Right wing */}
              <path d="M 20 16 Q 32 8 36 16 Q 28 18 20 20 Z" fill="url(#bird-right-loader)" opacity="0.9" />
              {/* Tail */}
              <path d="M 20 30 L 16 38 L 20 34 L 24 38 Z" fill="url(#bird-tail-loader)" opacity="0.7" />
              {/* Beak */}
              <path d="M 20 2 L 21.5 6 L 18.5 6 Z" fill="#22d3ee" />
              {/* Eye */}
              <circle cx="20" cy="12" r="1.5" fill="white" opacity="0.9" />

              <defs>
                <linearGradient id="bird-body-loader" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="50%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#4c1d95" />
                </linearGradient>
                <linearGradient id="bird-left-loader" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="100%" stopColor="#6366f1" />
                </linearGradient>
                <linearGradient id="bird-right-loader" x1="1" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="100%" stopColor="#6366f1" />
                </linearGradient>
                <linearGradient id="bird-tail-loader" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#4c1d95" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>

            {/* Pulse glow under icon */}
            <div className="absolute inset-0 rounded-2xl bg-indigo-500/10 animate-pulse" />
          </div>
        </div>

        {/* Brand Name */}
        <div className="text-center">
          <h1 className="font-playfair text-2xl font-bold text-white tracking-[0.15em] uppercase" style={{ fontFamily: "'Playfair Display', serif" }}>
            <span style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6, #22d3ee)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
              Nexora AI
            </span>
          </h1>
          <p className="mt-1 text-[10px] font-semibold tracking-[0.3em] uppercase text-zinc-500">
            Enterprise Intelligence Platform
          </p>
        </div>

        {/* Animated Loading Message */}
        <div className="flex flex-col items-center gap-3 min-h-[48px]">
          <p
            key={textPhase}
            className="text-sm font-medium text-zinc-400 tracking-wide animate-fade-in-up"
          >
            {loadingMessages[textPhase]}
          </p>

          {/* Progress bar */}
          <div className="relative h-[2px] w-56 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="absolute left-0 top-0 h-full rounded-full transition-all duration-300 ease-out"
              style={{
                width: `${Math.min(progress, 98)}%`,
                background: "linear-gradient(to right, #6366f1, #8b5cf6, #22d3ee)",
                boxShadow: "0 0 8px rgba(99,102,241,0.6)",
              }}
            />
            {/* Shimmer overlay */}
            <div className="absolute inset-0 animate-shimmer" />
          </div>

          {/* Dot loader row */}
          <div className="flex items-center gap-1.5">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-1 w-1 rounded-full bg-indigo-500"
                style={{
                  animation: `pulse-dot 1.2s ease-in-out infinite`,
                  animationDelay: `${i * 0.2}s`,
                }}
              />
            ))}
          </div>
        </div>

      </div>

      {/* Corner watermark */}
      <div className="absolute bottom-5 left-0 right-0 text-center text-[10px] tracking-widest uppercase text-zinc-700 pointer-events-none select-none">
        © 2026 Nexora AI · Enterprise RAG & Fine-Tuning Platform
      </div>
    </div>
  );
}
