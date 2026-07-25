"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import type { User } from "@healthcare-os/types";

export default function StaffPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();
  const [staff, setStaff] = useState<User[]>([]);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) api.get<User[]>("/auth/users/").then(setStaff).catch(() => {});
  }, [isAuthenticated]);

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
            <h1 className="text-3xl font-bold tracking-tight">Staff</h1>
            <p className="text-muted-foreground">{staff.length} team members</p>
          </div>
          <Button><Icons.plus className="mr-2 h-4 w-4" />Invite member</Button>
        </div>
        <div className="space-y-2">
          {staff.map((s) => (
            <Card key={s.id}>
              <CardContent className="flex items-center gap-4 py-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                  {s.first_name?.[0]}{s.last_name?.[0]}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{s.first_name} {s.last_name}</div>
                  <div className="text-sm text-muted-foreground">{s.email} · {s.role_name}</div>
                </div>
              </CardContent>
            </Card>
          ))}
          {staff.length === 0 && (
            <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
              <Icons.users className="mx-auto mb-3 h-8 w-8" />
              <p>No staff members yet.</p>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
