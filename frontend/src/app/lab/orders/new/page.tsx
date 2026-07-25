"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { TestCatalogSelect } from "@/components/laboratory/test-catalog-select";
import { api, ApiRequestError } from "@/lib/api/client";

export default function NewLabOrderPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patients, setPatients] = useState<{ id: string; label: string }[]>([]);
  const [patient, setPatient] = useState("");
  const [selectedTests, setSelectedTests] = useState<string[]>([]);
  const [priority, setPriority] = useState("routine");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadPatients();
  }, [isAuthenticated]);

  const loadPatients = async () => {
    try {
      const p = await api.get<{ results: { id: string; full_name: string }[] }>("/patients/?limit=500");
      setPatients(p.results.map((x) => ({ id: x.id, label: x.full_name })));
    } catch { /* empty state */ }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!patient) { setError("Select a patient."); return; }
    if (selectedTests.length === 0) { setError("Select at least one test."); return; }

    setSubmitting(true);
    try {
      const created = await api.post<{ id: string }>("/lab/orders/", {
        patient,
        test_ids: selectedTests,
        priority: priority || undefined,
        notes: notes || undefined,
      });
      router.push(`/lab/orders/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to create lab order.");
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => router.push("/lab")}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
          </Button>
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Lab Order</h1>
          <p className="text-muted-foreground">Order laboratory tests for a patient.</p>
        </div>

        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Patient</CardTitle></CardHeader>
            <CardContent>
              <select value={patient} onChange={(e) => setPatient(e.target.value)} className={selectCls} required>
                <option value="">Select patient...</option>
                {patients.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
              </select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Tests</CardTitle></CardHeader>
            <CardContent>
              <TestCatalogSelect selectedIds={selectedTests} onChange={setSelectedTests} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Details</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="priority">Priority</Label>
                <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value)} className={selectCls}>
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="stat">STAT</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="notes">Notes</Label>
                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  placeholder="Clinical notes or instructions..."
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>{submitting ? "Creating..." : "Create Order"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/lab")}>Cancel</Button>
          </div>
        </form>
      </div>
    </DashboardShell>
  );
}
