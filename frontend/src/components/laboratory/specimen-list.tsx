"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Specimen {
  id: string;
  barcode: string;
  specimen_type: string;
  status: string;
  collection_date: string | null;
  collected_by_name: string | null;
  lab_order: string;
  notes: string;
}

interface Props {
  orderId: string;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  collected: "bg-yellow-100 text-yellow-700",
  received: "bg-purple-100 text-purple-700",
  processing: "bg-indigo-100 text-indigo-700",
  completed: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

const TRANSITIONS: Record<string, string[]> = {
  pending: ["collect"],
  collected: ["receive", "reject"],
  received: ["process", "reject"],
  processing: ["complete", "reject"],
  completed: [],
  rejected: [],
};

const TRANSITION_LABELS: Record<string, string> = {
  collect: "Collect",
  receive: "Receive",
  process: "Process",
  complete: "Complete",
  reject: "Reject",
};

export function SpecimenList({ orderId }: Props) {
  const [specimens, setSpecimens] = useState<Specimen[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [transitioning, setTransitioning] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: Specimen[] }>(
        `/lab/specimens/?lab_order=${orderId}`,
      );
      setSpecimens(data.results);
    } catch {
      setError("Failed to load specimens");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orderId) load();
  }, [orderId]);

  const handleTransition = async (id: string, status: string) => {
    setTransitioning(id);
    try {
      await api.post(`/lab/specimens/${id}/transition/`, { status });
      await load();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.message : "Transition failed",
      );
    } finally {
      setTransitioning(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Specimens</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-20 animate-pulse rounded-lg bg-muted" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Specimens</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {specimens.length === 0 && (
          <p className="text-sm text-muted-foreground">No specimens collected.</p>
        )}
        {specimens.map((s) => {
          const available = TRANSITIONS[s.status] || [];
          return (
            <div
              key={s.id}
              className="rounded-lg border p-3 transition-colors hover:bg-accent/50"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <code className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">
                      {s.barcode}
                    </code>
                    <span className="text-sm font-medium">{s.specimen_type}</span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px] font-medium",
                        STATUS_STYLES[s.status] || "bg-gray-100 text-gray-700",
                      )}
                    >
                      {s.status}
                    </span>
                  </div>
                  {s.collection_date && (
                    <p className="text-xs text-muted-foreground">
                      Collected: {new Date(s.collection_date).toLocaleString()}
                      {s.collected_by_name && ` by ${s.collected_by_name}`}
                    </p>
                  )}
                  {s.notes && (
                    <p className="text-xs text-muted-foreground">{s.notes}</p>
                  )}
                </div>
              </div>
              {available.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {available.map((action) => (
                    <Button
                      key={action}
                      size="sm"
                      variant={action === "reject" ? "destructive" : "outline"}
                      disabled={transitioning === s.id}
                      onClick={() => handleTransition(s.id, action)}
                    >
                      {transitioning === s.id
                        ? "..."
                        : TRANSITION_LABELS[action]}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
