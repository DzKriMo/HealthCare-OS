"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { EncounterForm } from "@/components/clinical/encounter-form";
import { VitalsDisplay } from "@/components/clinical/vitals-display";
import { VitalsForm } from "@/components/clinical/vitals-form";
import { DiagnosisList } from "@/components/clinical/diagnosis-list";
import { ReferralList } from "@/components/clinical/referral-list";
import { VaccinationList } from "@/components/clinical/vaccination-list";
import { SOAPEditor } from "@/components/clinical/soap-editor";
import { api } from "@/lib/api/client";

interface EncounterFull {
  id: string; encounter_date: string; status: string;
  practitioner_name: string; patient: string; patient_name: string;
  subjective: string | null; objective: string | null;
  assessment: string | null; plan: string | null;
}

interface VitalsEntry {
  id: string; encounter: string; patient: string;
  blood_pressure_systolic: number; blood_pressure_diastolic: number;
  heart_rate: number; temperature: number;
  respiratory_rate: number; oxygen_saturation: number;
  weight: number; height: number; bmi: number;
  recorded_at: string;
}

const STATUS_BADGE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  in_progress: "bg-blue-100 text-blue-700",
  signed: "bg-green-100 text-green-700",
  completed: "bg-purple-100 text-purple-700",
};

export default function EncounterDetailPage() {
  const router = useRouter();
  const params = useParams();
  const encounterId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [encounter, setEncounter] = useState<EncounterFull | null>(null);
  const [vitals, setVitals] = useState<VitalsEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [signing, setSigning] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && encounterId) load();
  }, [isAuthenticated, encounterId]);

  const load = async () => {
    setLoading(true);
    setPageError("");
    try {
      const [encData, vitalsData] = await Promise.all([
        api.get<EncounterFull>(`/clinical/encounters/${encounterId}/`),
        api.get<{ results: VitalsEntry[] }>(`/clinical/vitals/?encounter=${encounterId}`),
      ]);
      setEncounter(encData);
      setVitals(vitalsData.results);
    } catch {
      setPageError("Failed to load encounter.");
    } finally { setLoading(false); }
  };

  const handleSign = async () => {
    setSigning(true);
    try {
      await api.post(`/clinical/encounters/${encounterId}/sign/`);
      await load();
    } catch {
      setPageError("Failed to sign encounter.");
    } finally { setSigning(false); }
  };

  const handleEditSubmit = async (data: Record<string, unknown>) => {
    setSaving(true);
    try {
      await api.patch(`/clinical/encounters/${encounterId}/`, data);
      setEditMode(false);
      await load();
    } catch {
      setPageError("Failed to update encounter.");
    } finally { setSaving(false); }
  };

  const handleVitalsSubmit = async (data: Record<string, unknown>) => {
    await api.post("/clinical/vitals/", { ...data, patient: encounter?.patient, encounter: encounterId });
    const vitalsData = await api.get<{ results: VitalsEntry[] }>(`/clinical/vitals/?encounter=${encounterId}`);
    setVitals(vitalsData.results);
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
      <div className="mx-auto max-w-6xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/clinical")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to encounters
        </Button>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {pageError}
          </div>
        )}

        {loading && !encounter && (
          <div className="space-y-4">
            <SkeletonCard />
          </div>
        )}

        {encounter && !editMode && (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex-1 min-w-[200px]">
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{encounter.patient_name}</h1>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[encounter.status] || ""}`}>
                    {encounter.status.replace("_", " ")}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {new Date(encounter.encounter_date).toLocaleDateString()} · {encounter.practitioner_name}
                </p>
              </div>
              <div className="flex gap-2">
                {(encounter.status === "draft" || encounter.status === "in_progress") && (
                  <Button variant="outline" onClick={() => setEditMode(true)}>
                    <Icons.settings className="mr-2 h-4 w-4" /> Edit
                  </Button>
                )}
                {(encounter.status === "draft" || encounter.status === "in_progress") && (
                  <Button onClick={handleSign} disabled={signing}>
                    {signing ? "Signing..." : "Sign"}
                  </Button>
                )}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-lg">Subjective</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap">{encounter.subjective || "—"}</p></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-lg">Objective</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap">{encounter.objective || "—"}</p></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-lg">Assessment</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap">{encounter.assessment || "—"}</p></CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-lg">Plan</CardTitle></CardHeader>
                <CardContent><p className="text-sm whitespace-pre-wrap">{encounter.plan || "—"}</p></CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader><CardTitle className="text-lg">Vitals</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <VitalsDisplay vitals={vitals} />
                <VitalsForm onSubmit={handleVitalsSubmit} />
              </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
              <DiagnosisList patientId={encounter.patient} encounterId={encounter.id} />
              <ReferralList patientId={encounter.patient} encounterId={encounter.id} />
            </div>

            <VaccinationList patientId={encounter.patient} />
          </>
        )}

        {encounter && editMode && (
          <>
            <div>
              <h1 className="text-2xl font-bold">Edit Encounter</h1>
              <p className="text-sm text-muted-foreground">{encounter.patient_name}</p>
            </div>
            <SOAPEditor
              subjective={encounter.subjective || ""}
              objective={encounter.objective || ""}
              assessment={encounter.assessment || ""}
              plan={encounter.plan || ""}
              onSubjectiveChange={(v: string) => setEncounter({ ...encounter, subjective: v })}
              onObjectiveChange={(v: string) => setEncounter({ ...encounter, objective: v })}
              onAssessmentChange={(v: string) => setEncounter({ ...encounter, assessment: v })}
              onPlanChange={(v: string) => setEncounter({ ...encounter, plan: v })}
            />
            <div className="flex gap-2">
              <Button onClick={() => handleEditSubmit({
                subjective: encounter.subjective,
                objective: encounter.objective,
                assessment: encounter.assessment,
                plan: encounter.plan,
              })} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </Button>
              <Button variant="outline" onClick={() => { setEditMode(false); load(); }}>
                Cancel
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
