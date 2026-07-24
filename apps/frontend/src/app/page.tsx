"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { 
  Shield, Cpu, Users, BarChart3, ChevronRight, 
  ExternalLink, Mail, Phone, Globe, Info, Play, CheckCircle2 
} from "lucide-react";

// Google Fonts loader via standard link injection to support serif headers
const FontLoader = () => (
  <style jsx global>{`
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Playfair+Display:ital,wght@0,600;0,800;1,600&display=swap');
    
    .font-outfit {
      font-family: 'Outfit', sans-serif;
    }
    .font-playfair {
      font-family: 'Playfair Display', serif;
    }
    .text-glow-blue {
      text-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }
    .glass-card {
      background: rgba(24, 24, 27, 0.4);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(39, 39, 42, 0.5);
    }
    .glass-card-hover:hover {
      border-color: rgba(99, 102, 241, 0.3);
      box-shadow: 0 0 30px rgba(99, 102, 241, 0.1);
    }
  `}</style>
);

// ── 3D Bird Boid Type ────────────────────────────────────────────────
interface Boid {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  wingPhase: number;
  wingSpeed: number;
  size: number;
  color: string;
}

export default function BluebirdLanding() {
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  
  // Modal & Interactive states
  const [activeModal, setActiveModal] = useState<"solutions" | "contact" | "resources" | null>(null);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false });

  // ── 3D Boids Simulation Setup ───────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    // Initialize 45 3D Boids
    const boids: Boid[] = Array.from({ length: 45 }, () => {
      const angle = Math.random() * Math.PI * 2;
      const speed = 1.5 + Math.random() * 2;
      return {
        x: (Math.random() - 0.5) * width * 0.8,
        y: (Math.random() - 0.5) * height * 0.8,
        z: Math.random() * 300 - 150,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        vz: (Math.random() - 0.5) * 1.5,
        wingPhase: Math.random() * Math.PI * 2,
        wingSpeed: 0.15 + Math.random() * 0.1,
        size: 3.5 + Math.random() * 2,
        color: Math.random() > 0.4 ? "rgba(99, 102, 241, 0.75)" : "rgba(34, 211, 238, 0.75)",
      };
    });

    const focalLength = 350;

    // Track mouse coordinates relative to canvas center
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current.x = e.clientX - width / 2;
      mouseRef.current.y = e.clientY - height / 2;
      mouseRef.current.active = true;
    };
    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);

    // Main animation loop
    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw faint, soft background radial glow following mouse
      if (mouseRef.current.active) {
        const mx = mouseRef.current.x + width / 2;
        const my = mouseRef.current.y + height / 2;
        const glow = ctx.createRadialGradient(mx, my, 10, mx, my, 400);
        glow.addColorStop(0, "rgba(99, 102, 241, 0.05)");
        glow.addColorStop(1, "rgba(9, 9, 11, 0)");
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, width, height);
      }

      // Update and Draw Boids
      boids.forEach((b) => {
        // --- 1. Flocking Algorithm (Rules of Alignment, Cohesion, Separation) ---
        let avgVx = 0, avgVy = 0, avgVz = 0;
        let avgX = 0, avgY = 0, avgZ = 0;
        let closeDx = 0, closeDy = 0, closeDz = 0;
        let neighborsCount = 0;

        boids.forEach((other) => {
          if (other === b) return;
          const dx = other.x - b.x;
          const dy = other.y - b.y;
          const dz = other.z - b.z;
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

          if (dist < 150) {
            avgVx += other.vx;
            avgVy += other.vy;
            avgVz += other.vz;
            avgX += other.x;
            avgY += other.y;
            avgZ += other.z;
            neighborsCount++;

            // Separation force
            if (dist < 40) {
              closeDx -= dx * (2.5 / (dist + 0.1));
              closeDy -= dy * (2.5 / (dist + 0.1));
              closeDz -= dz * (2.5 / (dist + 0.1));
            }
          }
        });

        // Apply flock rules if neighbors exist
        if (neighborsCount > 0) {
          avgVx /= neighborsCount;
          avgVy /= neighborsCount;
          avgVz /= neighborsCount;
          avgX /= neighborsCount;
          avgY /= neighborsCount;
          avgZ /= neighborsCount;

          // Steering factors
          b.vx += (avgVx - b.vx) * 0.02; // Align
          b.vy += (avgVy - b.vy) * 0.02;
          b.vz += (avgVz - b.vz) * 0.02;

          b.vx += (avgX - b.x) * 0.0005; // Cohesion
          b.vy += (avgY - b.y) * 0.0005;
          b.vz += (avgZ - b.z) * 0.0005;
        }

        b.vx += closeDx * 0.15; // Separation
        b.vy += closeDy * 0.15;
        b.vz += closeDz * 0.15;

        // --- 2. Mouse Attractor Pull ---
        if (mouseRef.current.active) {
          const mDx = mouseRef.current.x - b.x;
          const mDy = mouseRef.current.y - b.y;
          const mDist = Math.sqrt(mDx * mDx + mDy * mDy);
          if (mDist < 450) {
            b.vx += mDx * 0.0008;
            b.vy += mDy * 0.0008;
          }
        }

        // Limit maximum speed
        const speed = Math.sqrt(b.vx * b.vx + b.vy * b.vy + b.vz * b.vz);
        const maxSpeed = 3.5;
        if (speed > maxSpeed) {
          b.vx = (b.vx / speed) * maxSpeed;
          b.vy = (b.vy / speed) * maxSpeed;
          b.vz = (b.vz / speed) * maxSpeed;
        }

        // --- 3. Update Positions & Flap Wings ---
        b.x += b.vx;
        b.y += b.vy;
        b.z += b.vz;
        b.wingPhase += b.wingSpeed;

        // Boundary wrapping (Smooth toroidal space wrap)
        const borderX = width / 2 + 100;
        const borderY = height / 2 + 100;
        if (b.x > borderX) b.x = -borderX;
        else if (b.x < -borderX) b.x = borderX;
        
        if (b.y > borderY) b.y = -borderY;
        else if (b.y < -borderY) b.y = borderY;

        if (b.z > 200) b.z = -150;
        else if (b.z < -150) b.z = 200;

        // --- 4. Render Projected Boid Shape ---
        const scale = focalLength / (focalLength + b.z);
        const px = width / 2 + b.x * scale;
        const py = height / 2 + b.y * scale;

        // Normalize 2D direction vectors
        const speed2D = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
        const dx = b.vx / (speed2D + 0.01);
        const dy = b.vy / (speed2D + 0.01);

        // Normal vector for wing extension
        const nx = -dy;
        const ny = dx;

        const size = b.size * scale;
        const wingSpan = size * (1.3 + Math.sin(b.wingPhase) * 0.7);

        // Define bird shape points
        const headX = px + dx * size * 2.2;
        const headY = py + dy * size * 2.2;
        const tailX = px - dx * size * 1.5;
        const tailY = py - dy * size * 1.5;
        const leftWingX = px - dx * size * 0.4 + nx * wingSpan;
        const leftWingY = py - dy * size * 0.4 + ny * wingSpan;
        const rightWingX = px - dx * size * 0.4 - nx * wingSpan;
        const rightWingY = py - dy * size * 0.4 - ny * wingSpan;

        // Draw bird path
        ctx.beginPath();
        ctx.moveTo(headX, headY);
        ctx.lineTo(leftWingX, leftWingY);
        ctx.lineTo(px - dx * size * 0.5, py - dy * size * 0.5); // Center indent
        ctx.lineTo(rightWingX, rightWingY);
        ctx.closePath();

        // Calculate opacity based on Z depth
        const depthOpacity = Math.max(0.12, Math.min(0.9, (b.z + 150) / 350));
        ctx.fillStyle = b.color.replace("0.75", depthOpacity.toString());
        ctx.fill();

        // Draw smooth glowing tail trace
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(tailX, tailY);
        ctx.strokeStyle = `rgba(99, 102, 241, ${depthOpacity * 0.25})`;
        ctx.lineWidth = 1 * scale;
        ctx.stroke();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="relative font-outfit min-h-screen w-full bg-[#09090b] text-[#f4f4f5] overflow-x-hidden select-none">
      <FontLoader />

      {/* ── 3D Canvas Interactive Background ──────────────────────────── */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 z-0 pointer-events-none opacity-80"
      />

      {/* Background soft glow rings */}
      <div className="absolute top-[20%] left-[-10%] h-[600px] w-[600px] rounded-full bg-indigo-600/5 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[10%] right-[-10%] h-[500px] w-[500px] rounded-full bg-cyan-600/5 blur-[100px] pointer-events-none"></div>

      {/* ── Top Navigation Header ─────────────────────────────────────── */}
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 md:px-12">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => router.push("/")}>
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 shadow-lg shadow-indigo-500/20">
            {/* Minimalist Bird SVG Icon */}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-4.5 w-4.5 text-white">
              <path d="M12 2L2 22l10-6 10 6L12 2z" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="text-sm font-bold tracking-[0.15em] uppercase text-white">Nexora AI</span>
        </div>

        {/* Desktop Navbar menu */}
        <nav className="hidden md:flex items-center gap-8 text-[11px] font-semibold tracking-widest text-zinc-500 uppercase">
          <a href="#hero" className="text-white hover:text-white transition-colors">home</a>
          <a href="#" onClick={(e) => { e.preventDefault(); setActiveModal("solutions"); }} className="hover:text-white transition-colors">services</a>
          <a href="#" onClick={(e) => { e.preventDefault(); setActiveModal("resources"); }} className="hover:text-white transition-colors">resources</a>
          <a href="#" onClick={(e) => { e.preventDefault(); setActiveModal("contact"); }} className="hover:text-white transition-colors">contact</a>
        </nav>

        {/* CTA Login/Signup Buttons */}
        <div className="flex items-center gap-2">
          <button 
            onClick={() => router.push("/login")}
            className="rounded-full border border-zinc-700 bg-zinc-900/50 px-4 py-1.5 text-[11px] font-semibold tracking-wider text-zinc-300 transition-all hover:border-indigo-500 hover:text-white"
          >
            Sign In
          </button>
          <button 
            onClick={() => router.push("/login")}
            className="rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-1.5 text-[11px] font-semibold tracking-wider text-white transition-all hover:from-indigo-500 hover:to-violet-500 shadow-lg shadow-indigo-900/30"
          >
            Get Started
          </button>
        </div>
      </header>

      {/* ── Main Hero Layout ─────────────────────────────────────────── */}
      <main className="relative z-10 mx-auto flex max-w-7xl flex-col items-center px-6 py-12 md:px-12 lg:flex-row lg:py-24">
        
        {/* Large Backdrop Serif Text */}
        <div className="absolute inset-x-0 top-[10%] -z-10 text-center select-none pointer-events-none opacity-[0.03]" id="hero">
          <h1 className="font-playfair text-[9rem] md:text-[18rem] font-extrabold tracking-widest text-white leading-none uppercase">
            Nexora
          </h1>
        </div>

        {/* ── Left Grid: Hero Headlines & CTA ──────────────────────────── */}
        <div className="flex flex-1 flex-col justify-center text-center lg:text-left">
          {/* Tagline badge */}
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-[10px] font-semibold tracking-widest text-indigo-400 uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse"></span>
            Enterprise AI Platform · v1.0
          </div>

          <h2 className="font-playfair text-4xl font-extrabold tracking-tight text-white sm:text-6xl lg:text-[72px] leading-[1.05]">
            Intelligent <br className="hidden lg:block" />
            <span className="text-glow-blue bg-gradient-to-r from-indigo-400 via-violet-300 to-cyan-300 bg-clip-text text-transparent">
              AI agents.
            </span>
          </h2>
          <p className="mt-6 max-w-md text-sm leading-relaxed text-zinc-400 mx-auto lg:mx-0">
            Nexora AI is your all-in-one enterprise workspace — build, train, evaluate and deploy fine-tuned LLMs with a built-in RAG pipeline, multi-agent automation, and continuous learning dashboard.
          </p>

          {/* Feature pills */}
          <div className="mt-5 flex flex-wrap gap-2 justify-center lg:justify-start">
            {["RAG Search", "ML Studio", "AI Agents", "QLoRA Fine-Tuning", "Eval Dashboard"].map((tag) => (
              <span key={tag} className="rounded-full border border-zinc-800 bg-zinc-900/50 px-3 py-1 text-[10px] font-medium text-zinc-400">
                {tag}
              </span>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4 lg:justify-start">
            <button 
              onClick={() => router.push("/login")}
              className="group flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-violet-700 px-7 py-3.5 text-xs font-semibold tracking-wider text-white shadow-lg shadow-indigo-900/40 transition-all hover:scale-[1.02] hover:from-indigo-500 hover:to-violet-600"
            >
              <span>Sign In</span>
              <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>

            <button 
              onClick={() => router.push("/login")}
              className="rounded-full border border-zinc-700 bg-zinc-900/20 px-7 py-3.5 text-xs font-semibold tracking-wider text-zinc-300 hover:border-indigo-500 hover:text-white transition-all"
            >
              Create Account →
            </button>
          </div>
        </div>

        {/* ── Center Grid: Animated Neon Bird SVG & Glassmorphic Cards ── */}
        <div className="relative mt-16 flex flex-1 items-center justify-center lg:mt-0">
          
          {/* Animated Wing-Flapping SVG Bluebird */}
          <div className="relative z-10 flex h-[350px] w-[350px] md:h-[450px] md:w-[450px] items-center justify-center">
            {/* Ambient Backlight Aura */}
            <div className="absolute h-56 w-56 rounded-full bg-indigo-500/10 blur-[80px]"></div>

            <svg viewBox="0 0 400 400" className="h-full w-full overflow-visible drop-shadow-[0_0_35px_rgba(99,102,241,0.3)]">
              {/* Outer cyber ring */}
              <circle cx="200" cy="200" r="140" stroke="rgba(99, 102, 241, 0.12)" strokeWidth="1.5" fill="none" strokeDasharray="5 15" className="animate-spin" style={{ animationDuration: '30s' }} />
              <circle cx="200" cy="200" r="110" stroke="rgba(34, 211, 238, 0.08)" strokeWidth="1" fill="none" />

              {/* Glowing Neon Cyber-Bird vector lines */}
              <g className="translate-y-[-10px]">
                {/* Glowing Tail */}
                <path d="M 200 240 L 200 320 L 190 280 L 200 240 Z" fill="url(#cyan-glow)" opacity="0.85" />
                <path d="M 200 240 L 185 310 L 195 270 L 200 240 Z" fill="url(#indigo-glow)" opacity="0.6" />
                <path d="M 200 240 L 215 310 L 205 270 L 200 240 Z" fill="url(#indigo-glow)" opacity="0.6" />

                {/* Left Wing (Animated flapping using simple transform rotation) */}
                <g className="origin-center animate-pulse" style={{ transformOrigin: '200px 180px' }}>
                  <path d="M 200 180 Q 120 100 80 150 Q 140 180 200 200 Z" fill="url(#bluebird-gradient-left)" opacity="0.9" />
                  <path d="M 200 180 Q 140 120 110 160 Q 160 180 200 200 Z" fill="url(#cyan-glow)" opacity="0.4" />
                </g>

                {/* Right Wing (Animated flapping) */}
                <g className="origin-center animate-pulse" style={{ transformOrigin: '200px 180px' }}>
                  <path d="M 200 180 Q 280 100 320 150 Q 260 180 200 200 Z" fill="url(#bluebird-gradient-right)" opacity="0.9" />
                  <path d="M 200 180 Q 260 120 290 160 Q 240 180 200 200 Z" fill="url(#cyan-glow)" opacity="0.4" />
                </g>

                {/* Sleek Geometric Bird Body */}
                <path d="M 200 120 L 215 170 L 210 240 L 190 240 L 185 170 Z" fill="url(#bluebird-body)" />
                <path d="M 200 120 L 200 240 L 185 170 Z" fill="rgba(255, 255, 255, 0.08)" />

                {/* Glowing Crown Beak */}
                <path d="M 200 100 L 205 120 L 195 120 Z" fill="#22d3ee" className="animate-pulse" />

                {/* Eye dot */}
                <circle cx="200" cy="140" r="2.5" fill="#ffffff" />
                <circle cx="200" cy="140" r="5" stroke="#22d3ee" strokeWidth="0.5" fill="none" className="animate-ping" style={{ animationDuration: '2s' }} />
              </g>

              {/* Gradients definitions */}
              <defs>
                <linearGradient id="bluebird-gradient-left" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="50%" stopColor="#4f46e5" />
                  <stop offset="100%" stopColor="#09090b" />
                </linearGradient>
                <linearGradient id="bluebird-gradient-right" x1="1" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="50%" stopColor="#4f46e5" />
                  <stop offset="100%" stopColor="#09090b" />
                </linearGradient>
                <linearGradient id="bluebird-body" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" />
                  <stop offset="40%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#312e81" />
                </linearGradient>
                <linearGradient id="cyan-glow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="indigo-glow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          {/* ── Floating Glassmorphic Cards (Matching Mockups) ────────────── */}
          
          {/* Card 1: RAG Pipeline (Bottom Left) */}
          <div 
            onMouseEnter={() => setHoveredCard(1)}
            onMouseLeave={() => setHoveredCard(null)}
            className={`absolute bottom-[10%] left-[-4%] z-20 w-52 rounded-2xl p-4 glass-card glass-card-hover transition-all duration-300 ${
              hoveredCard === 1 ? "translate-y-[-4px]" : ""
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div>
                <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-[9px] font-semibold text-indigo-400">
                  RAG Pipeline
                </span>
                <p className="mt-1.5 text-[11px] font-semibold text-zinc-100 leading-snug">
                  Grounded answers from your docs
                </p>
              </div>
            </div>
          </div>

          {/* Card 2: Fine-Tuning Agent (Bottom Center-Right) */}
          <div 
            onMouseEnter={() => setHoveredCard(2)}
            onMouseLeave={() => setHoveredCard(null)}
            className={`absolute bottom-[-5%] right-[10%] z-20 w-56 rounded-2xl p-4 glass-card glass-card-hover transition-all duration-300 ${
              hoveredCard === 2 ? "translate-y-[-4px]" : ""
            }`}
          >
            <div className="flex items-center gap-3.5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 animate-pulse">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <span className="rounded-full bg-violet-500/10 px-2 py-0.5 text-[9px] font-semibold text-violet-400">
                  QLoRA Fine-Tuning
                </span>
                <p className="mt-1.5 text-[10px] text-zinc-400 leading-normal">
                  Train Nexora locally on your domain data.
                </p>
              </div>
            </div>
          </div>

          {/* Card 3: Model Accuracy Stats (Center Right) */}
          <div 
            onMouseEnter={() => setHoveredCard(3)}
            onMouseLeave={() => setHoveredCard(null)}
            className={`absolute top-[40%] right-[-10%] z-20 w-56 rounded-2xl p-4 glass-card glass-card-hover transition-all duration-300 ${
              hoveredCard === 3 ? "translate-y-[-4px]" : ""
            }`}
          >
            <div className="flex flex-col">
              <div className="flex items-baseline gap-1.5 text-glow-blue">
                <span className="text-3xl font-bold tracking-tight text-white font-playfair">94%</span>
                <span className="text-[10px] text-emerald-400 font-bold">&#9650; model accuracy</span>
              </div>
              <p className="mt-2 text-[10px] text-zinc-400 leading-relaxed">
                Nexora fine-tuned on your data achieves state-of-the-art results with minimal GPU cost.
              </p>
            </div>
          </div>

          {/* Card 4: Active Sessions (Top Right) */}
          <div 
            className="absolute top-[10%] right-[5%] z-20 flex items-center gap-3 rounded-full border border-zinc-800 bg-zinc-950/40 px-4 py-1.5 backdrop-blur-md"
          >
            <div className="flex -space-x-2">
              {["V", "A", "R"].map((initial, i) => (
                <div
                  key={i}
                  className="flex h-6 w-6 items-center justify-center rounded-full border border-[#09090b] text-[9px] font-bold text-white"
                  style={{ background: ["#6366f1", "#8b5cf6", "#22d3ee"][i] }}
                >
                  {initial}
                </div>
              ))}
            </div>
            <span className="text-[10px] font-semibold text-zinc-300 tracking-wider">
              Active Sessions <span className="text-white">+12</span>
            </span>
          </div>

        </div>
      </main>

      {/* ── Footer Elements ─────────────────────────────────────────── */}
      <footer className="relative z-10 mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 py-12 md:px-12 md:flex-row border-t border-zinc-900/60 mt-16 text-zinc-500">
        <div className="flex flex-col items-center gap-3 sm:flex-row">
          <div className="flex -space-x-2.5">
            {["#6366f1", "#8b5cf6", "#22d3ee", "#10b981"].map((color, i) => (
              <div
                key={i}
                className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-[#09090b] text-[9px] font-bold text-white"
                style={{ background: color }}
              >
                {["V", "A", "R", "K"][i]}
              </div>
            ))}
          </div>
          <span className="text-[11px] tracking-wide text-zinc-400">
            Trusted by enterprise AI teams
          </span>
        </div>

        <div className="text-[10px] text-zinc-600">
          © 2026 Nexora AI · Enterprise RAG & Fine-Tuning Platform
        </div>

        <div className="flex items-center gap-2">
          <span className="font-playfair text-2xl font-bold text-white text-glow-blue">4B+</span>
          <span className="text-[11px] tracking-widest uppercase text-zinc-500">Param Model</span>
        </div>
      </footer>

      {/* ── Active Modal Dialogs Overlay ─────────────────────────────── */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <div className="relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-[#09090b] p-6 shadow-2xl">
            <button 
              onClick={() => setActiveModal(null)}
              className="absolute right-4.5 top-4.5 rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-900 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            {activeModal === "solutions" && (
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Shield className="h-5 w-5 text-indigo-400" />
                  Nexora AI Platform Modules
                </h3>
                <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
                  A fully-integrated enterprise AI workspace — from file ingestion to fine-tuned model deployment, all running locally or on your cloud.
                </p>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  {[
                    { icon: "🔍", label: "RAG Chat Studio", desc: "Ground AI answers in your private docs" },
                    { icon: "🧠", label: "ML Training Studio", desc: "Train classifiers on your datasets" },
                    { icon: "📊", label: "Eval Dashboard", desc: "Faithfulness & hallucination scoring" },
                    { icon: "⚙️", label: "QLoRA Fine-Tuning", desc: "Fine-tune Nexora on domain data" },
                    { icon: "📋", label: "Report Studio", desc: "AI-generated analytics reports" },
                    { icon: "📧", label: "Email Agent", desc: "Context-aware email generation" },
                    { icon: "🐍", label: "Python Studio", desc: "Execute AI-assisted Python scripts" },
                    { icon: "📅", label: "Calendar Agent", desc: "Smart scheduling assistant" },
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-2.5 rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-3">
                      <span className="text-base">{item.icon}</span>
                      <div>
                        <div className="text-[11px] font-semibold text-white">{item.label}</div>
                        <div className="text-[9px] text-zinc-500 mt-0.5">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-5">
                  <button
                    onClick={() => { setActiveModal(null); router.push("/"); }}
                    className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 py-2.5 text-xs font-semibold text-white hover:from-indigo-500 hover:to-violet-500 transition-all"
                  >
                    Sign In to Access All Modules →
                  </button>
                </div>
              </div>
            )}

            {activeModal === "contact" && (
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Mail className="h-5 w-5 text-indigo-400" />
                  Get in Touch
                </h3>
                <p className="mt-2 text-xs text-zinc-400">
                  Ready to deploy secure AI infrastructure inside your enterprise network? Talk to our engineers.
                </p>
                <div className="mt-6 space-y-3.5">
                  <div className="flex items-center gap-3.5 text-xs text-zinc-300">
                    <Mail className="h-4.5 w-4.5 text-zinc-500" />
                    <span>enterprise@nexora.ai</span>
                  </div>
                  <div className="flex items-center gap-3.5 text-xs text-zinc-300">
                    <Phone className="h-4.5 w-4.5 text-zinc-500" />
                    <span>+1 (800) 555-NEXORA</span>
                  </div>
                  <div className="flex items-center gap-3.5 text-xs text-zinc-300">
                    <Globe className="h-4.5 w-4.5 text-zinc-500" />
                    <span>secure.nexora.ai</span>
                  </div>
                </div>
              </div>
            )}

            {activeModal === "resources" && (
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Info className="h-5 w-5 text-indigo-400" />
                  Documentation & Resources
                </h3>
                <p className="mt-2 text-xs text-zinc-400 leading-relaxed">
                  Access our latest security reports, API documentation, and implementation blueprints to see how to run local QLoRA workflows.
                </p>
                <div className="mt-5 grid grid-cols-2 gap-3.5">
                  {[
                    { label: "Developer Guide", desc: "API schema definitions & CLI parameters" },
                    { label: "Deployment Blueprint", desc: "Docker & Kubernetes cluster templates" },
                    { label: "Security Whitepaper", desc: "Data isolation, RAG guardrails & encryption" },
                    { label: "ML Model Card", desc: "Dataset structure, LoRA adapters & weights" }
                  ].map((res, i) => (
                    <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 hover:border-zinc-700 transition-colors cursor-pointer">
                      <div className="text-[11px] font-bold text-white flex items-center gap-1">
                        {res.label} <ExternalLink className="h-3 w-3 text-zinc-500" />
                      </div>
                      <div className="text-[9px] text-zinc-500 mt-1">{res.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setActiveModal(null)}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-semibold text-white hover:bg-zinc-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const X = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
