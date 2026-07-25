"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { EncounterCard } from "@/components/clinical/encounter-card";

interface EncounterSummary {
  id: string; encounter_date: string; status: string;
  practitioner_name?: string; subjective?: string;
  objective?: string; assessment?: string; plan?: string;
}

interface Props { patientId: string; }

export function PatientEncounters({ patientId }: Props) {
  const router = useRouter();
  const [encounters, setEncounters] = useState<EncounterSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<{ results: EncounterSummary[] }>(`/clinical/encounters/?patient=${patientId}`);
        setEncounters(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Encounters</CardTitle>
          <p className="text-sm text-muted-foreground">{encounters.length} encounter{encounters.length !== 1 ? "s" : ""}</p>
        </div>
        <Button size="sm" onClick={() => router.push(`/clinical/new?patient=${patientId}`)}>
          <Icons.plus className="mr-1 h-4 w-4" /> New Encounter
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {encounters.length === 0 ? (
          <p className="text-sm text-muted-foreground">No encounters recorded.</p>
        ) : (
          encounters.map((enc) => (
            <EncounterCard
              key={enc.id}
              encounter={enc}
              onClick={() => router.push(`/clinical/${enc.id}`)}
            />
          ))
        )}
      </CardContent>
    </Card>
  );
}
