"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface TimelineEntry {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  status: string;
  metadata: Record<string, unknown> | null;
}

const typeIcons: Record<string, keyof typeof Icons> = {
  medical_history: "calendar",
  allergy: "shield",
  medication: "creditCard",
  consent: "fileText",
  insurance: "creditCard",
  appointment: "calendar",
  encounter: "stethoscope",
  invoice: "creditCard",
  document: "fileText",
};

const typeColors: Record<string, string> = {
  medical_history: "border-l-blue-500",
  allergy: "border-l-red-500",
  medication: "border-l-green-500",
  consent: "border-l-purple-500",
  insurance: "border-l-yellow-500",
  appointment: "border-l-cyan-500",
  encounter: "border-l-indigo-500",
  invoice: "border-l-orange-500",
  document: "border-l-pink-500",
};

export function PatientTimeline({ patientId }: { patientId: string }) {
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<TimelineEntry[]>(
          `/patients/${patientId}/timeline/`,
        );
        setEntries(data);
      } catch {
        setError("Failed to load timeline");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [patientId]);

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
        <p className="text-sm text-muted-foreground">
          {entries.length} event{entries.length !== 1 ? "s" : ""}
        </p>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No events recorded.</p>
        ) : (
          <div className="space-y-0">
            {entries.map((entry) => {
              const Icon = Icons[typeIcons[entry.type] || "fileText"];
              const color = typeColors[entry.type] || "border-l-gray-500";
              return (
                <div
                  key={entry.id}
                  className={`relative border-l-2 ${color} pl-4 pb-4 last:pb-0`}
                >
                  <div className="absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full bg-background">
                    <Icon className="h-3 w-3 text-muted-foreground" />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(entry.timestamp).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                  <div className="text-sm font-medium">{entry.title}</div>
                  {entry.description && (
                    <div className="text-xs text-muted-foreground">
                      {entry.description}
                    </div>
                  )}
                  {entry.status && (
                    <span className="mt-0.5 inline-block rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                      {entry.status}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
