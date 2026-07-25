"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface ChatRoom {
  id: string; consultation: string | null;
  participant_names: string[];
  last_message: { content: string; sender_name: string; created_at: string } | null;
  is_active: boolean; created_at: string;
}

export default function ChatInboxPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
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
      const res = await api.get<{ results: ChatRoom[] }>("/telemedicine/chat/rooms/");
      setRooms(res.results);
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
            <h1 className="text-2xl font-bold">Chat</h1>
            <p className="text-sm text-muted-foreground">Your conversations</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/telemedicine")}>
            <Icons.video className="mr-2 h-4 w-4" /> Telemedicine
          </Button>
        </div>

        {loading ? (
          <SkeletonCard />
        ) : rooms.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Icons.messageSquare className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-sm text-muted-foreground">No conversations yet.</p>
              <p className="text-xs text-muted-foreground">Chat rooms are created when a video consultation is scheduled.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {rooms.map((room) => (
              <Card key={room.id} className="cursor-pointer hover:bg-accent/50 transition-colors" onClick={() => router.push(`/chat/${room.id}`)}>
                <CardContent className="flex items-center gap-4 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {room.participant_names.filter((n) => n !== user.full_name).map((n) => n[0]).join("") || "?"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">
                      {room.participant_names.filter((n) => n !== user.full_name).join(", ") || "General"}
                    </div>
                    {room.last_message && (
                      <div className="truncate text-sm text-muted-foreground">
                        <span className="font-medium">{room.last_message.sender_name}:</span> {room.last_message.content}
                      </div>
                    )}
                  </div>
                  {room.last_message && (
                    <div className="shrink-0 text-xs text-muted-foreground">
                      {format(new Date(room.last_message.created_at), "MMM d, HH:mm")}
                    </div>
                  )}
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
