"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { Icons } from "@/components/icons";

interface QueueAppt {
  id: string; patient_name: string; practitioner_name: string;
  start_time: string; type: string; status: string;
  priority: string; room_name: string | null;
  wait_time_minutes: number | null; checked_in_at: string | null;
}

interface PractitionerQueue {
  practitioner_id: string; practitioner_name: string;
  appointments: QueueAppt[];
  stats: Record<string, number>;
}

const STATUS_BADGE: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  confirmed: "bg-green-100 text-green-800",
  arrived: "bg-amber-100 text-amber-800",
  in_progress: "bg-purple-100 text-purple-800",
  completed: "bg-gray-100 text-gray-600",
  no_show: "bg-red-100 text-red-800",
};

const POLL_INTERVAL = 30000;

export function QueueBoard() {
  const router = useRouter();
  const [queues, setQueues] = useState<PractitionerQueue[]>([]);
  const [total, setTotal] = useState(0);
  const [date, setDate] = useState("");
  const [loading, setLoading] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  const load = useCallback(async () => {
    try {
      const data = await api.get<{ queues: PractitionerQueue[]; total_appointments: number; date: string }>(
        "/appointments/queue/",
      );
      setQueues(data.queues);
      setTotal(data.total_appointments);
      setDate(data.date);
    } catch { } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    load();
    timerRef.current = setInterval(load, POLL_INTERVAL);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [load]);

  const transition = async (id: string, target: string) => {
    try {
      await api.post(`/appointments/${id}/transition/`, { target_status: target });
      await load();
    } catch { }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}><CardContent><div className="h-32 animate-pulse rounded-lg bg-muted" /></CardContent></Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Queue Board</h2>
          <p className="text-sm text-muted-foreground">{date} · {total} appointments today</p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          <Icons.search className="mr-1 h-4 w-4" /> Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {queues.map((q) => (
          <Card key={q.practitioner_id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{q.practitioner_name}</CardTitle>
                <span className="text-xs text-muted-foreground">{q.appointments.length} appts</span>
              </div>
              <div className="flex gap-1.5 text-xs">
                {Object.entries(q.stats).filter(([, v]) => v > 0).map(([k, v]) => (
                  <span key={k} className="rounded-full bg-primary/10 px-2 py-0.5">{k.replace("_", " ")}: {v}</span>
                ))}
              </div>
            </CardHeader>
            <CardContent className="space-y-1">
              {q.appointments.map((a) => {
                const isNext = a.status === "scheduled" || a.status === "confirmed";
                return (
                  <div key={a.id}
                    className={`flex items-center gap-2 rounded-lg border p-2 text-sm ${isNext ? "border-primary/30 bg-primary/5" : ""}`}>
                    <div className={`h-2 w-2 shrink-0 rounded-full ${a.status === "in_progress" ? "bg-purple-500 animate-pulse" : a.status === "arrived" ? "bg-amber-500" : "bg-gray-300"}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1">
                        <span className="font-medium truncate">{a.patient_name}</span>
                        <span className={`rounded px-1 py-0.5 text-[10px] font-medium ${STATUS_BADGE[a.status] || ""}`}>
                          {a.status.replace("_", " ")}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(a.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        {a.room_name && ` · ${a.room_name}`}
                        {a.wait_time_minutes != null && ` · wait ${a.wait_time_minutes}m`}
                      </div>
                    </div>
                    <div className="flex gap-0.5">
                      {a.status === "scheduled" && (
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => transition(a.id, "confirmed")} title="Confirm">
                          <Icons.shield className="h-3 w-3 text-green-600" />
                        </Button>
                      )}
                      {a.status === "confirmed" && (
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => transition(a.id, "arrived")} title="Arrived">
                          <Icons.users className="h-3 w-3 text-amber-600" />
                        </Button>
                      )}
                      {a.status === "arrived" && (
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => transition(a.id, "in_progress")} title="Start">
                          <Icons.stethoscope className="h-3 w-3 text-purple-600" />
                        </Button>
                      )}
                      {a.status === "in_progress" && (
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => transition(a.id, "completed")} title="Complete">
                          <Icons.plus className="h-3 w-3 text-green-600" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
              {q.appointments.length === 0 && (
                <p className="text-sm text-muted-foreground">No appointments.</p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
