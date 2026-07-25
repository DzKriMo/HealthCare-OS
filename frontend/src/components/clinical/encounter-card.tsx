"use client";

import { Card, CardContent } from "@/components/ui/card";

interface EncounterSummary {
  id: string;
  encounter_date: string;
  status: string;
  practitioner_name?: string;
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
}

interface Props {
  encounter: EncounterSummary;
  onClick?: () => void;
}

const STATUS_BADGE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  signed: "bg-green-100 text-green-800",
  completed: "bg-blue-100 text-blue-800",
  cancelled: "bg-red-100 text-red-800",
};

function truncate(text: string | undefined, max: number): string | null {
  if (!text) return null;
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export function EncounterCard({ encounter, onClick }: Props) {
  return (
    <Card
      className={`cursor-pointer transition-colors hover:bg-accent ${onClick ? "" : ""}`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">
                {new Date(encounter.encounter_date).toLocaleDateString()}
              </span>
              {encounter.practitioner_name && (
                <span className="text-xs text-muted-foreground">
                  {encounter.practitioner_name}
                </span>
              )}
            </div>
            <div>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_BADGE[encounter.status] || "bg-gray-100 text-gray-800"}`}>
                {encounter.status}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
          <div>
            <span className="font-medium text-foreground">S:</span>{" "}
            {truncate(encounter.subjective, 100) || "—"}
          </div>
          <div>
            <span className="font-medium text-foreground">O:</span>{" "}
            {truncate(encounter.objective, 100) || "—"}
          </div>
          <div>
            <span className="font-medium text-foreground">A:</span>{" "}
            {truncate(encounter.assessment, 100) || "—"}
          </div>
          <div>
            <span className="font-medium text-foreground">P:</span>{" "}
            {truncate(encounter.plan, 100) || "—"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
