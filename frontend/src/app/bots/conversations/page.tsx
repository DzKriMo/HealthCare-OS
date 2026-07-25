"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface Conversation {
  id: string; customer_phone: string; customer_name: string;
  status: string; is_bot_handled: boolean; message_count: number;
  last_message: { content: string; direction: string; created_at: string } | null;
  last_message_at: string;
}

const statusColors: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  resolved: "bg-gray-100 text-gray-600",
  escalated: "bg-yellow-100 text-yellow-800",
};

export default function ConversationsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  const load = async () => {
    try {
      const params = search ? `?phone=${search}` : "";
      const res = await api.get<{ results: Conversation[] }>(`/bots/conversations/${params}`);
      setConversations(res.results);
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
            <h1 className="text-2xl font-bold">WhatsApp Conversations</h1>
            <p className="text-sm text-muted-foreground">Inbound & outbound message history</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => router.push("/bots")}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
          </Button>
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Search by phone number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            className="max-w-sm"
          />
          <Button variant="secondary" onClick={load}>Search</Button>
        </div>

        {loading ? (
          <Card><CardContent><div className="h-40 animate-pulse rounded-lg bg-muted" /></CardContent></Card>
        ) : conversations.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No conversations yet.</CardContent></Card>
        ) : (
          <div className="space-y-2">
            {conversations.map((c) => (
              <Card key={c.id} className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => router.push(`/bots/conversations/${c.id}`)}>
                <CardContent className="flex items-center gap-4 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {c.customer_phone.slice(-2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.customer_name || c.customer_phone}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[c.status] || ""}`}>{c.status}</span>
                      {!c.is_bot_handled && <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-800">Staff</span>}
                    </div>
                    {c.last_message && (
                      <div className="truncate text-sm text-muted-foreground">
                        {c.last_message.direction === "inbound" ? "← " : "→ "}{c.last_message.content}
                      </div>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-xs text-muted-foreground">{format(new Date(c.last_message_at), "MMM d, HH:mm")}</div>
                    <div className="text-xs text-muted-foreground">{c.message_count} msgs</div>
                  </div>
                  <Icons.chevronDown className="h-5 w-5 -rotate-90 text-muted-foreground" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
