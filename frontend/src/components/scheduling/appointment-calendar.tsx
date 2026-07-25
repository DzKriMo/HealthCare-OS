"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { Icons } from "@/components/icons";

interface ApptSummary {
  id: string; patient_name: string; practitioner_name: string;
  start_time: string; end_time: string; duration_minutes: number;
  type: string; status: string; room_name: string | null;
  color: string | null; practitioner: string;
}

const STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-100 border-l-blue-500 text-blue-800",
  confirmed: "bg-green-100 border-l-green-500 text-green-800",
  arrived: "bg-amber-100 border-l-amber-500 text-amber-800",
  in_progress: "bg-purple-100 border-l-purple-500 text-purple-800",
  completed: "bg-gray-100 border-l-gray-400 text-gray-600",
  cancelled: "bg-red-100 border-l-red-500 text-red-800 line-through",
  no_show: "bg-red-100 border-l-red-500 text-red-800",
};

function toDateStr(d: Date): string {
  return d.toISOString().split("T")[0];
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d); r.setDate(r.getDate() + n); return r;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function AppointmentCalendar() {
  const router = useRouter();
  const [view, setView] = useState<"day" | "week" | "month">("week");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [appointments, setAppointments] = useState<ApptSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<{ appointments: ApptSummary[]; range: { start: string; end: string } }>(
        `/appointments/calendar/?date=${toDateStr(currentDate)}&view=${view}`,
      );
      setAppointments(data.appointments);
    } catch { } finally { setLoading(false); }
  }, [currentDate, view]);

  useEffect(() => { load(); }, [load]);

  const nav = (dir: number) => {
    const d = new Date(currentDate);
    if (view === "day") d.setDate(d.getDate() + dir);
    else if (view === "week") d.setDate(d.getDate() + dir * 7);
    else d.setMonth(d.getMonth() + dir);
    setCurrentDate(d);
  };

  const days = getDays(currentDate, view);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setCurrentDate(new Date())}>Today</Button>
          <Button variant="ghost" size="sm" onClick={() => nav(-1)}><Icons.chevronDown className="h-4 w-4 rotate-90" /></Button>
          <Button variant="ghost" size="sm" onClick={() => nav(1)}><Icons.chevronDown className="h-4 w-4 -rotate-90" /></Button>
          <h2 className="text-lg font-semibold">
            {currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
            {view !== "month" && ` ${currentDate.toLocaleDateString("en-US", { day: "numeric" })}`}
          </h2>
        </div>
        <div className="flex gap-1">
          {(["day", "week", "month"] as const).map((v) => (
            <Button key={v} variant={view === v ? "default" : "outline"} size="sm" onClick={() => setView(v)}>
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      ) : view === "month" ? (
        <MonthView days={days} appointments={appointments} router={router} />
      ) : (
        <DayView days={days} appointments={appointments} router={router} />
      )}
    </div>
  );
}

function getDays(date: Date, view: string): Date[] {
  if (view === "day") return [date];
  if (view === "week") {
    const start = new Date(date);
    start.setDate(start.getDate() - start.getDay());
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }
  const start = new Date(date.getFullYear(), date.getMonth(), 1);
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  const days: Date[] = [];
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) days.push(new Date(d));
  return days;
}

function getApptsForDate(appts: ApptSummary[], date: Date): ApptSummary[] {
  const ds = toDateStr(date);
  return appts.filter((a) => a.start_time.startsWith(ds));
}

function MonthView({ days, appointments, router }: {
  days: Date[]; appointments: ApptSummary[]; router: ReturnType<typeof useRouter>;
}) {
  const firstDow = days[0].getDay();
  const pad = Array.from({ length: firstDow }, (_, i) => i);
  const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return (
    <Card>
      <CardContent className="p-2">
        <div className="grid grid-cols-7 gap-px">
          {DAYS.map((d) => (
            <div key={d} className="p-2 text-center text-xs font-medium text-muted-foreground">{d}</div>
          ))}
          {pad.map((i) => <div key={`pad-${i}`} />)}
          {days.map((d) => {
            const apps = getApptsForDate(appointments, d);
            const isToday = toDateStr(d) === toDateStr(new Date());
            return (
              <div key={d.toISOString()} className={`min-h-20 rounded-sm border p-1 ${isToday ? "bg-primary/5 border-primary/30" : ""}`}>
                <div className={`text-xs font-medium ${isToday ? "text-primary" : ""}`}>{d.getDate()}</div>
                <div className="space-y-0.5 mt-0.5">
                  {apps.slice(0, 3).map((a) => (
                    <div key={a.id}
                      className="cursor-pointer truncate rounded px-1 py-0.5 text-[10px] font-medium hover:opacity-80"
                      style={{ backgroundColor: a.color || "#e5e7eb" }}
                      onClick={() => router.push(`/appointments/${a.id}`)}
                    >{a.patient_name}</div>
                  ))}
                  {apps.length > 3 && <div className="text-[10px] text-muted-foreground">+{apps.length - 3} more</div>}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

const HOURS = Array.from({ length: 14 }, (_, i) => i + 7);

function DayView({ days, appointments, router }: {
  days: Date[]; appointments: ApptSummary[]; router: ReturnType<typeof useRouter>;
}) {
  const DAYS_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return (
    <Card>
      <CardContent className="p-2">
        <div className="grid grid-cols-[60px_repeat(auto-fill,minmax(0,1fr))]" style={{ gridTemplateColumns: `60px repeat(${days.length}, 1fr)` }}>
          <div />
          {days.map((d) => (
            <div key={d.toISOString()} className="p-1 text-center text-xs font-medium text-muted-foreground">
              {DAYS_SHORT[d.getDay()]} {d.getDate()}
            </div>
          ))}
          {HOURS.map((h) => (
            <>
              <div key={`h-${h}`} className="border-t p-1 text-right text-[10px] text-muted-foreground">
                {h.toString().padStart(2, "0")}:00
              </div>
              {days.map((d) => {
                const apps = getApptsForHour(appointments, d, h);
                return (
                  <div key={`${d.toISOString()}-${h}`} className="min-h-12 border-t border-dashed p-0.5">
                    {apps.map((a) => {
                      const color = STATUS_COLORS[a.status] || "bg-gray-100";
                      return (
                        <div key={a.id}
                          className={`cursor-pointer truncate rounded border-l-2 px-1 text-[10px] font-medium mb-0.5 hover:opacity-80 ${color}`}
                          onClick={() => router.push(`/appointments/${a.id}`)}
                        >
                          {formatTime(a.start_time)} {a.patient_name}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function getApptsForHour(appts: ApptSummary[], date: Date, hour: number): ApptSummary[] {
  const ds = toDateStr(date);
  return appts.filter((a) => {
    if (!a.start_time.startsWith(ds)) return false;
    const h = new Date(a.start_time).getHours();
    return h === hour;
  });
}
