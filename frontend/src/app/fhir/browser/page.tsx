"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

const resourceOptions = [
  "Patient", "Observation", "Encounter", "MedicationRequest",
  "AllergyIntolerance", "Condition", "Immunization", "Practitioner",
  "Coverage", "DiagnosticReport", "Medication",
];

export default function FHIRBrowserPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [resourceType, setResourceType] = useState(searchParams.get("resource") || "Patient");
  const [patientId, setPatientId] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  const handleQuery = async () => {
    setLoading(true);
    setError("");
    setResponse(null);
    try {
      let url = `/fhir/${resourceType}`;
      const params = new URLSearchParams();
      if (patientId) params.set("patient", patientId);
      const qs = params.toString();
      if (qs) url += `?${qs}`;
      const data = await api.get(url);
      setResponse(data);
    } catch (e: any) {
      setError(e?.message || "Query failed");
    } finally { setLoading(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/fhir")}>
          ← Back
        </Button>

        <Card>
          <CardHeader><CardTitle>FHIR Resource Browser</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <select
                className="rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={resourceType}
                onChange={(e) => setResourceType(e.target.value)}
              >
                {resourceOptions.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              <Input
                placeholder="Patient ID (optional)"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="max-w-xs"
              />
              <Button onClick={handleQuery} disabled={loading}>
                {loading ? "Querying..." : "Search"}
              </Button>
            </div>

            {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

            {response && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Type: <strong>{response.resourceType}</strong></span>
                  {response.total !== undefined && <span>· Total: <strong>{response.total}</strong></span>}
                  {response.entry && <span>· Entries: <strong>{response.entry.length}</strong></span>}
                </div>
                <pre className="max-h-[60vh] overflow-auto rounded-lg border bg-muted p-4 text-xs">
                  {JSON.stringify(response, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
