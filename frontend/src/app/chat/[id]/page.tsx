"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface Message {
  id: string; sender_name: string; content: string; created_at: string;
}

export default function ChatThreadPage() {
  const router = useRouter();
  const params = useParams();
  const roomId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [chatInput, setChatInput] = useState("");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadMessages();
  }, [isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadMessages = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ results: Message[] }>(`/telemedicine/chat/rooms/${roomId}/messages/`);
      setMessages(res.results);
      connectWebSocket();
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/chat/${roomId}/`);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "message") {
        setMessages((prev) => [...prev, { id: data.id, sender_name: data.sender_name, content: data.content, created_at: data.created_at }]);
      }
    };
    socket.onopen = () => setWs(socket);
    socket.onclose = () => setWs(null);
  };

  const sendMessage = () => {
    if (!chatInput.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "message", content: chatInput }));
    setChatInput("");
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl">
        <Button variant="ghost" size="sm" onClick={() => router.push("/chat")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to chat
        </Button>

        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${ws ? "bg-green-500" : "bg-red-500"}`} />
              {ws ? "Connected" : "Disconnected"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <SkeletonCard />
            ) : (
              <>
                <div className="mb-4 max-h-[60vh] min-h-[300px] space-y-2 overflow-y-auto rounded-lg border p-3">
                  {messages.map((m) => (
                    <div key={m.id} className={`flex ${m.sender_name === user.full_name ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${m.sender_name === user.full_name ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                        <div className="text-xs font-medium">{m.sender_name}</div>
                        <div>{m.content}</div>
                        <div className="mt-1 text-[10px] opacity-70">{format(new Date(m.created_at), "HH:mm")}</div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
                <div className="flex gap-2">
                  <input
                    className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    placeholder="Type a message..."
                  />
                  <Button size="sm" onClick={sendMessage} disabled={!ws || ws.readyState !== WebSocket.OPEN}>
                    Send
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
