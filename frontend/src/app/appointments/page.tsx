"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { AppointmentCalendar } from "@/components/scheduling/appointment-calendar";

export default function AppointmentsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Appointments</h1>
            <p className="text-muted-foreground">Manage patient appointments and schedules.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/appointments/queue")}>
              Queue Board
            </Button>
            <Button variant="outline" onClick={() => router.push("/appointments/waiting-list")}>
              Waiting List
            </Button>
            <Button onClick={() => router.push("/appointments/new")}>
              <Icons.plus className="mr-2 h-4 w-4" />
              New Appointment
            </Button>
          </div>
        </div>

        <AppointmentCalendar />
      </div>
    </DashboardShell>
  );
}
