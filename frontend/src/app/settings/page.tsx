"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
  const [licenseKey, setLicenseKey] = useState("");
  const [licenseEmail, setLicenseEmail] = useState("");
  const [licenseStatus, setLicenseStatus] = useState("Checking...");
  const [backupMessage, setBackupMessage] = useState("");
  const [restoreMessage, setRestoreMessage] = useState("");

  const isDesktop = typeof window !== "undefined" && !!window.healthcareOS;

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isDesktop && window.healthcareOS) {
      (window.healthcareOS as any).getLicenseStatus?.()
        .then((status: string) => setLicenseStatus(status))
        .catch(() => setLicenseStatus("Desktop Edition"));
    } else {
      setLicenseStatus("Desktop Edition");
    }
  }, [isDesktop]);

  const handleActivate = async () => {
    if (!window.healthcareOS) return;
    try {
      await (window.healthcareOS as any).activateLicense?.({ key: licenseKey, email: licenseEmail });
      setLicenseStatus("Active");
    } catch {
      setLicenseStatus("Activation failed");
    }
  };

  const handleBackup = async () => {
    if (!window.healthcareOS) return;
    try {
      const result = await (window.healthcareOS as any).invoke("backup:create");
      setBackupMessage(result?.path ? `Backup saved to ${result.path}` : "Backup created");
    } catch {
      setBackupMessage("Backup failed");
    }
  };

  const handleRestore = async () => {
    if (!window.healthcareOS) return;
    try {
      const result = await (window.healthcareOS as any).invoke("restore:execute");
      setRestoreMessage(result?.path ? `Restored from ${result.path}` : "Restore complete");
    } catch {
      setRestoreMessage("Restore failed");
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

        <Card>
          <CardHeader>
            <CardTitle>License</CardTitle>
            <CardDescription>License status and activation.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Status:</span>
              <span className="text-sm font-medium">{licenseStatus}</span>
              {isDesktop && (
                <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="license-key">License Key</Label>
              <Input id="license-key" value={licenseKey} onChange={(e) => setLicenseKey(e.target.value)} placeholder="Enter license key" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="license-email">Email</Label>
              <Input id="license-email" type="email" value={licenseEmail} onChange={(e) => setLicenseEmail(e.target.value)} placeholder="Enter email" />
            </div>
            <Button onClick={handleActivate} disabled={!isDesktop || !licenseKey || !licenseEmail}>Activate</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Backup & Restore</CardTitle>
            <CardDescription>Create or restore database backups.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <Button onClick={handleBackup} disabled={!isDesktop}>Create Backup</Button>
              <Button onClick={handleRestore} disabled={!isDesktop} variant="outline">Restore</Button>
            </div>
            {backupMessage && <p className="text-sm text-muted-foreground">{backupMessage}</p>}
            {restoreMessage && <p className="text-sm text-muted-foreground">{restoreMessage}</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p><span className="text-muted-foreground">Version:</span> Desktop Offline Edition 1.0.0</p>
            <p><span className="text-muted-foreground">Platform:</span> {isDesktop ? "Desktop (Electron)" : "Web"}</p>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
