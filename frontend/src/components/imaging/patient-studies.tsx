"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { StudyCard } from "@/components/imaging/study-card";

interface StudySummary {
  id: string; patient_name: string; modality: string;
  body_part: string; status: string; priority: string;
  performed_at: string | null; report_status: string;
}

interface Props { patientId: string; }

export function PatientStudies({ patientId }: Props) {
  const router = useRouter();
  const [studies, setStudies] = useState<StudySummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<{ results: StudySummary[] }>(`/imaging/studies/?patient=${patientId}`);
        setStudies(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Imaging Studies</CardTitle>
          <p className="text-sm text-muted-foreground">{studies.length} study{studies.length !== 1 ? "ies" : ""}</p>
        </div>
        <Button size="sm" onClick={() => router.push(`/imaging/studies/new?patient=${patientId}`)}>
          <Icons.plus className="mr-1 h-4 w-4" /> New Study
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {studies.length === 0 ? (
          <p className="text-sm text-muted-foreground">No imaging studies.</p>
        ) : (
          studies.map((s) => (
            <StudyCard key={s.id} study={s} onClick={() => router.push(`/imaging/studies/${s.id}`)} />
          ))
        )}
      </CardContent>
    </Card>
  );
}
