"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiRequestError } from "@/lib/api/client";

const TYPES = ["consultation", "follow_up", "procedure", "emergency", "checkup", "other"];

interface Option { id: string; label: string; }

function NewAppointmentInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetPatient = searchParams.get("patient") || "";
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [patients, setPatients] = useState<Option[]>([]);
  const [practitioners, setPractitioners] = useState<Option[]>([]);
  const [patient, setPatient] = useState(presetPatient);
  const [practitioner, setPractitioner] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [duration, setDuration] = useState(30);
  const [type, setType] = useState("consultation");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [correlationId, setCorrelationId] = useState<string | undefined>();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const loadOptions = async () => {
    try {
      const p = await api.get<{ results: { id: string; full_name: string }[] }>("/patients/");
      setPatients(p.results.map((x) => ({ id: x.id, label: x.full_name })));
    } catch { /* handled by empty state */ }
    try {
      const u = await api.get<{ results: { id: string; full_name: string; role_name: string }[] }>("/auth/users/");
      setPractitioners(
        u.results
          .filter((x) => ["Doctor", "Nurse", "Admin"].includes(x.role_name))
          .map((x) => ({ id: x.id, label: x.full_name })),
      );
    } catch {
      // Reception may lack user-list permission; fall back to self.
      if (user) setPractitioners([{ id: user.id, label: `${user.first_name} ${user.last_name}` }]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCorrelationId(undefined);
    if (!patient || !practitioner || !date || !time) {
      setError("Patient, practitioner, date, and time are required.");
      return;
    }
    const start = new Date(`${date}T${time}`);
    const end = new Date(start.getTime() + duration * 60000);

    setSubmitting(true);
    try {
      const created = await api.post<{ id: string }>("/appointments/", {
        patient,
        practitioner,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        type,
        reason,
      });
      router.push(`/appointments/${created.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
        setCorrelationId(err.correlationId);
      } else {
        setError("Failed to book appointment.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Book Appointment</h1>
          <p className="text-muted-foreground">Schedule a new appointment.</p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
            {correlationId && <span className="mt-1 block text-xs opacity-70">Ref: {correlationId}</span>}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Details</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="patient">Patient *</Label>
                <select id="patient" value={patient} onChange={(e) => setPatient(e.target.value)} className={selectCls} required>
                  <option value="">Select patient...</option>
                  {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="practitioner">Practitioner *</Label>
                <select id="practitioner" value={practitioner} onChange={(e) => setPractitioner(e.target.value)} className={selectCls} required>
                  <option value="">Select practitioner...</option>
                  {practitioners.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="date">Date *</Label>
                <Input id="date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="time">Time *</Label>
                <Input id="time" type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="duration">Duration (min)</Label>
                <Input id="duration" type="number" min={5} step={5} value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="type">Type</Label>
                <select id="type" value={type} onChange={(e) => setType(e.target.value)} className={selectCls}>
                  {TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
                </select>
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="reason">Reason</Label>
                <Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Chief complaint or note" />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>{submitting ? "Booking..." : "Book Appointment"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/appointments")}>Cancel</Button>
          </div>
        </form>
      </div>
    </DashboardShell>
  );
}

export default function NewAppointmentPage() {
  return (
    <Suspense fallback={null}>
      <NewAppointmentInner />
    </Suspense>
  );
}
