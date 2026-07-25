"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { PatientForm } from "@/components/patients/patient-form";

export default function EditPatientPage() {
  const router = useRouter();
  const params = useParams();
  const patientId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [initialData, setInitialData] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && patientId) load();
  }, [isAuthenticated, patientId]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<Record<string, unknown>>(`/patients/${patientId}/`);
      setInitialData({
        first_name: String(data.first_name || ""),
        middle_name: String(data.middle_name || ""),
        last_name: String(data.last_name || ""),
        date_of_birth: String(data.date_of_birth || ""),
        gender: String(data.gender || "unknown"),
        blood_type: String(data.blood_type || ""),
        marital_status: String(data.marital_status || ""),
        national_id: "",
        phone_primary: String(data.phone_primary || ""),
        phone_secondary: String(data.phone_secondary || ""),
        email: String(data.email || ""),
        address_line1: String(data.address_line1 || ""),
        address_line2: String(data.address_line2 || ""),
        city: String(data.city || ""),
        state: String(data.state || ""),
        postal_code: String(data.postal_code || ""),
        country: String(data.country || "US"),
      });
    } catch {
      setError("Failed to load patient data.");
    } finally {
      setLoading(false);
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
        <div>
          <Button variant="ghost" size="sm" onClick={() => router.push(`/patients/${patientId}`)}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to patient
          </Button>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Edit Patient</h1>
          <p className="text-muted-foreground">Update patient demographics and contact information.</p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>
        )}

        {loading && <SkeletonCard />}

        {initialData && !loading && (
          <PatientForm initialData={initialData} patientId={patientId} isEdit />
        )}
      </div>
    </DashboardShell>
  );
}
