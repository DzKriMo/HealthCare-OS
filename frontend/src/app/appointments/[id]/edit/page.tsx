"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api, ApiRequestError } from "@/lib/api/client";

const TYPES = ["consultation", "follow_up", "procedure", "emergency", "checkup", "other"];

export default function EditAppointmentPage() {
  const router = useRouter();
  const params = useParams();
  const apptId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [type, setType] = useState("consultation");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && apptId) load();
  }, [isAuthenticated, apptId]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<Record<string, string>>(`/appointments/${apptId}/`);
      const st = new Date(data.start_time);
      setStartDate(st.toISOString().split("T")[0]);
      setStartTime(st.toTimeString().slice(0, 5));
      setType(data.type || "consultation");
      setReason(data.reason || "");
      setNotes(data.notes || "");
    } catch { setError("Failed to load appointment."); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!startDate || !startTime) { setError("Date and time are required."); return; }
    setSubmitting(true); setError("");
    try {
      const start = new Date(`${startDate}T${startTime}`);
      const end = new Date(start.getTime() + 30 * 60000);
      await api.put(`/appointments/${apptId}/`, {
        start_time: start.toISOString(), end_time: end.toISOString(),
        type, reason, notes,
      });
      router.push(`/appointments/${apptId}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to update.");
    } finally { setSubmitting(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push(`/appointments/${apptId}`)}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Edit Appointment</h1>
          <p className="text-muted-foreground">Update appointment details.</p>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        {loading && <SkeletonCard />}

        {!loading && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <Card>
              <CardHeader><CardTitle>Schedule</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>Date *</Label>
                  <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label>Time *</Label>
                  <Input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <select value={type} onChange={(e) => setType(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    {TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
                  </select>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Details</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Reason</Label>
                  <Input value={reason} onChange={(e) => setReason(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Notes</Label>
                  <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                    className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
              </CardContent>
            </Card>
            <div className="flex gap-2">
              <Button type="submit" disabled={submitting}>{submitting ? "Saving..." : "Save Changes"}</Button>
              <Button type="button" variant="outline" onClick={() => router.push(`/appointments/${apptId}`)}>Cancel</Button>
            </div>
          </form>
        )}
      </div>
    </DashboardShell>
  );
}
