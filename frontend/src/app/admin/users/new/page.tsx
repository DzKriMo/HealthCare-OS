"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { UserForm } from "@/components/admin/user-form";
import { api } from "@/lib/api/client";

interface Role {
  id: string; name: string;
}

export default function AdminNewUserPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (!isAuthenticated) return;
    api.get<{ results: Role[] }>("/auth/roles/")
      .then((r) => setRoles(r.results))
      .catch(() => setPageError("Failed to load roles."))
      .finally(() => setLoadingRoles(false));
  }, [isAuthenticated]);

  const handleSubmit = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      const created = await api.post<{ id: string }>("/auth/users/", data);
      router.push(`/admin/users/${created.id}`);
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : "Failed to create user.");
    } finally { setSaving(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">New User</h1>
            <p className="text-muted-foreground">Create a new user account</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/admin/users")}>
            Back to Users
          </Button>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {!loadingRoles && (
          <UserForm
            roles={roles}
            onSubmit={handleSubmit}
            loading={saving}
          />
        )}
      </div>
    </DashboardShell>
  );
}
