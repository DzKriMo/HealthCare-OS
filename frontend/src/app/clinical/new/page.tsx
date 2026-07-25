"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EncounterForm } from "@/components/clinical/encounter-form";
import { api } from "@/lib/api/client";

interface PatientOption {
  id: string; first_name: string; last_name: string;
}

export default function NewEncounterPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadPatients();
  }, [isAuthenticated]);

  const loadPatients = async () => {
    setLoadingPatients(true);
    try {
      const data = await api.get<{ results: PatientOption[] }>("/patients/?limit=500");
      setPatients(data.results);
    } catch {
      setPageError("Failed to load patients.");
    } finally { setLoadingPatients(false); }
  };

  const handleSubmit = async (formData: Record<string, unknown>) => {
    setSubmitting(true);
    setPageError("");
    try {
      const result = await api.post<{ id: string }>("/clinical/encounters/", formData);
      router.push(`/clinical/${result.id}`);
    } catch {
      setPageError("Failed to create encounter.");
      setSubmitting(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/clinical")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to encounters
        </Button>

        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Encounter</h1>
          <p className="text-muted-foreground">Create a new clinical encounter record.</p>
        </div>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>
        )}

        {loadingPatients ? (
          <SkeletonTable rows={5} />
        ) : (
          <EncounterForm
            patients={patients}
            onSubmit={handleSubmit}
            loading={submitting}
          />
        )}
      </div>
    </DashboardShell>
  );
}
