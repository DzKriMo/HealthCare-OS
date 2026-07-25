"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

interface UserSummary {
  id: string; full_name: string; email: string; role_name: string;
  is_active: boolean; last_login: string | null;
}

export default function AdminUsersPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) load(); }, [isAuthenticated]);

  const load = async () => {
    setLoading(true);
    try {
      const q = search ? `?search=${encodeURIComponent(search)}` : "";
      const data = await api.get<{ results: UserSummary[] }>(`/auth/users/${q}`);
      setUsers(data.results);
    } catch { setPageError("Failed to load users."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const filtered = search
    ? users.filter((u) =>
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase()))
    : users;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Users</h1>
            <p className="text-muted-foreground">{users.length} users</p>
          </div>
          <Button onClick={() => router.push("/admin/users/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New User
          </Button>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2">
          <Input placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="space-y-2">
            {filtered.map((u) => (
              <Card key={u.id} className="cursor-pointer transition-colors hover:border-primary" onClick={() => router.push(`/admin/users/${u.id}`)}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{u.full_name}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p className="truncate text-sm text-muted-foreground">{u.email}</p>
                  </div>
                  <div className="ml-4 text-right text-sm text-muted-foreground">
                    <p>{u.role_name}</p>
                    {u.last_login && <p className="text-xs">Last login: {new Date(u.last_login).toLocaleDateString()}</p>}
                  </div>
                </CardContent>
              </Card>
            ))}
            {filtered.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.users className="mx-auto mb-3 h-8 w-8" />
                <p>No users found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
