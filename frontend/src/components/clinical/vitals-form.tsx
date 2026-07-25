"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface VitalsData {
  systolic_bp: number | null;
  diastolic_bp: number | null;
  heart_rate: number | null;
  respiratory_rate: number | null;
  temperature_c: number | null;
  oxygen_saturation: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  pain_score: number | null;
  notes: string;
}

interface Props {
  initial?: Partial<VitalsData>;
  onSubmit: (data: VitalsData) => Promise<void>;
}

export function VitalsForm({ initial, onSubmit }: Props) {
  const [systolicBp, setSystolicBp] = useState(initial?.systolic_bp?.toString() ?? "");
  const [diastolicBp, setDiastolicBp] = useState(initial?.diastolic_bp?.toString() ?? "");
  const [heartRate, setHeartRate] = useState(initial?.heart_rate?.toString() ?? "");
  const [respiratoryRate, setRespiratoryRate] = useState(initial?.respiratory_rate?.toString() ?? "");
  const [temperatureC, setTemperatureC] = useState(initial?.temperature_c?.toString() ?? "");
  const [oxygenSaturation, setOxygenSaturation] = useState(initial?.oxygen_saturation?.toString() ?? "");
  const [heightCm, setHeightCm] = useState(initial?.height_cm?.toString() ?? "");
  const [weightKg, setWeightKg] = useState(initial?.weight_kg?.toString() ?? "");
  const [painScore, setPainScore] = useState(initial?.pain_score?.toString() ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        systolic_bp: systolicBp ? Number(systolicBp) : null,
        diastolic_bp: diastolicBp ? Number(diastolicBp) : null,
        heart_rate: heartRate ? Number(heartRate) : null,
        respiratory_rate: respiratoryRate ? Number(respiratoryRate) : null,
        temperature_c: temperatureC ? Number(temperatureC) : null,
        oxygen_saturation: oxygenSaturation ? Number(oxygenSaturation) : null,
        height_cm: heightCm ? Number(heightCm) : null,
        weight_kg: weightKg ? Number(weightKg) : null,
        pain_score: painScore ? Number(painScore) : null,
        notes,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1">
          <Label>Systolic BP (mmHg)</Label>
          <Input type="number" min={0} value={systolicBp} onChange={(e) => setSystolicBp(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Diastolic BP (mmHg)</Label>
          <Input type="number" min={0} value={diastolicBp} onChange={(e) => setDiastolicBp(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Heart Rate (bpm)</Label>
          <Input type="number" min={0} value={heartRate} onChange={(e) => setHeartRate(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Respiratory Rate (/min)</Label>
          <Input type="number" min={0} value={respiratoryRate} onChange={(e) => setRespiratoryRate(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Temperature (°C)</Label>
          <Input type="number" step="0.1" value={temperatureC} onChange={(e) => setTemperatureC(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>O₂ Saturation (%)</Label>
          <Input type="number" min={0} max={100} value={oxygenSaturation} onChange={(e) => setOxygenSaturation(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Height (cm)</Label>
          <Input type="number" min={0} step="0.1" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Weight (kg)</Label>
          <Input type="number" min={0} step="0.1" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label>Pain Score (0–10)</Label>
          <Input type="number" min={0} max={10} value={painScore} onChange={(e) => setPainScore(e.target.value)} />
        </div>
      </div>
      <div className="space-y-1">
        <Label>Notes</Label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        />
      </div>
      <Button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : "Save Vitals"}
      </Button>
    </form>
  );
}
