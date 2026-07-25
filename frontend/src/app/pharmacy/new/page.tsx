"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { PrescriptionForm } from "@/components/pharmacy/prescription-form";
import { api, ApiRequestError } from "@/lib/api/client";

function NewPrescriptionInner() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patients, setPatients] = useState<{ id: string; first_name: string; last_name: string }[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [correlationId, setCorrelationId] = useState<string | undefined>();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadPatients();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const loadPatients = async () => {
    try {
      const p = await api.get<{ results: { id: string; first_name: string; last_name: string }[] }>("/patients/?limit=500");
      setPatients(p.results);
    } catch { /* empty state */ }
  };

  const handleSubmit = async (formData: {
    patient: string; encounter: string; drug_name: string; drug_code: string;
    dosage: string; frequency: string; duration_days: number; route: string;
    instructions: string; quantity_prescribed: number; refills_authorized: number;
    daw: boolean; is_controlled: boolean; controlled_schedule: string;
    notes: string; expiry_date: string;
  }) => {
    setError("");
    setCorrelationId(undefined);
    setSubmitting(true);
    try {
      const created = await api.post<{ id: string }>("/pharmacy/prescriptions/", formData);
      router.push(`/pharmacy/${created.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
        setCorrelationId(err.correlationId);
      } else {
        setError("Failed to create prescription.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">New Prescription</h1>
            <p className="text-muted-foreground">Create a new medication prescription.</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/pharmacy")}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
          </Button>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
            {correlationId && <span className="mt-1 block text-xs opacity-70">Ref: {correlationId}</span>}
          </div>
        )}

        <PrescriptionForm onSubmit={handleSubmit} loading={submitting} patients={patients} />
      </div>
    </DashboardShell>
  );
}

export default function NewPrescriptionPage() {
  return (
    <Suspense fallback={null}>
      <NewPrescriptionInner />
    </Suspense>
  );
}
