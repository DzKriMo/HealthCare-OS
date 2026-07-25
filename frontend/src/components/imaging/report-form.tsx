"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface ReportFormData {
  findings: string;
  impression: string;
  recommendations: string;
}

interface Props {
  initial?: Partial<ReportFormData>;
  onSubmit: (data: ReportFormData) => Promise<void>;
  loading?: boolean;
}

export function ReportForm({ initial, onSubmit, loading }: Props) {
  const [findings, setFindings] = useState(initial?.findings ?? "");
  const [impression, setImpression] = useState(initial?.impression ?? "");
  const [recommendations, setRecommendations] = useState(
    initial?.recommendations ?? "",
  );
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({ findings, impression, recommendations });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-1.5">
        <Label htmlFor="findings">Findings</Label>
        <textarea
          id="findings"
          rows={8}
          value={findings}
          onChange={(e) => setFindings(e.target.value)}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Enter radiology findings..."
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="impression">Impression</Label>
        <textarea
          id="impression"
          rows={4}
          value={impression}
          onChange={(e) => setImpression(e.target.value)}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Enter your impression..."
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="recommendations">Recommendations</Label>
        <textarea
          id="recommendations"
          rows={3}
          value={recommendations}
          onChange={(e) => setRecommendations(e.target.value)}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Enter recommendations..."
        />
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={submitting || loading}>
          {submitting ? "Saving…" : "Save Report"}
        </Button>
      </div>
    </form>
  );
}
