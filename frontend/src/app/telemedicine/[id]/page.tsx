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

interface Consultation {
  id: string; patient_name: string; practitioner_name: string;
  status: string; scheduled_at: string; started_at: string | null;
  ended_at: string | null; meeting_url: string; room_name: string;
  notes: string; patient: string; practitioner: string;
}

interface Message {
  id: string; sender_name: string; content: string; created_at: string;
}

const statusColors: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  ready: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-600",
  cancelled: "bg-red-100 text-red-800",
  missed: "bg-red-100 text-red-800",
};

export default function ConsultationDetailPage() {
  const router = useRouter();
  const params = useParams();
  const cId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatRoomId, setChatRoomId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadConsultation();
  }, [isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConsultation = async () => {
    setLoading(true);
    try {
      const data = await api.get<Consultation>(`/telemedicine/consultations/${cId}/`);
      setConsultation(data);
    } catch {
      setError("Failed to load consultation.");
      setLoading(false);
      return;
    }
    try {
      const rooms = await api.get<{ results: { id: string; consultation: string }[] }>("/telemedicine/chat/rooms/");
      const room = rooms.results.find((r) => r.consultation === cId);
      if (room) {
        setChatRoomId(room.id);
        const msgs = await api.get<{ results: Message[] }>(`/telemedicine/chat/rooms/${room.id}/messages/`);
        setMessages(msgs.results);
        connectWebSocket(room.id);
      }
    } catch { /* chat room may not exist yet */ }
    setLoading(false);
  };

  const connectWebSocket = (roomId: string) => {
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

  const handleStart = async () => {
    await api.post(`/telemedicine/consultations/${cId}/start/`);
    loadConsultation();
  };

  const handleEnd = async () => {
    await api.post(`/telemedicine/consultations/${cId}/end/`);
    loadConsultation();
  };

  const handleCancel = async () => {
    await api.delete(`/telemedicine/consultations/${cId}/`);
    router.push("/telemedicine");
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  if (loading) return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-4"><SkeletonCard /><SkeletonCard /></div>
    </DashboardShell>
  );

  if (error) return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl">
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
      </div>
    </DashboardShell>
  );

  if (!consultation) return null;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/telemedicine")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{consultation.patient_name}</h1>
            <p className="text-sm text-muted-foreground">
              Dr. {consultation.practitioner_name} · {format(new Date(consultation.scheduled_at), "MMM d, yyyy h:mm a")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`rounded-full px-3 py-1 text-sm font-medium ${statusColors[consultation.status] || ""}`}>
              {consultation.status.replace("_", " ")}
            </span>
            {consultation.status === "scheduled" && (
              <>
                <Button onClick={handleStart}><Icons.video className="mr-2 h-4 w-4" /> Start</Button>
                <Button variant="outline" onClick={handleCancel}>Cancel</Button>
              </>
            )}
            {consultation.status === "in_progress" && (
              <>
                <Button onClick={() => window.open(consultation.meeting_url, "_blank")}>
                  <Icons.video className="mr-2 h-4 w-4" /> Join
                </Button>
                <Button onClick={handleEnd}>End Consultation</Button>
              </>
            )}
          </div>
        </div>

        {consultation.notes && (
          <Card>
            <CardHeader><CardTitle className="text-sm">Notes</CardTitle></CardHeader>
            <CardContent><p className="text-sm">{consultation.notes}</p></CardContent>
          </Card>
        )}

        {chatRoomId && (
          <Card>
            <CardHeader><CardTitle className="text-sm">Chat</CardTitle></CardHeader>
            <CardContent>
              <div className="mb-4 max-h-64 space-y-2 overflow-y-auto rounded-lg border p-3">
                {messages.map((m) => (
                  <div key={m.id} className={`flex ${m.sender_name === user.full_name ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${m.sender_name === user.full_name ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                      <div className="text-xs font-medium">{m.sender_name}</div>
                      <div>{m.content}</div>
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
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardShell>
  );
}
