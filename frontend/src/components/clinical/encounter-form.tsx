"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SOAPEditor } from "@/components/clinical/soap-editor";

interface PatientSummary {
  id: string;
  first_name: string;
  last_name: string;
}

interface EncounterData {
  patient: string;
  appointment?: string;
  encounter_date: string;
  duration_minutes: number | null;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  status: string;
}

interface Props {
  initial?: Partial<EncounterData>;
  patients: PatientSummary[];
  onSubmit: (data: EncounterData) => Promise<void>;
  loading?: boolean;
}

export function EncounterForm({ initial, patients, onSubmit, loading }: Props) {
  const [patientId, setPatientId] = useState(initial?.patient ?? "");
  const [encounterDate, setEncounterDate] = useState(
    initial?.encounter_date ?? new Date().toISOString().slice(0, 10),
  );
  const [durationMinutes, setDurationMinutes] = useState(
    initial?.duration_minutes?.toString() ?? "30",
  );
  const [status, setStatus] = useState(initial?.status ?? "draft");
  const [subjective, setSubjective] = useState(initial?.subjective ?? "");
  const [objective, setObjective] = useState(initial?.objective ?? "");
  const [assessment, setAssessment] = useState(initial?.assessment ?? "");
  const [plan, setPlan] = useState(initial?.plan ?? "");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        patient: patientId,
        encounter_date: encounterDate,
        duration_minutes: durationMinutes ? Number(durationMinutes) : null,
        status,
        subjective,
        objective,
        assessment,
        plan,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1">
          <Label>Patient *</Label>
          <select
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            required
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="">Select a patient…</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.first_name} {p.last_name}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label>Encounter date *</Label>
          <Input
            type="date"
            value={encounterDate}
            onChange={(e) => setEncounterDate(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1">
          <Label>Duration (minutes)</Label>
          <Input
            type="number"
            min={0}
            value={durationMinutes}
            onChange={(e) => setDurationMinutes(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <Label>Status</Label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option value="draft">Draft</option>
            <option value="signed">Signed</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      <SOAPEditor
        subjective={subjective}
        objective={objective}
        assessment={assessment}
        plan={plan}
        onSubjectiveChange={setSubjective}
        onObjectiveChange={setObjective}
        onAssessmentChange={setAssessment}
        onPlanChange={setPlan}
      />

      <div className="flex justify-end">
        <Button type="submit" disabled={submitting || loading || !patientId}>
          {submitting ? "Saving…" : initial?.patient ? "Update Encounter" : "Create Encounter"}
        </Button>
      </div>
    </form>
  );
}
