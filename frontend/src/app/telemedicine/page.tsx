"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface Consultation {
  id: string; patient_name: string; practitioner_name: string;
  status: string; scheduled_at: string; meeting_url: string; room_name: string;
  notes: string; patient: string; practitioner: string;
}

interface DashboardStats {
  upcoming: number; in_progress: number; completed_today: number; total: number;
}

const statusColors: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  ready: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-600",
  cancelled: "bg-red-100 text-red-800",
  missed: "bg-red-100 text-red-800",
};

export default function TelemedicinePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  const load = async () => {
    setLoading(true);
    try {
      const [consRes, statsRes] = await Promise.all([
        api.get<{ results: Consultation[] }>("/telemedicine/consultations/"),
        api.get<DashboardStats>("/telemedicine/dashboard/"),
      ]);
      setConsultations(consRes.results);
      setStats(statsRes);
    } catch { setError("Failed to load telemedicine data."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Telemedicine</h1>
            <p className="text-sm text-muted-foreground">Video consultations &amp; chat</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/chat")}>
              <Icons.messageSquare className="mr-2 h-4 w-4" /> Chat
            </Button>
            <Button onClick={() => router.push("/telemedicine/new")}>
              <Icons.video className="mr-2 h-4 w-4" /> New Consultation
            </Button>
          </div>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        {stats && (
          <div className="grid gap-4 md:grid-cols-4">
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Upcoming</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.upcoming}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">In Progress</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.in_progress}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Completed Today</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.completed_today}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total}</div></CardContent></Card>
          </div>
        )}

        {loading ? (
          <div className="space-y-4"><SkeletonCard /><SkeletonTable rows={4} /></div>
        ) : (
          <Card>
            <CardHeader><CardTitle>Video Consultations</CardTitle></CardHeader>
            <CardContent>
              {consultations.length === 0 ? (
                <p className="text-sm text-muted-foreground">No consultations scheduled.</p>
              ) : (
                <div className="space-y-3">
                  {consultations.map((c) => (
                    <div key={c.id} className="flex items-center justify-between rounded-lg border p-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{c.patient_name}</span>
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[c.status] || ""}`}>
                            {c.status.replace("_", " ")}
                          </span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Dr. {c.practitioner_name} · {format(new Date(c.scheduled_at), "MMM d, yyyy h:mm a")}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {c.status === "in_progress" && (
                          <Button size="sm" onClick={() => window.open(c.meeting_url, "_blank")}>
                            <Icons.video className="mr-1 h-4 w-4" /> Join
                          </Button>
                        )}
                        <Button size="sm" variant="outline" onClick={() => router.push(`/telemedicine/${c.id}`)}>
                          <Icons.chevronDown className="h-4 w-4 rotate-270" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
