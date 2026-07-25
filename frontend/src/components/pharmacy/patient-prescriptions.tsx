"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { PrescriptionCard } from "@/components/pharmacy/prescription-card";

interface PrescriptionSummary {
  id: string | number; patient_name: string; drug_name: string;
  dosage: string; frequency: string; status: string;
  prescribed_by_name: string; is_controlled: boolean;
  controlled_schedule?: string; issued_date: string;
}

interface Props { patientId: string; }

export function PatientPrescriptions({ patientId }: Props) {
  const router = useRouter();
  const [prescriptions, setPrescriptions] = useState<PrescriptionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<{ results: PrescriptionSummary[] }>(`/pharmacy/prescriptions/?patient=${patientId}`);
        setPrescriptions(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Prescriptions</CardTitle>
          <p className="text-sm text-muted-foreground">{prescriptions.length} prescription{prescriptions.length !== 1 ? "s" : ""}</p>
        </div>
        <Button size="sm" onClick={() => router.push(`/pharmacy/new?patient=${patientId}`)}>
          <Icons.plus className="mr-1 h-4 w-4" /> New Prescription
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {prescriptions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No prescriptions recorded.</p>
        ) : (
          prescriptions.map((rx) => (
            <PrescriptionCard
              key={rx.id}
              prescription={rx}
              onClick={() => router.push(`/pharmacy/${rx.id}`)}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}
