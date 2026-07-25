"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MFASetup } from "@/components/admin/mfa-setup";
import { Icons } from "@/components/icons";

export default function AdminSecurityPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [showMfaSetup, setShowMfaSetup] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const mfaEnabled = (user as Record<string, unknown>).mfa_enabled === true;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Security</h1>
            <p className="text-muted-foreground">Multi-factor authentication settings</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/admin")}>
            Back to Admin
          </Button>
        </div>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg border p-2.5 text-green-600">
                <Icons.shield className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold">Multi-Factor Authentication</h3>
                <p className="text-sm text-muted-foreground">
                  {mfaEnabled
                    ? "MFA is currently enabled for your account."
                    : "MFA is not enabled. Add an extra layer of security."}
                </p>
              </div>
            </div>
            {!mfaEnabled && !showMfaSetup && (
              <Button className="mt-4" onClick={() => setShowMfaSetup(true)}>
                Enable MFA
              </Button>
            )}
          </CardContent>
        </Card>

        {showMfaSetup && (
          <MFASetup
            onComplete={() => { setShowMfaSetup(false); fetchCurrentUser(); }}
            onSkip={() => setShowMfaSetup(false)}
          />
        )}
      </div>
    </DashboardShell>
  );
}
