"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api, ApiRequestError } from "@/lib/api/client";

interface ApptDetail {
  id: string; patient: string; patient_name: string;
  practitioner: string; practitioner_name: string;
  start_time: string; end_time: string; duration_minutes: number;
  type: string; status: string; priority: string;
  reason: string; notes: string;
  room: string | null; room_name: string | null;
  is_recurring: boolean; recurrence_rule: string; recurrence_group: string | null;
  booked_online: boolean; booking_source: string; confirmation_code: string;
  checked_in_at: string | null; started_at: string | null; completed_at: string | null;
  cancelled_at: string | null; cancellation_reason: string;
  created_by_name: string; created_at: string; updated_at: string;
  available_transitions: string[];
}

const STATUS_BADGES: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800", confirmed: "bg-green-100 text-green-800",
  arrived: "bg-amber-100 text-amber-800", in_progress: "bg-purple-100 text-purple-800",
  completed: "bg-gray-100 text-gray-600", cancelled: "bg-red-100 text-red-800",
  no_show: "bg-red-100 text-red-800",
};

export default function AppointmentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const apptId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [appt, setAppt] = useState<ApptDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState<string | null>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && apptId) load();
  }, [isAuthenticated, apptId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try { setAppt(await api.get<ApptDetail>(`/appointments/${apptId}/`)); }
    catch { setLoadError("Failed to load appointment."); }
    finally { setLoading(false); }
  };

  const transition = async (target: string) => {
    setTransitioning(target);
    try {
      await api.post(`/appointments/${apptId}/transition/`, { target_status: target });
      await load();
    } catch (err) {
      setLoadError(err instanceof ApiRequestError ? err.message : "Transition failed.");
    } finally { setTransitioning(null); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/appointments")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        {loading && !appt && <SkeletonCard />}

        {appt && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{appt.patient_name}</h1>
                  <span className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_BADGES[appt.status]}`}>
                    {appt.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-muted-foreground mt-1">
                  {new Date(appt.start_time).toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                  {" · "}{new Date(appt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  {" — "}{new Date(appt.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  {" · "}{appt.duration_minutes}m
                </p>
                <p className="text-sm text-muted-foreground">
                  {appt.practitioner_name} · {appt.type.replace("_", " ")}
                  {appt.room_name ? ` · Room ${appt.room_name}` : ""}
                  {appt.confirmation_code ? ` · Code: ${appt.confirmation_code}` : ""}
                </p>
              </div>
              <Button variant="outline" onClick={() => router.push(`/appointments/${appt.id}/edit`)}>
                <Icons.settings className="mr-2 h-4 w-4" /> Edit
              </Button>
            </div>

            {appt.is_recurring && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="flex items-center gap-2 py-3 text-sm text-blue-800">
                  <Icons.calendar className="h-4 w-4" />
                  Recurring appointment · {appt.recurrence_rule || "Series"}
                </CardContent>
              </Card>
            )}

            {appt.reason && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Reason</CardTitle></CardHeader>
                <CardContent className="text-sm">{appt.reason}</CardContent>
              </Card>
            )}

            {appt.notes && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Notes</CardTitle></CardHeader>
                <CardContent className="text-sm whitespace-pre-wrap">{appt.notes}</CardContent>
              </Card>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-sm font-medium">Timeline</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <Row label="Created" value={appt.created_by_name ? `${new Date(appt.created_at).toLocaleString()} by ${appt.created_by_name}` : new Date(appt.created_at).toLocaleString()} />
                  {appt.checked_in_at && <Row label="Checked in" value={new Date(appt.checked_in_at).toLocaleString()} />}
                  {appt.started_at && <Row label="Started" value={new Date(appt.started_at).toLocaleString()} />}
                  {appt.completed_at && <Row label="Completed" value={new Date(appt.completed_at).toLocaleString()} />}
                  {appt.cancelled_at && <Row label="Cancelled" value={`${new Date(appt.cancelled_at).toLocaleString()} · ${appt.cancellation_reason || "No reason"}`} />}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-sm font-medium">Details</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <Row label="Type" value={appt.type.replace("_", " ")} />
                  <Row label="Priority" value={appt.priority} />
                  <Row label="Source" value={appt.booking_source || "In-clinic"} />
                  <Row label="Patient ID" value={appt.patient} />
                  <Row label="Updated" value={new Date(appt.updated_at).toLocaleString()} />
                </CardContent>
              </Card>
            </div>

            {appt.available_transitions.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Status Actions</CardTitle></CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {appt.available_transitions.map((t) => {
                    const variant = t === "cancelled" || t === "no_show" ? "destructive" : "default";
                    return (
                      <Button key={t} variant={variant} size="sm" disabled={transitioning === t}
                        onClick={() => transition(t)}>
                        {transitioning === t ? "..." : t.replace("_", " ")}
                      </Button>
                    );
                  })}
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push(`/patients/${appt.patient}`)}>
                <Icons.users className="mr-2 h-4 w-4" /> View Patient
              </Button>
              <Button variant="outline" onClick={() => router.push(`/billing/new?patient=${appt.patient}`)}>
                <Icons.creditCard className="mr-2 h-4 w-4" /> Create invoice
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-muted-foreground">{label}:</span>
      <span className="text-right">{value}</span>
    </div>
  );
}
