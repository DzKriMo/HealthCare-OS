"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

const exportResources = [
  { name: "All Patients", endpoint: "Patient", icon: "users" },
  { name: "All Encounters", endpoint: "Encounter", icon: "calendar" },
  { name: "Active Medications", endpoint: "MedicationRequest?status=active", icon: "pill" },
  { name: "All Allergies", endpoint: "AllergyIntolerance", icon: "alertTriangle" },
  { name: "All Conditions", endpoint: "Condition", icon: "heartPulse" },
  { name: "Immunization Records", endpoint: "Immunization", icon: "syringe" },
  { name: "Practitioners", endpoint: "Practitioner", icon: "stethoscope" },
  { name: "Insurance Coverage", endpoint: "Coverage", icon: "shield" },
  { name: "Diagnostic Reports", endpoint: "DiagnosticReport", icon: "fileText" },
];

export default function FHIRExportPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [exporting, setExporting] = useState<string | null>(null);
  const [exported, setExported] = useState<string | null>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const handleExport = async (endpoint: string) => {
    setExporting(endpoint);
    setExported(null);
    try {
      const data = await api.get(`/fhir/${endpoint}`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = `fhir-${endpoint.replace(/[?&]/g, "-")}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExported(endpoint);
    } catch { /* ignore */ }
    finally { setExporting(null); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/fhir")}>
          ← Back
        </Button>

        <Card>
          <CardHeader><CardTitle>FHIR Data Export</CardTitle></CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Export clinical data as standard FHIR R4 JSON. Files can be imported into any FHIR-compliant system.
            </p>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {exportResources.map((res) => (
                <div key={res.endpoint} className="flex items-center justify-between rounded-lg border p-4">
                  <span className="text-sm font-medium">{res.name}</span>
                  <Button
                    size="sm"
                    variant={exported === res.endpoint ? "secondary" : "outline"}
                    disabled={exporting === res.endpoint}
                    onClick={() => handleExport(res.endpoint)}
                  >
                    {exporting === res.endpoint ? "Exporting..." : exported === res.endpoint ? "Exported!" : "Export"}
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Bulk Export ($export)</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              For bulk FHIR export conforming to the Bulk Data Access (STU2) specification,
              use the FHIR API directly with the Accept header <code>application/fhir+json</code>.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
