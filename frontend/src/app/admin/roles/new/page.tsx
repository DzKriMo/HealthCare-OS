"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { RoleForm } from "@/components/admin/role-form";
import { PermissionTree } from "@/components/admin/permission-tree";
import { api } from "@/lib/api/client";

interface Permission {
  id: string; codename: string; label: string;
}

export default function AdminNewRolePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loadingPerms, setLoadingPerms] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (!isAuthenticated) return;
    api.get<Permission[]>("/auth/permissions/")
      .then((p) => setPermissions(Array.isArray(p) ? p : (p as { results: Permission[] }).results || []))
      .catch(() => setPageError("Failed to load permissions."))
      .finally(() => setLoadingPerms(false));
  }, [isAuthenticated]);

  const handleSubmit = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      const created = await api.post<{ id: string }>("/auth/roles/", { ...data, permission_ids: selectedIds });
      router.push(`/admin/roles/${created.id}`);
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : "Failed to create role.");
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
            <h1 className="text-3xl font-bold tracking-tight">New Role</h1>
            <p className="text-muted-foreground">Create a new role</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/admin/roles")}>
            Back to Roles
          </Button>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {!loadingPerms && (
          <div className="space-y-6">
            <RoleForm
              permissions={permissions}
              selectedIds={selectedIds}
              onPermissionsChange={setSelectedIds}
              onSubmit={handleSubmit}
              loading={saving}
            />
            <div className="rounded-lg border p-4">
              <h3 className="mb-3 font-semibold">Permissions</h3>
              <PermissionTree
                permissions={permissions}
                selectedIds={selectedIds}
                onChange={setSelectedIds}
              />
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
