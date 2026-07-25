"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

const FEATURES = [
  "Patient Management",
  "Appointments",
  "Clinical Records",
  "e-Prescriptions",
  "Lab & Imaging",
  "Inventory",
  "Billing",
];

const TECH_STACK = [
  { name: "Next.js", class: "bg-black text-white" },
  { name: "Django", class: "bg-green-700 text-white" },
  { name: "SQLite", class: "bg-blue-600 text-white" },
  { name: "Electron", class: "bg-cyan-700 text-white" },
];

export default function AboutPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary">
              <Icons.logo className="h-8 w-8 text-primary-foreground" />
            </div>
            <h1 className="mt-4 text-2xl font-bold">Healthcare OS</h1>
            <p className="text-sm text-muted-foreground">Desktop Offline Edition 1.0.0</p>
            <p className="mt-2 text-sm text-muted-foreground">Offline-first healthcare management platform</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Features</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {FEATURES.map((feature) => (
                <div key={feature} className="rounded-md border px-3 py-2 text-sm">{feature}</div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Tech Stack</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {TECH_STACK.map((tech) => (
                <span key={tech.name} className={`rounded-md px-3 py-1 text-xs font-medium ${tech.class}`}>{tech.name}</span>
              ))}
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} Healthcare OS. All rights reserved.
        </p>
      </div>
    </DashboardShell>
  );
}
