"use client";

import { Label } from "@/components/ui/label";

interface Props {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  onSubjectiveChange: (val: string) => void;
  onObjectiveChange: (val: string) => void;
  onAssessmentChange: (val: string) => void;
  onPlanChange: (val: string) => void;
}

export function SOAPEditor({
  subjective,
  objective,
  assessment,
  plan,
  onSubjectiveChange,
  onObjectiveChange,
  onAssessmentChange,
  onPlanChange,
}: Props) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="space-y-2">
        <Label>Subjective (S)</Label>
        <textarea
          value={subjective}
          onChange={(e) => onSubjectiveChange(e.target.value)}
          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Chief complaint, history of present illness..."
        />
      </div>
      <div className="space-y-2">
        <Label>Objective (O)</Label>
        <textarea
          value={objective}
          onChange={(e) => onObjectiveChange(e.target.value)}
          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Physical exam findings, vitals, labs..."
        />
      </div>
      <div className="space-y-2">
        <Label>Assessment (A)</Label>
        <textarea
          value={assessment}
          onChange={(e) => onAssessmentChange(e.target.value)}
          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Diagnosis, differential, clinical impression..."
        />
      </div>
      <div className="space-y-2">
        <Label>Plan (P)</Label>
        <textarea
          value={plan}
          onChange={(e) => onPlanChange(e.target.value)}
          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Medications, referrals, follow-up plan..."
        />
      </div>
    </div>
  );
}
