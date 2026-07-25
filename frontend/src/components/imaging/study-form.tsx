"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface PatientSummary {
  id: string;
  first_name: string;
  last_name: string;
}

interface StudyFormData {
  patient: string;
  modality: string;
  body_part: string;
  protocol: string;
  priority: string;
  reason: string;
}

interface Props {
  patients: PatientSummary[];
  onSubmit: (data: StudyFormData) => Promise<void>;
  loading?: boolean;
}

const MODALITIES = [
  "xray",
  "ct",
  "mri",
  "ultrasound",
  "mammography",
  "nuclear",
  "dexa",
  "other",
] as const;

const PRIORITIES = ["routine", "urgent", "stat"] as const;

export function StudyForm({ patients, onSubmit, loading }: Props) {
  const [patient, setPatient] = useState("");
  const [modality, setModality] = useState<string>(MODALITIES[0]);
  const [bodyPart, setBodyPart] = useState("");
  const [protocol, setProtocol] = useState("");
  const [priority, setPriority] = useState<string>(PRIORITIES[0]);
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        patient,
        modality,
        body_part: bodyPart,
        protocol,
        priority,
        reason,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="patient">Patient *</Label>
          <select
            id="patient"
            value={patient}
            onChange={(e) => setPatient(e.target.value)}
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

        <div className="space-y-1.5">
          <Label htmlFor="modality">Modality *</Label>
          <select
            id="modality"
            value={modality}
            onChange={(e) => setModality(e.target.value)}
            required
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {MODALITIES.map((m) => (
              <option key={m} value={m}>
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="bodyPart">Body part *</Label>
          <Input
            id="bodyPart"
            value={bodyPart}
            onChange={(e) => setBodyPart(e.target.value)}
            required
            placeholder="e.g. Chest, Lumbar Spine, Right Knee"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="protocol">Protocol</Label>
          <Input
            id="protocol"
            value={protocol}
            onChange={(e) => setProtocol(e.target.value)}
            placeholder="e.g. CT Chest w/ contrast"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="priority">Priority *</Label>
          <select
            id="priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            required
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="reason">Reason for study</Label>
        <textarea
          id="reason"
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          placeholder="Clinical indication / reason for request..."
        />
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={submitting || loading || !patient}>
          {submitting ? "Ordering…" : "Order Study"}
        </Button>
      </div>
    </form>
  );
}
