"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const SETTINGS_SECTIONS = [
  { title: "Roles", description: "Manage roles and permissions", href: "/settings/roles", icon: "🔐" },
  { title: "Staff", description: "Invite and manage users", href: "/settings/staff", icon: "👥" },
  { title: "Branding", description: "Clinic logo, colors, and theme", href: "/settings/branding", icon: "🎨" },
  { title: "Notifications", description: "Configure notification channels and templates", href: "/settings/notifications", icon: "🔔" },
  { title: "Modules", description: "Enable or disable modules", href: "/settings/modules", icon: "🧩" },
  { title: "Billing", description: "Item catalog, tax rates, payment methods", href: "/settings/billing", icon: "💳" },
];

export default function SettingsPage() {
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
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Manage your clinic configuration.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SETTINGS_SECTIONS.map((section) => (
            <Link key={section.href} href={section.href}>
              <Card className="cursor-pointer transition-colors hover:border-primary">
                <CardHeader>
                  <div className="text-2xl mb-2">{section.icon}</div>
                  <CardTitle className="text-lg">{section.title}</CardTitle>
                  <CardDescription>{section.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}
