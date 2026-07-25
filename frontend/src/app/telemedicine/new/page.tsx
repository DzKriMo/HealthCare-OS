"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

export default function NewConsultationPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [patientId, setPatientId] = useState("");
  const [practitionerId, setPractitionerId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId || !practitionerId || !scheduledAt) {
      setError("Patient, practitioner, and scheduled time are required.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const res = await api.post("/telemedicine/consultations/", {
        patient: patientId,
        practitioner: practitionerId,
        scheduled_at: new Date(scheduledAt).toISOString(),
        notes,
      });
      router.push(`/telemedicine/${res.id}`);
    } catch {
      setError("Failed to create consultation.");
    } finally { setSubmitting(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/telemedicine")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>
        <Card>
          <CardHeader><CardTitle>Schedule Video Consultation</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
              <div className="space-y-2">
                <Label htmlFor="patient">Patient ID *</Label>
                <Input id="patient" value={patientId} onChange={(e) => setPatientId(e.target.value)} placeholder="Patient UUID" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="practitioner">Practitioner ID *</Label>
                <Input id="practitioner" value={practitionerId} onChange={(e) => setPractitionerId(e.target.value)} placeholder="Practitioner UUID" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="scheduled_at">Scheduled Date &amp; Time *</Label>
                <Input id="scheduled_at" type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notes</Label>
                <textarea id="notes" className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Creating..." : "Schedule Consultation"}
                </Button>
                <Button type="button" variant="outline" onClick={() => router.push("/telemedicine")}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
