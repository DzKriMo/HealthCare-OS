"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { UserForm } from "@/components/admin/user-form";
import { SkeletonDetail } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

interface Role {
  id: string; name: string;
}

interface UserData {
  id: string; email: string; full_name: string; role_id: string;
  is_active: boolean; last_login: string | null;
}

export default function AdminUserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const pk = params?.id as string;

  useEffect(() => {
    if (!isAuthenticated || !pk) return;
    Promise.all([
      api.get<UserData>(`/auth/users/${pk}/`),
      api.get<{ results: Role[] }>("/auth/roles/").catch(() => ({ results: [] })),
    ]).then(([u, r]) => {
      setUserData(u);
      setRoles(r.results);
    }).catch(() => setPageError("Failed to load user."))
    .finally(() => setLoading(false));
  }, [isAuthenticated, pk]);

  const handleSubmit = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      await api.put(`/auth/users/${pk}/`, data);
      router.push("/admin/users");
    } catch (e: unknown) {
      setPageError(e instanceof Error ? e.message : "Failed to update user.");
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
            <h1 className="text-3xl font-bold tracking-tight">Edit User</h1>
            <p className="text-muted-foreground">{userData?.email || "Loading..."}</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/admin/users")}>
            Back to Users
          </Button>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {loading ? <SkeletonDetail /> : userData && (
          <UserForm
            initial={userData}
            roles={roles}
            onSubmit={handleSubmit}
            loading={saving}
          />
        )}
      </div>
    </DashboardShell>
  );
}
