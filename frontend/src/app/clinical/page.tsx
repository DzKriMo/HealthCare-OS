"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EncounterCard } from "@/components/clinical/encounter-card";
import { api } from "@/lib/api/client";

interface EncounterSummary {
  id: string; encounter_date: string; status: string;
  practitioner_name: string; subjective: string | null;
  objective: string | null; assessment: string | null; plan: string | null;
  patient_name?: string;
}

const STATUS_OPTIONS = ["", "draft", "signed", "completed"];

export default function ClinicalPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [encounters, setEncounters] = useState<EncounterSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) load(); }, [isAuthenticated, statusFilter, dateFrom, dateTo]);

  const load = async () => {
    setLoading(true);
    setPageError("");
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (searchQuery) params.set("search", searchQuery);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const qs = params.toString();
      const data = await api.get<{ results: EncounterSummary[] }>(`/clinical/encounters/${qs ? `?${qs}` : ""}`);
      setEncounters(data.results);
    } catch {
      setPageError("Failed to load encounters.");
    } finally { setLoading(false); }
  };

  const filtered = searchQuery
    ? encounters.filter((e) => (e.patient_name || "").toLowerCase().includes(searchQuery.toLowerCase()))
    : encounters;

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  const selectCls = "flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Clinical Encounters</h1>
            <p className="text-muted-foreground">{encounters.length} encounters</p>
          </div>
          <Button onClick={() => router.push("/clinical/new")}>
            <Icons.plus className="mr-2 h-4 w-4" /> New Encounter
          </Button>
        </div>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {pageError}
            <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        <div className="flex gap-2 flex-wrap items-end">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={selectCls}>
            {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
          </select>
          <Input
            placeholder="Search by patient name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-xs"
          />
          <div className="flex items-center gap-1">
            <label className="text-xs text-muted-foreground">From</label>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-40" />
          </div>
          <div className="flex items-center gap-1">
            <label className="text-xs text-muted-foreground">To</label>
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-40" />
          </div>
        </div>

        {loading ? (
          <SkeletonTable rows={8} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((enc) => (
              <EncounterCard
                key={enc.id}
                encounter={enc}
                onClick={() => router.push(`/clinical/${enc.id}`)}
              />
            ))}
            {filtered.length === 0 && (
              <div className="col-span-full rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.stethoscope className="mx-auto mb-3 h-8 w-8" />
                <p>No encounters found.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
