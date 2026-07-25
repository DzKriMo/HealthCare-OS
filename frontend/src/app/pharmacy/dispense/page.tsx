"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { DispenseForm } from "@/components/pharmacy/dispense-form";
import { api, ApiRequestError } from "@/lib/api/client";

interface DispenseRecord {
  id: string; prescription: string; drug_name: string;
  patient_name: string; quantity: number; is_refill: boolean;
  copay_charged: string; dispensed_by_name: string;
  created_at: string; notes: string;
}

interface PrescriptionSummary {
  id: string; drug_name: string; dosage: string;
  frequency: string; patient_name: string;
  quantity_prescribed: number; quantity_dispensed: number;
  refills_remaining: number; status: string;
}

export default function DispensePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [prescriptions, setPrescriptions] = useState<PrescriptionSummary[]>([]);
  const [dispenseHistory, setDispenseHistory] = useState<DispenseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [dispensing, setDispensing] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [formKey, setFormKey] = useState(0);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated) { loadPrescriptions(); loadHistory(); } }, [isAuthenticated]);

  const loadPrescriptions = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: PrescriptionSummary[] }>("/pharmacy/prescriptions/?status=issued&status=partially_filled");
      setPrescriptions(data.results);
    } catch { setPageError("Failed to load prescriptions."); }
    finally { setLoading(false); }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await api.get<{ results: DispenseRecord[] }>("/pharmacy/dispense/");
      setDispenseHistory(data.results);
    } catch { /* non-critical */ }
    finally { setHistoryLoading(false); }
  };

  const handleDispense = async (data: { prescription: string; quantity: number; copay_charged: number; is_refill: boolean; notes: string }) => {
    setDispensing(true); setPageError(""); setSuccessMsg("");
    try {
      await api.post("/pharmacy/dispense/", data);
      setSuccessMsg("Medication dispensed successfully.");
      setFormKey((k) => k + 1);
      await loadPrescriptions();
      await loadHistory();
    } catch (err) {
      setPageError(err instanceof ApiRequestError ? err.message : "Failed to dispense.");
    } finally { setDispensing(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dispense Medication</h1>
            <p className="text-muted-foreground">Dispense an issued or partially filled prescription.</p>
          </div>
          <Button variant="outline" onClick={() => router.push("/pharmacy")}>
            <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
          </Button>
        </div>

        {successMsg && (
          <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">{successMsg}</div>
        )}

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>
        )}

        {loading ? (
          <SkeletonTable rows={4} />
        ) : (
          <DispenseForm
            key={formKey}
            onSubmit={handleDispense}
            loading={dispensing}
            onCancel={() => router.push("/pharmacy")}
            prescriptions={prescriptions}
          />
        )}

        <Card>
          <CardHeader><CardTitle className="text-lg">Dispense History</CardTitle></CardHeader>
          <CardContent>
            {historyLoading ? <SkeletonTable rows={4} /> : dispenseHistory.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Date</th>
                    <th className="pb-2 font-medium">Drug</th>
                    <th className="pb-2 font-medium">Patient</th>
                    <th className="pb-2 font-medium">Qty</th>
                    <th className="pb-2 font-medium">Refill</th>
                    <th className="pb-2 font-medium">Copay</th>
                    <th className="pb-2 font-medium">Dispensed By</th>
                  </tr>
                </thead>
                <tbody>
                  {dispenseHistory.map((dr) => (
                    <tr key={dr.id} className="border-b last:border-0">
                      <td className="py-2">{new Date(dr.created_at).toLocaleDateString()}</td>
                      <td className="py-2">{dr.drug_name}</td>
                      <td className="py-2">{dr.patient_name}</td>
                      <td className="py-2">{dr.quantity}</td>
                      <td className="py-2">{dr.is_refill ? "Yes" : "No"}</td>
                      <td className="py-2">${Number(dr.copay_charged || 0).toFixed(2)}</td>
                      <td className="py-2">{dr.dispensed_by_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-muted-foreground">No dispense history.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
