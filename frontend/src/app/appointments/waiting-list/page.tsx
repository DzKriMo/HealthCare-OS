"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api, ApiRequestError } from "@/lib/api/client";

interface WaitingEntry {
  id: string; patient: string; patient_name: string;
  preferred_practitioner: string | null; practitioner_name: string | null;
  preferred_date_start: string | null; preferred_date_end: string | null;
  preferred_time_of_day: string; appointment_type: string;
  priority: string; reason: string; notes: string;
  created_at: string;
}

const PRIORITIES = ["low", "normal", "high"];
const TIME_PREFS = ["morning", "afternoon", "evening"];
const APPT_TYPES = ["consultation", "follow_up", "procedure", "emergency", "checkup", "other"];

export default function WaitingListPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [entries, setEntries] = useState<WaitingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [patients, setPatients] = useState<{ id: string; label: string }[]>([]);
  const [showForm, setShowForm] = useState(false);

  const [patient, setPatient] = useState("");
  const [appointmentType, setAppointmentType] = useState("consultation");
  const [priority, setPriority] = useState("normal");
  const [preferredTimeOfDay, setPreferredTimeOfDay] = useState("morning");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) { load(); loadPatients(); } }, [isAuthenticated]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: WaitingEntry[] }>("/appointments/waiting-list/");
      setEntries(data.results);
    } catch { setError("Failed to load waiting list."); }
    finally { setLoading(false); }
  };

  const loadPatients = async () => {
    try {
      const data = await api.get<{ results: { id: string; full_name: string }[] }>("/patients/");
      setPatients(data.results.map((x) => ({ id: x.id, label: x.full_name })));
    } catch { }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patient) { setFormError("Patient is required."); return; }
    setSubmitting(true); setFormError("");
    try {
      await api.post("/appointments/waiting-list/", {
        patient, appointment_type: appointmentType, priority,
        preferred_time_of_day: preferredTimeOfDay, reason,
      });
      setShowForm(false); setPatient(""); setReason("");
      await load();
    } catch (err) { setFormError(err instanceof ApiRequestError ? err.message : "Failed to add."); }
    finally { setSubmitting(false); }
  };

  const handleRemove = async (id: string) => {
    try { await api.delete(`/appointments/waiting-list/${id}/`); await load(); }
    catch { }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Button variant="ghost" size="sm" onClick={() => router.push("/appointments")}>
              <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
            </Button>
            <h1 className="text-3xl font-bold tracking-tight mt-2">Waiting List</h1>
            <p className="text-muted-foreground">{entries.length} patient{entries.length !== 1 ? "s" : ""} waiting</p>
          </div>
          <Button onClick={() => setShowForm(!showForm)}>
            <Icons.plus className="mr-2 h-4 w-4" />{showForm ? "Cancel" : "Add to Waitlist"}
          </Button>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        {showForm && (
          <form onSubmit={handleAdd} className="space-y-4 rounded-lg border p-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Patient *</Label>
                <select value={patient} onChange={(e) => setPatient(e.target.value)} className={selectCls}>
                  <option value="">Select...</option>
                  {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Type</Label>
                <select value={appointmentType} onChange={(e) => setAppointmentType(e.target.value)} className={selectCls}>
                  {APPT_TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Priority</Label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)} className={selectCls}>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Time preference</Label>
                <select value={preferredTimeOfDay} onChange={(e) => setPreferredTimeOfDay(e.target.value)} className={selectCls}>
                  {TIME_PREFS.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Reason</Label>
              <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why is the patient waiting?" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" disabled={submitting}>{submitting ? "Adding..." : "Add to Waitlist"}</Button>
          </form>
        )}

        {loading ? <SkeletonTable rows={5} /> : (
          <div className="space-y-2">
            {entries.map((e) => (
              <Card key={e.id}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{e.patient_name}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${e.priority === "high" ? "bg-red-100 text-red-800" : e.priority === "normal" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600"}`}>
                        {e.priority}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {e.appointment_type.replace("_", " ")} · {e.preferred_time_of_day}
                      {e.practitioner_name && ` · Dr. ${e.practitioner_name}`}
                    </div>
                    {e.reason && <div className="text-xs text-muted-foreground">{e.reason}</div>}
                    <div className="text-xs text-muted-foreground">
                      Added {new Date(e.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleRemove(e.id)}>
                    <Icons.x className="h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
            {entries.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.calendar className="mx-auto mb-3 h-8 w-8" />
                <p>No patients on the waiting list.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
