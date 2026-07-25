"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface DashboardStats {
  active_conversations: number; total_conversations: number;
  total_messages: number; calls_today: number; total_calls: number; successful_calls: number;
}

export default function BotsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
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
      const data = await api.get<DashboardStats>("/bots/dashboard/");
      setStats(data);
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
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">WhatsApp & Voice Bots</h1>
            <p className="text-sm text-muted-foreground">Automated patient communication</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/bots/conversations")}>
              <Icons.messageSquare className="mr-2 h-4 w-4" /> Conversations
            </Button>
            <Button variant="outline" onClick={() => router.push("/bots/calls")}>
              <Icons.phone className="mr-2 h-4 w-4" /> Call Log
            </Button>
            <Button variant="outline" onClick={() => router.push("/bots/settings")}>
              <Icons.settings className="mr-2 h-4 w-4" /> Settings
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[1,2,3].map((i) => <Card key={i}><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>)}
          </div>
        ) : stats ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active Conversations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.active_conversations}</div></CardContent></Card>
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Messages</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_messages}</div></CardContent></Card>
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Conversations</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_conversations}</div></CardContent></Card>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Calls Today</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.calls_today}</div></CardContent></Card>
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total Calls</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_calls}</div></CardContent></Card>
              <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Successful Calls</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{stats.successful_calls}</div></CardContent></Card>
            </div>
          </>
        ) : (
          <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">Configure WhatsApp & Voice bots in Settings to get started.</CardContent></Card>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => router.push("/bots/conversations")}>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-700">
                <Icons.messageSquare className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">WhatsApp Bot</h3>
                <p className="text-sm text-muted-foreground">Auto-reply, appointment reminders, conversation history</p>
              </div>
            </CardContent>
          </Card>
          <Card className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => router.push("/bots/calls")}>
            <CardContent className="flex items-center gap-4 p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-700">
                <Icons.phone className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-semibold">Voice Bot</h3>
                <p className="text-sm text-muted-foreground">Outbound voice calls, appointment reminders, follow-ups</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
