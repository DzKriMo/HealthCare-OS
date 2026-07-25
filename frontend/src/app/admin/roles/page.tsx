"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

interface RoleSummary {
  id: string; name: string; description: string; is_system_role: boolean;
}

export default function AdminRolesPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [roles, setRoles] = useState<RoleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) load(); }, [isAuthenticated]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: RoleSummary[] }>("/auth/roles/");
      setRoles(data.results);
    } catch { setPageError("Failed to load roles."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Roles</h1>
            <p className="text-muted-foreground">{roles.length} roles</p>
          </div>
          <Button onClick={() => router.push("/admin/roles/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New Role
          </Button>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {loading ? <SkeletonTable rows={5} /> : (
          <div className="space-y-2">
            {roles.map((r) => (
              <Card key={r.id} className="cursor-pointer transition-colors hover:border-primary" onClick={() => router.push(`/admin/roles/${r.id}`)}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{r.name}</span>
                      {r.is_system_role && (
                        <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                          System
                        </span>
                      )}
                    </div>
                    <p className="truncate text-sm text-muted-foreground">{r.description || "—"}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
            {roles.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.shield className="mx-auto mb-3 h-8 w-8" />
                <p>No roles found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
