"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface AppointmentSummary {
  id: string;
  patient_name: string;
  practitioner_name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  type: string;
  status: string;
  room_name: string | null;
}

export default function AppointmentsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();
  const [appointments, setAppointments] = useState<AppointmentSummary[]>([]);
  const [view, setView] = useState<"day" | "week">("day");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadAppointments();
  }, [isAuthenticated]);

  const loadAppointments = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const data = await api.get<{ results: AppointmentSummary[] }>(
        `/appointments/?from=${today}`,
      );
      setAppointments(data.results);
    } catch { /* handled */ }
  };

  const statusColor = (status: string) => {
    const map: Record<string, string> = {
      scheduled: "text-blue-600 bg-blue-50",
      confirmed: "text-green-600 bg-green-50",
      arrived: "text-amber-600 bg-amber-50",
      in_progress: "text-purple-600 bg-purple-50",
      completed: "text-gray-600 bg-gray-50",
      cancelled: "text-red-600 bg-red-50",
      no_show: "text-red-800 bg-red-100",
    };
    return map[status] || "text-gray-600 bg-gray-50";
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
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Appointments</h1>
            <p className="text-muted-foreground">
              {appointments.length} scheduled
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant={view === "day" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("day")}
            >
              Day
            </Button>
            <Button
              variant={view === "week" ? "default" : "outline"}
              size="sm"
              onClick={() => setView("week")}
            >
              Week
            </Button>
            <Button onClick={() => router.push("/appointments/new")}>
              <Icons.plus className="mr-2 h-4 w-4" />
              New Appointment
            </Button>
          </div>
        </div>

        {/* Quick links */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => router.push("/appointments/queue")}>
            Queue Board
          </Button>
          <Button variant="outline" size="sm" onClick={() => router.push("/appointments/waiting-list")}>
            Waiting List
          </Button>
        </div>

        {/* Appointment list */}
        <div className="space-y-2">
          {appointments.map((appt) => (
            <Card
              key={appt.id}
              className="cursor-pointer transition-colors hover:border-primary"
              onClick={() => router.push(`/appointments/${appt.id}`)}
            >
              <CardContent className="flex items-center gap-4 p-4">
                <div className="w-20 text-center">
                  <div className="text-lg font-bold">
                    {new Date(appt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {appt.duration_minutes}m
                  </div>
                </div>
                <div className="flex-1">
                  <div className="font-medium">{appt.patient_name}</div>
                  <div className="text-sm text-muted-foreground">
                    {appt.practitioner_name} · {appt.type}
                    {appt.room_name ? ` · ${appt.room_name}` : ""}
                  </div>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(appt.status)}`}
                >
                  {appt.status.replace("_", " ")}
                </span>
              </CardContent>
            </Card>
          ))}
          {appointments.length === 0 && (
            <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
              <Icons.calendar className="mx-auto mb-3 h-8 w-8" />
              <p>No appointments scheduled</p>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
