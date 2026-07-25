"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MedicalHistoryEditor } from "@/components/patients/medical-history-editor";
import { AllergiesList } from "@/components/patients/allergies-list";
import { InsuranceList } from "@/components/patients/insurance-list";
import { EmergencyContactsList } from "@/components/patients/emergency-contacts-list";
import { ConsentManager } from "@/components/patients/consent-manager";
import { PatientBillingHistory } from "@/components/billing/patient-billing-history";
import { PatientEncounters } from "@/components/clinical/patient-encounters";
import { PatientPrescriptions } from "@/components/pharmacy/patient-prescriptions";
import { PatientLabOrders } from "@/components/laboratory/patient-lab-orders";
import { PatientStudies } from "@/components/imaging/patient-studies";
import { VitalsDisplay } from "@/components/clinical/vitals-display";
import { VitalsForm } from "@/components/clinical/vitals-form";
import { DiagnosisList } from "@/components/clinical/diagnosis-list";
import { VaccinationList } from "@/components/clinical/vaccination-list";
import { PatientTimeline } from "@/components/patients/patient-timeline";
import { PatientConsultations } from "@/components/telemedicine/patient-consultations";

interface PatientFull {
  id: string; display_id: string; full_name: string;
  first_name: string; middle_name: string; last_name: string;
  date_of_birth: string; age: number; gender: string;
  blood_type: string; marital_status: string;
  national_id_type: string;
  phone_primary: string; phone_secondary: string; email: string;
  address_line1: string; address_line2: string; city: string;
  state: string; postal_code: string; country: string;
  is_active: boolean; registration_date: string;
  allergies: { id: string; substance: string; severity: string }[];
  emergency_contacts: { id: string; name: string; relationship: string; phone_primary: string }[];
  insurance_policies: { id: string; provider: string; policy_number: string; coverage_type: string }[];
  active_medications: { id: string; drug_name: string; dosage: string; frequency: string }[];
  has_active_consents: boolean;
  created_at: string; updated_at: string;
}

