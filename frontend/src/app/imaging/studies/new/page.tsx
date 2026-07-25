"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { SkeletonDetail } from "@/components/ui/skeleton";
import { StudyForm } from "@/components/imaging/study-form";
import { api } from "@/lib/api/client";

interface PatientSummary {
  id: string;
  first_name: string;
  last_name: string;
}

interface CreatedStudy {
  id: string;
}

export default function NewStudyPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [loading, setLoading] = useState(true);
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
    try {
      const data = await api.get<{ results: PatientSummary[] }>("/patients/?limit=500");
      setPatients(data.results);
    } catch { setPageError("Failed to load patients."); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (formData: {
    patient: string;
    modality: string;
    body_part: string;
    protocol: string;
    priority: string;
    reason: string;
  }) => {
    setSubmitting(true);
    setPageError("");
    try {
      const created = await api.post<CreatedStudy>("/imaging/studies/", formData);
      router.push(`/imaging/studies/${created.id}`);
    } catch (err: unknown) {
      setPageError(err instanceof Error ? err.message : "Failed to create study.");
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell
      user={user}
      onLogout={logout}
      breadcrumbs={[
        { label: "Imaging", href: "/imaging" },
        { label: "New Study" },
      ]}
    >
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push("/imaging")}>
            <Icons.chevronDown className="h-5 w-5 rotate-90" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Order New Study</h1>
            <p className="text-sm text-muted-foreground">Fill in the details to place a new imaging order.</p>
          </div>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        {loading ? (
          <SkeletonDetail />
        ) : (
          <StudyForm patients={patients} onSubmit={handleSubmit} loading={submitting} />
        )}
      </div>
    </DashboardShell>
  );
}
