"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface CallLog {
  id: string; direction: string; status: string; to_number: string;
  from_number: string; duration_seconds: number | null; purpose: string;
  is_bot_call: boolean; started_at: string | null; created_at: string;
}

const statusColors: Record<string, string> = {
  queued: "bg-gray-100 text-gray-600",
  ringing: "bg-blue-100 text-blue-800",
  in_progress: "bg-green-100 text-green-800",
  completed: "bg-green-100 text-green-800",
  busy: "bg-red-100 text-red-800",
  failed: "bg-red-100 text-red-800",
  no_answer: "bg-yellow-100 text-yellow-800",
  cancelled: "bg-gray-100 text-gray-600",
};

export default function CallLogPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [calls, setCalls] = useState<CallLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  const load = async () => {
    try {
      const res = await api.get<{ results: CallLog[] }>("/bots/calls/");
      setCalls(res.results);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Voice Call Log</h1>
            <p className="text-sm text-muted-foreground">Outbound call history</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => router.push("/bots")}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
          </Button>
        </div>

        {loading ? (
          <Card><CardContent><div className="h-40 animate-pulse rounded-lg bg-muted" /></CardContent></Card>
        ) : calls.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No calls yet. Configure voice bot in Settings.</CardContent></Card>
        ) : (
          <Card>
            <CardHeader><CardTitle>Call History</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {calls.map((call) => (
                  <div key={call.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Icons.phone className={`h-4 w-4 ${call.status === "completed" ? "text-green-600" : "text-muted-foreground"}`} />
                        <span className="font-medium">{call.to_number}</span>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[call.status] || ""}`}>
                          {call.status.replace("_", " ")}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {call.purpose || "General"} · {call.duration_seconds ? `${call.duration_seconds}s` : "—"}
                        {call.is_bot_call ? " · Bot call" : ""}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {call.started_at ? format(new Date(call.started_at), "MMM d, HH:mm") : format(new Date(call.created_at), "MMM d, HH:mm")}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
