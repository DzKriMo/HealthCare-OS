"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { Users, Shield, Globe, Fingerprint, Palette } from "lucide-react";

interface OnboardingStatus {
  id: string;
  step: string;
  completed: boolean;
  required: boolean;
  order: number;
}

interface Edition {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
}

const cards = [
  { title: "Team", description: "Manage users and their access", href: "/admin/users", icon: Users, color: "text-blue-600" },
  { title: "Roles & Permissions", description: "Define roles and assign permissions", href: "/admin/roles", icon: Shield, color: "text-purple-600" },
  { title: "Sessions", description: "View and manage active sessions", href: "/admin/sessions", icon: Globe, color: "text-green-600" },
  { title: "Security", description: "Multi-factor authentication settings", href: "/admin/security", icon: Fingerprint, color: "text-red-600" },
  { title: "Branding & Settings", description: "Tenant branding and configuration", href: "#", icon: Palette, color: "text-orange-600" },
];

export default function AdminPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [onboarding, setOnboarding] = useState<OnboardingStatus[]>([]);
  const [editions, setEditions] = useState<Edition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (!isAuthenticated) return;
    Promise.all([
      api.get<OnboardingStatus[]>("/onboarding/").catch(() => []),
      api.get<{ results: Edition[] }>("/editions/").catch(() => ({ results: [] })),
    ]).then(([onb, ed]) => {
      setOnboarding(Array.isArray(onb) ? onb : []);
      setEditions(ed.results);
    }).finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const completed = onboarding.filter((s) => s.completed).length;
  const total = onboarding.filter((s) => s.required).length;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const activeEdition = editions.find((e) => e.is_active);

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Administration</h1>
          <p className="text-muted-foreground">Manage your clinic settings, users, roles, and security.</p>
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Card key={i}><CardContent className="p-6"><Skeleton className="mb-3 h-10 w-10 rounded-lg" /><Skeleton className="mb-2 h-5 w-32" /><Skeleton className="h-4 w-48" /></CardContent></Card>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => {
              const Icon = card.icon;
              return (
                <Card key={card.href} className="cursor-pointer transition-colors hover:border-primary" onClick={() => router.push(card.href)}>
                  <CardContent className="flex items-start gap-4 p-6">
                    <div className={`rounded-lg border p-2.5 ${card.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{card.title}</h3>
                      <p className="text-sm text-muted-foreground">{card.description}</p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardContent className="p-6">
              <h3 className="mb-2 font-semibold">Onboarding Progress</h3>
              {loading ? (
                <Skeleton className="h-4 w-full" />
              ) : total === 0 ? (
                <p className="text-sm text-muted-foreground">No onboarding steps configured.</p>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{completed} of {total} steps complete</span>
                    <span className="font-medium">{pct}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <ul className="mt-3 space-y-1">
                    {onboarding.filter((s) => s.required).map((s) => (
                      <li key={s.id} className="flex items-center gap-2 text-sm">
                        <span className={`h-2 w-2 rounded-full ${s.completed ? "bg-green-500" : "bg-muted-foreground/30"}`} />
                        <span className={s.completed ? "text-muted-foreground line-through" : ""}>{s.step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <h3 className="mb-2 font-semibold">Current Edition</h3>
              {loading ? (
                <Skeleton className="h-4 w-full" />
              ) : activeEdition ? (
                <div>
                  <p className="text-lg font-medium">{activeEdition.name}</p>
                  <p className="text-sm text-muted-foreground">{activeEdition.description}</p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No active edition.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
