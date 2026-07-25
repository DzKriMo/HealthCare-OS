"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

const fhirResources = [
  { name: "Patient", endpoint: "Patient", color: "bg-blue-100 text-blue-800", icon: "users" },
  { name: "Observation", endpoint: "Observation", color: "bg-green-100 text-green-800", icon: "activity" },
  { name: "Encounter", endpoint: "Encounter", color: "bg-purple-100 text-purple-800", icon: "calendar" },
  { name: "MedicationRequest", endpoint: "MedicationRequest", color: "bg-yellow-100 text-yellow-800", icon: "pill" },
  { name: "AllergyIntolerance", endpoint: "AllergyIntolerance", color: "bg-red-100 text-red-800", icon: "alertTriangle" },
  { name: "Condition", endpoint: "Condition", color: "bg-pink-100 text-pink-800", icon: "heartPulse" },
  { name: "Immunization", endpoint: "Immunization", color: "bg-indigo-100 text-indigo-800", icon: "syringe" },
  { name: "Practitioner", endpoint: "Practitioner", color: "bg-teal-100 text-teal-800", icon: "stethoscope" },
  { name: "Coverage", endpoint: "Coverage", color: "bg-orange-100 text-orange-800", icon: "shield" },
  { name: "DiagnosticReport", endpoint: "DiagnosticReport", color: "bg-cyan-100 text-cyan-800", icon: "fileText" },
  { name: "Medication", endpoint: "Medication", color: "bg-amber-100 text-amber-800", icon: "pill" },
];

export default function FHIRPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [capability, setCapability] = useState<any>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) fetchMeta();
  }, [isAuthenticated]);

  const fetchMeta = async () => {
    try { setCapability(await api.get("/fhir/metadata")); } catch { /* ignore */ }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  const resources = capability?.rest?.[0]?.resource || [];

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">FHIR R4 Compliance</h1>
            <p className="text-sm text-muted-foreground">
              FHIR v{capability?.fhirVersion || "4.0.1"} · {resources.length} resources · {capability?.rest?.[0]?.mode || "server"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/fhir/browser")}>
              <Icons.search className="mr-2 h-4 w-4" /> Resource Browser
            </Button>
            <Button variant="outline" onClick={() => router.push("/fhir/export")}>
              <Icons.download className="mr-2 h-4 w-4" /> Export
            </Button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">FHIR Version</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{capability?.fhirVersion || "4.0.1"}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Resources</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{resources.length}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Format</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">JSON</div></CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader><CardTitle>FHIR Resources</CardTitle></CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {fhirResources.map((res) => {
                const capRes = resources.find((r: any) => r.type === res.name);
                const interactions = capRes?.interaction?.map((i: any) => i.code).join(", ") || "read-only";
                return (
                  <div key={res.name} className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${res.color}`}>{res.name}</span>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{interactions}</div>
                    </div>
                    <Button size="sm" variant="ghost" onClick={() => router.push(`/fhir/browser?resource=${res.endpoint}`)}>
                      <Icons.chevronDown className="h-4 w-4 -rotate-90" />
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>SMART on FHIR</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <div className="text-sm font-medium">OAuth 2.0 / SMART on FHIR</div>
                <div className="text-xs text-muted-foreground">Bearer token authentication for third-party apps</div>
              </div>
              <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">Configured</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <div className="text-sm font-medium">Audit Trail (FHIR AuditEvent)</div>
                <div className="text-xs text-muted-foreground">All FHIR operations logged to immutable audit trail</div>
              </div>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">Active</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <div className="text-sm font-medium">Field-Level Encryption</div>
                <div className="text-xs text-muted-foreground">PHI encrypted at rest (Fernet AES-128)</div>
              </div>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">Active</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
