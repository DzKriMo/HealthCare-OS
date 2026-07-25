"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DashboardStats {
  total_suggestions: number;
  accepted: number;
  rejected: number;
  pending_review: number;
  fallback_rate: number;
  avg_latency_ms: number | null;
}

export default function AIDiagnosticsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [symptomInput, setSymptomInput] = useState("");
  const [symptomResult, setSymptomResult] = useState<any>(null);
  const [icd10Input, setIcd10Input] = useState("");
  const [icd10Result, setIcd10Result] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [symptomLoading, setSymptomLoading] = useState(false);
  const [icd10Loading, setIcd10Loading] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadStats();
  }, [isAuthenticated]);

  const loadStats = async () => {
    try {
      const data = await api.get<DashboardStats>("/ai/dashboard/");
      setStats(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const analyzeSymptoms = async () => {
    if (!symptomInput.trim()) return;
    setSymptomLoading(true);
    try {
      const res = await api.post("/ai/suggest/symptom-analysis/", { symptoms: symptomInput });
      setSymptomResult(res);
    } catch { setSymptomResult({ error: "Analysis failed" }); }
    finally { setSymptomLoading(false); }
  };

  const suggestICD10 = async () => {
    if (!icd10Input.trim()) return;
    setIcd10Loading(true);
    try {
      const res = await api.post("/ai/suggest/icd10/", { diagnosis_text: icd10Input });
      setIcd10Result(res);
    } catch { setIcd10Result({ error: "Suggestion failed" }); }
    finally { setIcd10Loading(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Diagnostics</h1>
            <p className="text-sm text-muted-foreground">Clinical decision support &amp; AI-assisted workflows</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/ai-diagnostics/settings")}>
            <Icons.settings className="mr-2 h-4 w-4" /> Settings
          </Button>
        </div>

        {stats && (
          <div className="grid gap-4 md:grid-cols-5">
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total_suggestions}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Accepted</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{stats.accepted}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Rejected</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-red-600">{stats.rejected}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Pending</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-yellow-600">{stats.pending_review}</div></CardContent></Card>
            <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Avg Latency</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.avg_latency_ms ? `${Math.round(stats.avg_latency_ms)}ms` : "—"}</div></CardContent></Card>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader><CardTitle>Symptom Analysis</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="symptoms">Enter symptoms</Label>
                <textarea
                  id="symptoms"
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={symptomInput}
                  onChange={(e) => setSymptomInput(e.target.value)}
                  placeholder="Describe symptoms, onset, duration, severity..."
                />
              </div>
              <Button onClick={analyzeSymptoms} disabled={symptomLoading}>
                {symptomLoading ? "Analyzing..." : "Analyze Symptoms"}
              </Button>
              {symptomResult && !symptomResult.error && (
                <div className="rounded-lg border p-4 space-y-3">
                  {symptomResult.differential_diagnoses && (
                    <div>
                      <h4 className="text-sm font-medium">Differential Diagnoses</h4>
                      {symptomResult.differential_diagnoses.map((d: any, i: number) => (
                        <div key={i} className="text-sm text-muted-foreground">• {d}</div>
                      ))}
                    </div>
                  )}
                  {symptomResult.recommended_tests && (
                    <div>
                      <h4 className="text-sm font-medium">Recommended Tests</h4>
                      {symptomResult.recommended_tests.map((t: string, i: number) => (
                        <div key={i} className="text-sm text-muted-foreground">• {t}</div>
                      ))}
                    </div>
                  )}
                  {symptomResult.urgency && (
                    <p className="text-sm"><strong>Urgency:</strong> {symptomResult.urgency}</p>
                  )}
                  {symptomResult.is_fallback && (
                    <p className="text-xs text-yellow-600">{symptomResult.reason}</p>
                  )}
                </div>
              )}
              {symptomResult?.error && <p className="text-sm text-destructive">{symptomResult.error}</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>ICD-10 Code Suggestion</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="diagnosis">Enter diagnosis</Label>
                <Input
                  id="diagnosis"
                  value={icd10Input}
                  onChange={(e) => setIcd10Input(e.target.value)}
                  placeholder="e.g. Type 2 diabetes with neuropathy"
                />
              </div>
              <Button onClick={suggestICD10} disabled={icd10Loading}>
                {icd10Loading ? "Suggesting..." : "Suggest Codes"}
              </Button>
              {icd10Result && !icd10Result.error && (
                <div className="rounded-lg border p-4 space-y-2">
                  {(icd10Result.suggestions || []).map((s: any, i: number) => (
                    <div key={i} className="flex items-center justify-between border-b pb-2 last:border-0">
                      <div>
                        <span className="font-mono text-sm font-medium">{s.code}</span>
                        <span className="ml-2 text-sm text-muted-foreground">{s.description}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {s.confidence ? `${Math.round(s.confidence * 100)}%` : ""}
                      </span>
                    </div>
                  ))}
                  {icd10Result.is_fallback && (
                    <p className="text-xs text-yellow-600">{icd10Result.reason}</p>
                  )}
                </div>
              )}
              {icd10Result?.error && <p className="text-sm text-destructive">{icd10Result.error}</p>}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
