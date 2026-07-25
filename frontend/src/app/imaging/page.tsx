"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable, SkeletonCard } from "@/components/ui/skeleton";
import { StudyCard } from "@/components/imaging/study-card";
import { api } from "@/lib/api/client";

interface DashboardData {
  studies_today: number;
  pending_reports: number;
  by_modality: { modality: string; count: number }[];
}

interface StudySummary {
  id: string;
  patient_name: string;
  modality: string;
  body_part: string;
  status: string;
  priority: string;
  performed_at: string | null;
  report_status: string;
}

const STATUSES = ["", "scheduled", "in_progress", "completed", "cancelled"];

export default function ImagingPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [studies, setStudies] = useState<StudySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) { loadDashboard(); loadStudies(); } }, [isAuthenticated, statusFilter]);

  const loadDashboard = async () => {
    setDashboardLoading(true);
    try {
      const data = await api.get<DashboardData>("/imaging/dashboard/");
      setDashboard(data);
    } catch { /* non-critical */ }
    finally { setDashboardLoading(false); }
  };

  const loadStudies = async () => {
    setLoading(true);
    try {
      const q = statusFilter ? `?status=${statusFilter}` : "";
      const data = await api.get<{ results: StudySummary[] }>(`/imaging/studies/${q}`);
      setStudies(data.results);
    } catch { setPageError("Failed to load studies."); }
    finally { setLoading(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Imaging</h1>
            <p className="text-muted-foreground">{studies.length} studies</p>
          </div>
          <Button onClick={() => router.push("/imaging/studies/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New Study
          </Button>
        </div>

        {dashboardLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : dashboard && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Studies Today</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{dashboard.studies_today}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Pending Reports</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{dashboard.pending_reports}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">By Modality</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {dashboard.by_modality.map((m) => (
                  <div key={m.modality} className="flex items-center justify-between text-sm">
                    <span className="capitalize">{m.modality}</span>
                    <span className="font-medium">{m.count}</span>
                  </div>
                ))}
                {dashboard.by_modality.length === 0 && (
                  <p className="text-sm text-muted-foreground">No studies recorded.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {studies.map((study) => (
              <StudyCard
                key={study.id}
                study={study}
                onClick={() => router.push(`/imaging/studies/${study.id}`)}
              />
            ))}
            {studies.length === 0 && (
              <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.fileText className="mx-auto mb-3 h-8 w-8" />
                <p>No studies found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
