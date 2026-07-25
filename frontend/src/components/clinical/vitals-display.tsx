"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface VitalsEntry {
  id: string;
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
  recorded_at: string;
  recorded_by_name?: string;
}

interface Props {
  vitals: VitalsEntry[];
}

function VitalsCard({ v }: { v: VitalsEntry }) {
  const items = [
    { label: "BP", value: v.systolic_bp != null && v.diastolic_bp != null ? `${v.systolic_bp}/${v.diastolic_bp}` : null, unit: "mmHg" },
    { label: "HR", value: v.heart_rate, unit: "bpm" },
    { label: "RR", value: v.respiratory_rate, unit: "/min" },
    { label: "Temp", value: v.temperature_c != null ? v.temperature_c.toFixed(1) : null, unit: "°C" },
    { label: "SpO₂", value: v.oxygen_saturation, unit: "%" },
    { label: "Height", value: v.height_cm, unit: "cm" },
    { label: "Weight", value: v.weight_kg, unit: "kg" },
    { label: "Pain", value: v.pain_score, unit: "/10" },
  ];

  return (
    <Card className="break-inside-avoid">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">
          {new Date(v.recorded_at).toLocaleString()}
        </CardTitle>
        {v.recorded_by_name && (
          <p className="text-xs text-muted-foreground">{v.recorded_by_name}</p>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2">
          {items.map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-lg font-semibold">
                {item.value ?? "—"}
              </div>
              <div className="text-[10px] text-muted-foreground">
                {item.label}{item.unit ? ` (${item.unit})` : ""}
              </div>
            </div>
          ))}
        </div>
        {v.notes && (
          <p className="mt-2 text-xs text-muted-foreground">{v.notes}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function VitalsDisplay({ vitals }: Props) {
  if (vitals.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Vitals</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No vitals recorded.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground">
        Vitals · {vitals.length} record{vitals.length !== 1 ? "s" : ""}
      </h3>
      <div className="columns-1 md:columns-2 gap-4 space-y-4">
        {vitals.map((v) => (
          <VitalsCard key={v.id} v={v} />
        ))}
      </div>
    </div>
  );
}
