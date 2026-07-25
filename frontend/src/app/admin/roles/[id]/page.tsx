"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { RoleForm } from "@/components/admin/role-form";
import { PermissionTree } from "@/components/admin/permission-tree";
import { SkeletonDetail } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

interface RoleData {
  id: string; name: string; description: string; is_system_role: boolean; permission_ids: string[];
}

interface Permission {
  id: string; codename: string; label: string;
}

export default function AdminRoleDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [roleData, setRoleData] = useState<RoleData | null>(null);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const pk = params?.id as string;

  useEffect(() => {
    if (!isAuthenticated || !pk) return;
    Promise.all([
      api.get<RoleData>(`/auth/roles/${pk}/`),
      api.get<Permission[]>("/auth/permissions/"),
    ]).then(([r, p]) => {
      setRoleData(r);
      setPermissions(Array.isArray(p) ? p : (p as { results: Permission[] }).results || []);
      setSelectedIds(r.permission_ids || []);
    }).catch(() => setPageError("Failed to load role."))
    .finally(() => setLoading(false));
  }, [isAuthenticated, pk]);

  const handleSubmit = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      await api.put(`/auth/roles/${pk}/`, { ...data, permission_ids: selectedIds });
      router.push("/admin/roles");
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : "Failed to update role.");
    } finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this role?")) return;
    setDeleting(true);
    try {
      await api.delete(`/auth/roles/${pk}/`);
      router.push("/admin/roles");
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : "Failed to delete role.");
    } finally { setDeleting(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Edit Role</h1>
            <p className="text-muted-foreground">{roleData?.name || "Loading..."}</p>
          </div>
          <div className="flex gap-2">
            {roleData && !roleData.is_system_role && (
              <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                {deleting ? "Deleting..." : "Delete"}
              </Button>
            )}
            <Button variant="outline" onClick={() => router.push("/admin/roles")}>
              Back to Roles
            </Button>
          </div>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {loading ? <SkeletonDetail /> : roleData && (
          <div className="space-y-6">
            <RoleForm
              initial={roleData}
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
