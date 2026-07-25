"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface Message {
  id: string; direction: string; content: string; is_bot_reply: boolean; created_at: string;
}

interface Conversation {
  id: string; customer_phone: string; customer_name: string; status: string;
  messages: Message[];
}

export default function ConversationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const convId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [conv, setConv] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conv?.messages]);

  const load = async () => {
    try {
      const data = await api.get<Conversation>(`/bots/conversations/${convId}/`);
      setConv(data);
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
      <div className="mx-auto max-w-4xl">
        <Button variant="ghost" size="sm" onClick={() => router.push("/bots/conversations")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-sm">
              {conv?.customer_name || conv?.customer_phone || "Conversation"}
              {conv?.status && <span className="ml-2 text-xs text-muted-foreground">({conv.status})</span>}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-60 animate-pulse rounded-lg bg-muted" />
            ) : (
              <div className="max-h-[60vh] min-h-[300px] space-y-2 overflow-y-auto rounded-lg border p-3">
                {conv?.messages.map((m) => (
                  <div key={m.id} className={`flex ${m.direction === "outbound" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${m.direction === "outbound" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                      <div className="text-xs font-medium">{m.direction === "outbound" ? "Bot" : conv.customer_name || conv.customer_phone}</div>
                      <div>{m.content}</div>
                      <div className="mt-1 flex items-center gap-2 text-[10px] opacity-70">
                        <span>{format(new Date(m.created_at), "MMM d, HH:mm")}</span>
                        {m.is_bot_reply && <span className="rounded bg-primary/20 px-1">bot</span>}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