export default function PatientDetailPage() {
  const router = useRouter();
  const params = useParams();
  const patientId = params.id as string;
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patient, setPatient] = useState<PatientFull | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("demographics");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated && patientId) load();
  }, [isAuthenticated, patientId]);

  const load = async () => {
    setLoading(true); setLoadError("");
    try {
      const data = await api.get<PatientFull>(`/patients/${patientId}/`);
      setPatient(data);
    } catch {
      setLoadError("Failed to load patient.");
    } finally { setLoading(false); }
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
        <Button variant="ghost" size="sm" onClick={() => router.push("/patients")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back to patients
        </Button>

        {loadError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {loadError}
            <Button variant="link" size="sm" onClick={load}>Retry</Button>
          </div>
        )}

        {loading && !patient && (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonTable rows={4} />
          </div>
        )}

        {patient && (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
                {patient.first_name?.[0]}{patient.last_name?.[0]}
              </div>
              <div className="flex-1 min-w-[200px]">
                <h1 className="text-2xl font-bold">{patient.full_name}</h1>
                <p className="text-sm text-muted-foreground">
                  {patient.display_id} · {patient.age} yrs · {patient.gender}
                  {patient.blood_type ? ` · ${patient.blood_type}` : ""} · {patient.city || "—"}
                </p>
              </div>
              <Button variant="outline" onClick={() => router.push(`/patients/${patient.id}/edit`)}>
                <Icons.settings className="mr-2 h-4 w-4" /> Edit
              </Button>
              <Button onClick={() => router.push(`/appointments/new?patient=${patient.id}`)}>
                <Icons.calendar className="mr-2 h-4 w-4" /> Book appointment
              </Button>
              <Button variant="outline" onClick={() => router.push(`/billing/new?patient=${patient.id}`)}>
                <Icons.creditCard className="mr-2 h-4 w-4" /> New invoice
              </Button>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
              <TabsList className="flex-wrap">
                <TabsTrigger value="demographics">Demographics</TabsTrigger>
                <TabsTrigger value="history">Medical History</TabsTrigger>
                <TabsTrigger value="allergies">Allergies</TabsTrigger>
                <TabsTrigger value="medications">Medications</TabsTrigger>
                <TabsTrigger value="insurance">Insurance</TabsTrigger>
                <TabsTrigger value="contacts">Contacts</TabsTrigger>
                <TabsTrigger value="consents">Consents</TabsTrigger>
                <TabsTrigger value="encounters">Encounters</TabsTrigger>
                <TabsTrigger value="vitals">Vitals</TabsTrigger>
                <TabsTrigger value="diagnoses">Diagnoses</TabsTrigger>
                <TabsTrigger value="vaccinations">Vaccinations</TabsTrigger>
                <TabsTrigger value="prescriptions">Prescriptions</TabsTrigger>
                <TabsTrigger value="lab">Lab</TabsTrigger>
                <TabsTrigger value="imaging">Imaging</TabsTrigger>
                <TabsTrigger value="billing">Billing</TabsTrigger>
                <TabsTrigger value="telemedicine">Telemedicine</TabsTrigger>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
              </TabsList>

              <TabsContent value="demographics" className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <Card>
                    <CardHeader><CardTitle className="text-lg">Personal Info</CardTitle></CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <Row label="Full name" value={patient.full_name} />
                      <Row label="Date of birth" value={`${patient.date_of_birth} (${patient.age} yrs)`} />
                      <Row label="Gender" value={patient.gender} />
                      <Row label="Blood type" value={patient.blood_type || "\u2014"} />
                      <Row label="Marital status" value={patient.marital_status || "\u2014"} />
                      <Row label="National ID type" value={patient.national_id_type || "\u2014"} />
                      <Row label="Patient ID" value={patient.display_id} />
                      <Row label="Registered" value={new Date(patient.registration_date).toLocaleDateString()} />
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader><CardTitle className="text-lg">Contact</CardTitle></CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <Row label="Phone" value={patient.phone_primary || "\u2014"} />
                      <Row label="Alt. phone" value={patient.phone_secondary || "\u2014"} />
                      <Row label="Email" value={patient.email || "\u2014"} />
                      <Row label="Address" value={patient.address_line1 || "\u2014"} />
                      {patient.address_line2 && <Row label="" value={patient.address_line2} />}
                      <Row label="City" value={`${patient.city || ""}${patient.state ? `, ${patient.state}` : ""}`} />
                      <Row label="Postal code" value={patient.postal_code || "\u2014"} />
                      <Row label="Country" value={patient.country || "\u2014"} />
                    </CardContent>
                  </Card>
                </div>
                <Card>
                  <CardHeader><CardTitle className="text-lg">Quick Summary</CardTitle></CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <SummaryBox label="Allergies" value={patient.allergies.length} active={patient.allergies.length > 0} />
                    <SummaryBox label="Medications" value={patient.active_medications.length} active={patient.active_medications.length > 0} />
                    <SummaryBox label="Insurance" value={patient.insurance_policies.length} active={patient.insurance_policies.length > 0} />
                    <SummaryBox label="Consents" value={patient.has_active_consents ? "Yes" : "No"} active={patient.has_active_consents} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="history">
                <MedicalHistoryEditor patientId={patient.id} />
              </TabsContent>

              <TabsContent value="allergies">
                <AllergiesList patientId={patient.id} />
              </TabsContent>

              <TabsContent value="medications">
                <Card>
                  <CardHeader><CardTitle>Current Medications</CardTitle></CardHeader>
                  <CardContent>
                    {patient.active_medications.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No active medications.</p>
                    ) : (
                      <div className="space-y-2">
                        {patient.active_medications.map((m) => (
                          <div key={m.id} className="rounded-lg border p-3">
                            <div className="text-sm font-medium">{m.drug_name}</div>
                            <div className="text-xs text-muted-foreground">
                              {m.dosage}{m.dosage && m.frequency ? " · " : ""}{m.frequency}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="insurance">
                <InsuranceList patientId={patient.id} />
              </TabsContent>

              <TabsContent value="contacts">
                <EmergencyContactsList patientId={patient.id} />
              </TabsContent>

              <TabsContent value="consents">
                <ConsentManager patientId={patient.id} />
              </TabsContent>

              <TabsContent value="encounters">
                <PatientEncounters patientId={patient.id} />
              </TabsContent>

              <TabsContent value="vitals">
                <div className="space-y-4">
                  <VitalsTab patientId={patient.id} />
                </div>
              </TabsContent>

              <TabsContent value="diagnoses">
                <DiagnosisList patientId={patient.id} />
              </TabsContent>

              <TabsContent value="vaccinations">
                <VaccinationList patientId={patient.id} />
              </TabsContent>

              <TabsContent value="prescriptions">
                <PatientPrescriptions patientId={patient.id} />
              </TabsContent>

              <TabsContent value="lab">
                <PatientLabOrders patientId={patient.id} />
              </TabsContent>

              <TabsContent value="imaging">
                <PatientStudies patientId={patient.id} />
              </TabsContent>

              <TabsContent value="billing">
                <PatientBillingHistory patientId={patient.id} />
              </TabsContent>

              <TabsContent value="telemedicine">
                <PatientConsultations patientId={patient.id} />
              </TabsContent>
              <TabsContent value="timeline">
                <PatientTimeline patientId={patient.id} />
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-muted-foreground shrink-0">{label}:</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

function SummaryBox({ label, value, active }: { label: string; value: string | number; active: boolean }) {
  return (
    <div className={`rounded-lg border p-3 text-center ${active ? "bg-primary/5 border-primary/20" : ""}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function VitalsTab({ patientId }: { patientId: string }) {
  const [vitals, setVitals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: any[] }>(`/clinical/vitals/?patient=${patientId}`);
      setVitals(data.results);
    } catch { } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Vitals</h3>
        <Button size="sm" variant="outline" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Record Vitals"}
        </Button>
      </div>
      {showForm && (
        <VitalsForm
          onSubmit={async (data) => {
            await api.post("/clinical/vitals/", { patient: patientId, ...data });
            setShowForm(false);
            await load();
          }}
        />
      )}
      <VitalsDisplay vitals={vitals} />
    </div>
  );
}
