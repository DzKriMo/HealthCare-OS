"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiRequestError } from "@/lib/api/client";

interface AppointmentDetail {
  id: string;
  patient: string;
  patient_name: string;
  practitioner_name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  type: string;
  status: string;
  reason: string;
  notes: string;
  room_name: string | null;
  available_transitions: string[];
}

export default function AppointmentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const apptId = params.id as string;
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [appt, setAppt] = useState<AppointmentDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && apptId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, apptId]);

  const load = async () => {
    setLoading(true);
    setLoadError("");
    try {
      setAppt(await api.get<AppointmentDetail>(`/appointments/${apptId}/`));
    } catch {
      setLoadError("Failed to load appointment.");
    } finally {
      setLoading(false);
    }
  };

  const transition = async (target: string) => {
    setTransitioning(true);
    try {
      await api.post(`/appointments/${apptId}/transition/`, { target_status: target });
      await load();
    } catch (err) {
      setLoadError(err instanceof ApiRequestError ? err.message : "Transition failed.");
    } finally {
      setTransitioning(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/appointments")}>
          ← Back to appointments
        </Button>

        {loadError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {loadError}
            <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        {loading && !appt && <div className="h-40 animate-pulse rounded-lg bg-muted" />}

        {appt && (
          <>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold">{appt.patient_name}</h1>
                <p className="text-muted-foreground">
                  {new Date(appt.start_time).toLocaleString()} · {appt.duration_minutes}m · {appt.type}
                </p>
                <p className="text-sm text-muted-foreground">
                  {appt.practitioner_name}{appt.room_name ? ` · ${appt.room_name}` : ""}
                </p>
              </div>
              <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                {appt.status.replace("_", " ")}
              </span>
            </div>

            {appt.reason && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Reason</CardTitle></CardHeader>
                <CardContent className="text-sm">{appt.reason}</CardContent>
              </Card>
            )}

            {appt.available_transitions?.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-lg">Actions</CardTitle></CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {appt.available_transitions.map((t) => (
                    <Button key={t} variant="outline" size="sm" disabled={transitioning}
                      onClick={() => transition(t)}>
                      {t.replace("_", " ")}
                    </Button>
                  ))}
                </CardContent>
              </Card>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push(`/billing/new?patient=${appt.patient}`)}>
                Create invoice
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
