"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { format } from "date-fns";

interface Consultation {
  id: string; practitioner_name: string; status: string;
  scheduled_at: string; meeting_url: string; notes: string;
}

const statusColors: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  ready: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-600",
  cancelled: "bg-red-100 text-red-800",
  missed: "bg-red-100 text-red-800",
};

export function PatientConsultations({ patientId }: { patientId: string }) {
  const router = useRouter();
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get<{ results: Consultation[] }>(`/telemedicine/consultations/?patient=${patientId}`);
        setConsultations(res.results);
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Video Consultations</CardTitle>
        <Button size="sm" onClick={() => router.push(`/telemedicine/new?patient=${patientId}`)}>
          <Icons.video className="mr-2 h-4 w-4" /> Schedule
        </Button>
      </CardHeader>
      <CardContent>
        {consultations.length === 0 ? (
          <p className="text-sm text-muted-foreground">No video consultations.</p>
        ) : (
          <div className="space-y-2">
            {consultations.map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">Dr. {c.practitioner_name}</span>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[c.status] || ""}`}>
                      {c.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{format(new Date(c.scheduled_at), "MMM d, yyyy h:mm a")}</p>
                </div>
                <Button size="sm" variant="ghost" onClick={() => router.push(`/telemedicine/${c.id}`)}>
                  <Icons.chevronDown className="h-4 w-4 rotate-270" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
