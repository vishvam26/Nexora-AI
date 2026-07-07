"use client";

import { useState, useEffect, useCallback } from "react";
import { useChatStore } from "../stores/chat-store";
import {
  Calendar, Clock, AlertCircle, CheckCircle2,
  Users, CalendarDays, Sparkles, Send, Download,
  Loader2, Plus, Info, RefreshCw
} from "lucide-react";

import { API_BASE_URL } from "../services/api-service";

const API_BASE = API_BASE_URL;

interface CalendarEvent {
  id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  attendees?: string;
}

export default function CalendarStudio() {
  const { token } = useChatStore();

  // Booking states
  const [title, setTitle] = useState("Nexora Platform Alignment Sync");
  const [description, setDescription] = useState("Weekly multi-agent checkpoint review");
  
  // Format helpers to set tomorrow at 10:00 AM as initial start
  const getTomorrowDateStr = (offsetHours = 0) => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    d.setHours(10 + offsetHours, 0, 0, 0);
    // Format YYYY-MM-DD HH:MM
    const yr = d.getFullYear();
    const mo = String(d.getMonth() + 1).padStart(2, "0");
    const dy = String(d.getDate()).padStart(2, "0");
    const hr = String(d.getHours()).padStart(2, "0");
    const mn = String(d.getMinutes()).padStart(2, "0");
    return `${yr}-${mo}-${dy} ${hr}:${mn}`;
  };

  const [startTime, setStartTime] = useState(getTomorrowDateStr(0));
  const [endTime, setEndTime] = useState(getTomorrowDateStr(1));
  const [attendees, setAttendees] = useState("cfo@company.com, manager@company.com");

  // Scheduled events list states
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [booking, setBooking] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // AI Copilot state
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [scheduling, setScheduling] = useState(false);

  const headers = useCallback(() => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`
  }), [token]);

  const loadEvents = useCallback(async () => {
    setLoadingEvents(true);
    try {
      const res = await fetch(`${API_BASE}/calendar/events`, { headers: headers() });
      if (res.ok) setEvents(await res.json());
    } catch { /* ignore */ }
    setLoadingEvents(false);
  }, [headers]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const handleBookSlot = async () => {
    if (!title.trim() || !startTime.trim() || !endTime.trim()) {
      setErrorMsg("Subject title, start, and end times are required.");
      return;
    }

    setBooking(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await fetch(`${API_BASE}/calendar/schedule`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          title,
          description,
          start_time: startTime,
          end_time: endTime,
          attendees
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Overlap conflict detected.");
      }
      setSuccessMsg(`Slot successfully scheduled: ${title}.`);
      loadEvents();
    } catch (e: any) {
      setErrorMsg(e.message || "Overlap conflict or parsing error occurred.");
    } finally {
      setBooking(false);
    }
  };

  const handleAIScheduler = async () => {
    if (!naturalLanguage.trim()) return;
    setScheduling(true);
    try {
      const prompt = `Convert this natural language scheduling request to a valid JSON block: "${naturalLanguage}". Current date is ${new Date().toISOString().slice(0, 10)}. Format output ONLY as a JSON matching keys: {"title": "string", "start_time": "YYYY-MM-DD HH:MM", "end_time": "YYYY-MM-DD HH:MM", "attendees": "comma-separated emails", "description": "string"}. Return no comments, no markdown backticks.`;
      
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({
          conversation_id: 1, // Broad system fallback conversation
          content: prompt
        })
      });
      const data = await res.json();
      if (res.ok && data.content) {
        const cleanJSON = data.content.replace(/```json|```/g, "").trim();
        const parsed = JSON.parse(cleanJSON);
        if (parsed.title) setTitle(parsed.title);
        if (parsed.start_time) setStartTime(parsed.start_time);
        if (parsed.end_time) setEndTime(parsed.end_time);
        if (parsed.attendees) setAttendees(parsed.attendees);
        if (parsed.description) setDescription(parsed.description);
      }
    } catch { /* ignore */ }
    setScheduling(false);
  };

  const BACKEND_ROOT = API_BASE.replace("/api/v1", "");

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#09090b] text-[#f4f4f5]">
      {/* ── Left Panel: Form Booking Scheduler ──────────────────────── */}
      <div className="flex flex-1 flex-col border-r border-zinc-800 overflow-y-auto">
        <div className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20 border border-indigo-500/30">
              <Calendar className="h-4 w-4 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">Calendar Studio</h2>
              <p className="text-[10px] text-zinc-500">Plan & schedule meeting slots</p>
            </div>
          </div>

          <button
            onClick={handleBookSlot}
            disabled={booking}
            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50 transition"
          >
            {booking ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
            Book Slot
          </button>
        </div>

        <div className="flex flex-col gap-5 p-6">
          {/* Status Banners */}
          {successMsg && (
            <div className="flex items-start gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
              <p className="text-xs text-emerald-300">{successMsg}</p>
            </div>
          )}
          {errorMsg && (
            <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
              <p className="text-xs text-red-300">{errorMsg}</p>
            </div>
          )}

          {/* AI Scheduler Assistant */}
          <div className="flex items-center gap-2.5 rounded-xl border border-indigo-500/20 bg-indigo-500/5 px-4 py-2.5">
            <Sparkles className="h-4 w-4 text-indigo-400 shrink-0" />
            <input
              type="text"
              value={naturalLanguage}
              onChange={(e) => setNaturalLanguage(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleAIScheduler(); }}
              placeholder="Ask AI Scheduler (e.g. 'Schedule project sync tomorrow at 2 PM for 1 hour')"
              className="flex-1 bg-transparent text-xs text-zinc-200 placeholder:text-zinc-500 focus:outline-none"
            />
            <button
              onClick={handleAIScheduler}
              disabled={scheduling || !naturalLanguage.trim()}
              className="rounded p-1 text-indigo-400 hover:bg-indigo-500/10 disabled:opacity-30"
            >
              {scheduling ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </button>
          </div>

          {/* Form Fields */}
          <div className="flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Meeting Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Start Time</label>
                <input
                  type="text"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  placeholder="YYYY-MM-DD HH:MM"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none font-mono"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-zinc-500">End Time</label>
                <input
                  type="text"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  placeholder="YYYY-MM-DD HH:MM"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none font-mono"
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Attendees (Emails)</label>
              <input
                type="text"
                value={attendees}
                onChange={(e) => setAttendees(e.target.value)}
                placeholder="Comma separated emails"
                className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-200 focus:border-indigo-500 focus:outline-none resize-y"
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Right Panel: Scheduled Slots List ──────────────────────── */}
      <div className="flex w-96 shrink-0 flex-col bg-zinc-950/20 overflow-hidden">
        <div className="border-b border-zinc-800 px-5 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">Scheduled Slots</h2>
            <p className="text-[10px] text-zinc-500">Local calendar database</p>
          </div>
          <button onClick={loadEvents} className="rounded p-1 hover:bg-zinc-800 text-zinc-400">
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3">
          {loadingEvents ? (
            <div className="flex items-center gap-2 text-zinc-500 text-xs">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Loading appointments...
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12 text-zinc-600 text-xs flex flex-col items-center gap-3">
              <CalendarDays className="h-10 w-10 text-zinc-700" />
              <span>No scheduled slots booked yet.</span>
            </div>
          ) : (
            events.map((ev) => (
              <div key={ev.id} className="rounded-xl border border-zinc-800 bg-[#0d0d0e] p-4 flex flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-bold text-zinc-200">{ev.title}</h4>
                  <a
                    href={`${BACKEND_ROOT}/reports/event_${ev.id}.ics`}
                    download
                    className="flex h-6 w-6 items-center justify-center rounded border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800 text-zinc-400 hover:text-white transition shrink-0"
                    title="Download ICS File"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </a>
                </div>

                <div className="flex flex-col gap-1 text-[10px] text-zinc-500 font-mono">
                  <span className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-zinc-600" />
                    {ev.start_time} - {ev.end_time.split(" ")[1]}
                  </span>
                  {ev.attendees && (
                    <span className="flex items-start gap-1.5">
                      <Users className="h-3.5 w-3.5 text-zinc-600 mt-0.5 shrink-0" />
                      <span className="truncate max-w-[240px]">{ev.attendees}</span>
                    </span>
                  )}
                </div>

                {ev.description && (
                  <p className="mt-1 border-t border-zinc-900 pt-2 text-[10px] text-zinc-400 leading-relaxed">
                    {ev.description}
                  </p>
                )}
              </div>
            ))
          )}

          <div className="mt-auto flex gap-2 rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 text-[10px] text-zinc-500 leading-tight">
            <Info className="h-3.5 w-3.5 shrink-0 text-zinc-600" />
            <span>Slots are validated locally for overlap conflicts. Click the download icon to save a standard .ics file.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
