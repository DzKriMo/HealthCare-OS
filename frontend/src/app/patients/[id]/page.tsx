"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface PatientDetail {
  id: string;
  display_id: string;
  full_name: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  age: number;
  gender: string;
  blood_type: string;
  phone_primary: string;
  phone_secondary: string;
  email: string;
  address_line1: string;
  city: string;
  country: string;
  allergies: { id: string; substance: string; severity: string }[];
  insurance_policies: { id: string; provider: string; policy_number: string }[];
}

export default function PatientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const patientId = params.id as string;
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && patientId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, patientId]);

  const load = async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await api.get<PatientDetail>(`/patients/${patientId}/`);
      setPatient(data);
    } catch {
      setLoadError("Failed to load patient.");
    } finally {
      setLoading(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/patients")}>
          ← Back to patients
        </Button>

        {loadError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {loadError}
            <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        {loading && !patient && (
          <div className="space-y-3">
            <div className="h-24 animate-pulse rounded-lg bg-muted" />
            <div className="h-40 animate-pulse rounded-lg bg-muted" />
          </div>
        )}

        {patient && (
          <>
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
                {patient.first_name?.[0]}{patient.last_name?.[0]}
              </div>
              <div className="flex-1">
                <h1 className="text-2xl font-bold">{patient.full_name}</h1>
                <p className="text-muted-foreground">
                  {patient.display_id} · {patient.age} yrs · {patient.gender}
                  {patient.blood_type ? ` · ${patient.blood_type}` : ""}
                </p>
              </div>
              <Button onClick={() => router.push(`/appointments/new?patient=${patient.id}`)}>
                <Icons.calendar className="mr-2 h-4 w-4" /> Book appointment
              </Button>
              <Button variant="outline" onClick={() => router.push(`/billing/new?patient=${patient.id}`)}>
                <Icons.creditCard className="mr-2 h-4 w-4" /> New invoice
              </Button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-lg">Contact</CardTitle></CardHeader>
                <CardContent className="space-y-1 text-sm">
                  <div><span className="text-muted-foreground">Phone:</span> {patient.phone_primary || "—"}</div>
                  <div><span className="text-muted-foreground">Email:</span> {patient.email || "—"}</div>
                  <div><span className="text-muted-foreground">Address:</span> {patient.address_line1 || "—"}{patient.city ? `, ${patient.city}` : ""}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-lg">Allergies</CardTitle></CardHeader>
                <CardContent className="text-sm">
                  {patient.allergies?.length ? (
                    <ul className="space-y-1">
                      {patient.allergies.map((a) => (
                        <li key={a.id}>{a.substance} <span className="text-muted-foreground">({a.severity})</span></li>
                      ))}
                    </ul>
                  ) : <span className="text-muted-foreground">No known allergies</span>}
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
