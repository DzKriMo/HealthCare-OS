"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard } from "@/components/ui/skeleton";
import { DispenseForm } from "@/components/pharmacy/dispense-form";
import { api, ApiRequestError } from "@/lib/api/client";

interface DispenseRecord {
  id: string; quantity: number; is_refill: boolean;
  dispensed_by_name: string; copay_charged: string;
  created_at: string; notes: string;
}

interface PrescriptionDetail {
  id: string; patient: string; patient_name: string;
  encounter: string; drug_name: string; drug_code: string;
  dosage: string; frequency: string; duration_days: number;
  route: string; instructions: string; notes: string;
  quantity_prescribed: number; quantity_dispensed: number;
  refills_authorized: number; refills_remaining: number;
  daw: boolean; is_controlled: boolean; controlled_schedule: string;
  status: string; prescribed_by: string; prescribed_by_name: string;
  issued_date: string; expiry_date: string;
  dispense_records: DispenseRecord[];
}

const STATUS_BADGES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700", issued: "bg-blue-100 text-blue-700",
  partially_filled: "bg-yellow-100 text-yellow-700", filled: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700", expired: "bg-orange-100 text-orange-700",
};

export default function PrescriptionDetailPage() {
  const router = useRouter(); const params = useParams();
  const rxId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [rx, setRx] = useState<PrescriptionDetail | null>(null);
  const [loadError, setLoadError] = useState(""); const [loading, setLoading] = useState(true);
  const [showDispense, setShowDispense] = useState(false);
  const [dispensing, setDispensing] = useState(false); const [dispenseError, setDispenseError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => { if (!authLoading && !isAuthenticated) router.push("/login"); }, [authLoading, isAuthenticated, router]);
  useEffect(() => { if (isAuthenticated && rxId) load(); }, [isAuthenticated, rxId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try { const d = await api.get<PrescriptionDetail>(`/pharmacy/prescriptions/${rxId}/`); setRx(d); }
    catch { setLoadError("Failed to load prescription."); } finally { setLoading(false); }
  };

  const handleDispense = async (data: { prescription: string; quantity: number; copay_charged: number; is_refill: boolean; notes: string }) => {
    setDispensing(true); setDispenseError("");
    try {
      await api.post("/pharmacy/dispense/", data);
      setShowDispense(false);
      await load();
    } catch (err) {
      setDispenseError(err instanceof ApiRequestError ? err.message : "Failed to dispense.");
    } finally { setDispensing(false); }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  const canDispense = rx && !["filled", "cancelled", "expired"].includes(rx.status);

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-4xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/pharmacy")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        {loadError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{loadError} <Button variant="link" size="sm" onClick={load}>Retry</Button></div>}
        {loading && !rx && <SkeletonCard />}

        {rx && (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{rx.drug_name}</h1>
                  <span className={`rounded-full px-3 py-1 text-sm font-medium ${STATUS_BADGES[rx.status] || ""}`}>
                    {rx.status.replace(/_/g, " ")}
                  </span>
                  {rx.is_controlled && (
                    <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
                      C-II{rx.controlled_schedule ? `-${rx.controlled_schedule}` : ""}
                    </span>
                  )}
                </div>
                <p className="text-muted-foreground">{rx.dosage} &middot; {rx.frequency}</p>
                <div className="flex gap-4 text-sm text-muted-foreground mt-1">
                  {rx.issued_date && <span>Issued: {new Date(rx.issued_date).toLocaleDateString()}</span>}
                  {rx.expiry_date && <span>Expires: {new Date(rx.expiry_date).toLocaleDateString()}</span>}
                </div>
              </div>
              <div className="flex gap-2">
                {canDispense && (
                  <Button onClick={() => setShowDispense(!showDispense)}>
                    <Icons.creditCard className="mr-2 h-4 w-4" /> Dispense
                  </Button>
                )}
              </div>
            </div>

            {dispenseError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{dispenseError}</div>}

            {showDispense && canDispense && (
              <DispenseForm
                onSubmit={handleDispense}
                loading={dispensing}
                onCancel={() => setShowDispense(false)}
                prescriptions={[{
                  id: rx.id, drug_name: rx.drug_name, dosage: rx.dosage,
                  frequency: rx.frequency, patient_name: rx.patient_name,
                  quantity_prescribed: rx.quantity_prescribed,
                  quantity_dispensed: rx.quantity_dispensed,
                  refills_remaining: rx.refills_remaining, status: rx.status,
                }]}
              />
            )}

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-lg">Patient</CardTitle></CardHeader>
                <CardContent>
                  <p className="font-medium">{rx.patient_name}</p>
                  <Button variant="link" className="h-auto p-0 text-sm" onClick={() => router.push(`/patients/${rx.patient}`)}>
                    View patient record
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="text-lg">Prescriber</CardTitle></CardHeader>
                <CardContent>
                  <p className="font-medium">{rx.prescribed_by_name}</p>
                  <p className="text-sm text-muted-foreground">Encounter: {rx.encounter || "—"}</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader><CardTitle className="text-lg">Quantity Details</CardTitle></CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Prescribed</p>
                  <p className="text-lg font-semibold">{rx.quantity_prescribed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Dispensed</p>
                  <p className="text-lg font-semibold">{rx.quantity_dispensed}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Refills Authorized</p>
                  <p className="text-lg font-semibold">{rx.refills_authorized}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Refills Remaining</p>
                  <p className="text-lg font-semibold">{rx.refills_remaining}</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-lg">Route &amp; Instructions</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex gap-4">
                  <span className="text-muted-foreground">Route:</span><span>{rx.route || "—"}</span>
                  <span className="text-muted-foreground">DAW:</span><span>{rx.daw ? "Yes" : "No"}</span>
                  {rx.drug_code && <><span className="text-muted-foreground">Code:</span><span>{rx.drug_code}</span></>}
                </div>
                {rx.instructions && <p><span className="text-muted-foreground">Instructions:</span> {rx.instructions}</p>}
                {rx.notes && <p><span className="text-muted-foreground">Notes:</span> {rx.notes}</p>}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-lg">Dispense History</CardTitle></CardHeader>
              <CardContent>
                {rx.dispense_records && rx.dispense_records.length > 0 ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 font-medium">Date</th>
                        <th className="pb-2 font-medium">Qty</th>
                        <th className="pb-2 font-medium">Refill</th>
                        <th className="pb-2 font-medium">Copay</th>
                        <th className="pb-2 font-medium">Dispensed By</th>
                        <th className="pb-2 font-medium">Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rx.dispense_records.map((dr) => (
                        <tr key={dr.id} className="border-b last:border-0">
                          <td className="py-2">{new Date(dr.created_at).toLocaleDateString()}</td>
                          <td className="py-2">{dr.quantity}</td>
                          <td className="py-2">{dr.is_refill ? "Yes" : "No"}</td>
                          <td className="py-2">${Number(dr.copay_charged || 0).toFixed(2)}</td>
                          <td className="py-2">{dr.dispensed_by_name}</td>
                          <td className="py-2">{dr.notes || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-sm text-muted-foreground">No dispense records.</p>
                )}
              </CardContent>
            </Card>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => router.push(`/patients/${rx.patient}`)}>
                <Icons.users className="mr-2 h-4 w-4" /> View Patient
              </Button>
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}
