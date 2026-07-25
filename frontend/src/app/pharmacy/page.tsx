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
import { PrescriptionCard } from "@/components/pharmacy/prescription-card";
import { api } from "@/lib/api/client";

interface PrescriptionSummary {
  id: string; patient_name: string; drug_name: string;
  dosage: string; frequency: string; status: string;
  prescribed_by_name: string; is_controlled: boolean;
  controlled_schedule?: string; issued_date: string;
}

interface DashboardSummary {
  pending_count: number;
  dispensed_today: number;
}

const STATUSES = ["", "draft", "issued", "partially_filled", "filled", "cancelled", "expired"];

export default function PharmacyPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [prescriptions, setPrescriptions] = useState<PrescriptionSummary[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchPatient, setSearchPatient] = useState("");
  const [controlledOnly, setControlledOnly] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) { load(); loadDashboard(); } }, [isAuthenticated, statusFilter]);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (searchPatient) params.set("patient", searchPatient);
      if (controlledOnly) params.set("controlled", "true");
      const q = params.toString();
      const data = await api.get<{ results: PrescriptionSummary[] }>(`/pharmacy/prescriptions/${q ? `?${q}` : ""}`);
      setPrescriptions(data.results);
    } catch { setPageError("Failed to load prescriptions."); }
    finally { setLoading(false); }
  };

  const loadDashboard = async () => {
    try {
      const data = await api.get<DashboardSummary>("/pharmacy/dashboard/");
      setDashboard(data);
    } catch { /* non-critical */ }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  const filtered = searchPatient
    ? prescriptions.filter((p) => p.patient_name.toLowerCase().includes(searchPatient.toLowerCase()))
    : prescriptions;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Prescriptions</h1>
            <p className="text-muted-foreground">{prescriptions.length} prescriptions</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/pharmacy/dispense")}>
              <Icons.creditCard className="mr-2 h-4 w-4" /> Dispense
            </Button>
            <Button onClick={() => router.push("/pharmacy/new")}>
              <Icons.plus className="mr-2 h-4 w-4" /> New Prescription
            </Button>
          </div>
        </div>

        {dashboard && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold">{dashboard.pending_count}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <p className="text-sm text-muted-foreground">Dispensed Today</p>
                <p className="text-2xl font-bold">{dashboard.dispensed_today}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="flex gap-2 flex-wrap items-center">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
          <Input placeholder="Search by patient name..." value={searchPatient} onChange={(e) => setSearchPatient(e.target.value)} className="max-w-xs" />
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={controlledOnly}
              onChange={(e) => setControlledOnly(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            Controlled only
          </label>
        </div>

        {loading ? <SkeletonTable rows={8} /> : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((rx) => (
              <PrescriptionCard
                key={rx.id}
                prescription={rx}
                onClick={() => router.push(`/pharmacy/${rx.id}`)}
              />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.fileText className="mx-auto mb-3 h-8 w-8" />
                <p>No prescriptions found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
