"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PatientOption {
  id: string;
  first_name: string;
  last_name: string;
}

interface PrescriptionFormData {
  patient: string;
  encounter: string;
  drug_name: string;
  drug_code: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  route: string;
  instructions: string;
  quantity_prescribed: number;
  refills_authorized: number;
  daw: boolean;
  is_controlled: boolean;
  controlled_schedule: string;
  notes: string;
  expiry_date: string;
}

interface PrescriptionFormProps {
  onSubmit: (data: PrescriptionFormData) => Promise<void>;
  loading: boolean;
  patients: PatientOption[];
}

const ROUTES = [
  "oral", "sublingual", "topical", "inhaled", "iv", "im", "sc",
  "rectal", "ophthalmic", "otic", "other",
];

const CONTROLLED_SCHEDULES = ["II", "III", "IV", "V"];

export function PrescriptionForm({ onSubmit, loading, patients }: PrescriptionFormProps) {
  const [form, setForm] = useState<PrescriptionFormData>({
    patient: "",
    encounter: "",
    drug_name: "",
    drug_code: "",
    dosage: "",
    frequency: "",
    duration_days: 0,
    route: "oral",
    instructions: "",
    quantity_prescribed: 0,
    refills_authorized: 0,
    daw: false,
    is_controlled: false,
    controlled_schedule: "",
    notes: "",
    expiry_date: "",
  });

  const set = (k: keyof PrescriptionFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setCheck = (k: keyof PrescriptionFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.checked }));

  const setNum = (k: keyof PrescriptionFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(form);
  };

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Prescription Details</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="patient">Patient *</Label>
            <select id="patient" value={form.patient} onChange={set("patient")} required className={selectCls}>
              <option value="">Select patient...</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="drug_name">Drug name *</Label>
            <Input id="drug_name" value={form.drug_name} onChange={set("drug_name")} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="drug_code">Drug code</Label>
            <Input id="drug_code" value={form.drug_code} onChange={set("drug_code")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dosage">Dosage *</Label>
            <Input id="dosage" value={form.dosage} onChange={set("dosage")} required placeholder="e.g. 500mg" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="frequency">Frequency *</Label>
            <Input id="frequency" value={form.frequency} onChange={set("frequency")} required placeholder="e.g. BID" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="duration_days">Duration (days)</Label>
            <Input id="duration_days" type="number" min={0} value={form.duration_days || ""} onChange={setNum("duration_days")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="route">Route</Label>
            <select id="route" value={form.route} onChange={set("route")} className={selectCls}>
              {ROUTES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="quantity_prescribed">Qty prescribed *</Label>
            <Input id="quantity_prescribed" type="number" min={0} value={form.quantity_prescribed || ""} onChange={setNum("quantity_prescribed")} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="refills_authorized">Refills authorized</Label>
            <Input id="refills_authorized" type="number" min={0} value={form.refills_authorized || ""} onChange={setNum("refills_authorized")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="expiry_date">Expiry date</Label>
            <Input id="expiry_date" type="date" value={form.expiry_date} onChange={set("expiry_date")} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="encounter">Encounter ID</Label>
            <Input id="encounter" value={form.encounter} onChange={set("encounter")} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Instructions &amp; Notes</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="instructions">Instructions</Label>
            <textarea
              id="instructions"
              value={form.instructions}
              onChange={set("instructions")}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              value={form.notes}
              onChange={set("notes")}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Controlled Substance</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_controlled"
              checked={form.is_controlled}
              onChange={setCheck("is_controlled")}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <Label htmlFor="is_controlled">This is a controlled substance</Label>
          </div>
          {form.is_controlled && (
            <div className="space-y-1.5">
              <Label htmlFor="controlled_schedule">Schedule *</Label>
              <select
                id="controlled_schedule"
                value={form.controlled_schedule}
                onChange={set("controlled_schedule")}
                required={form.is_controlled}
                className={selectCls}
              >
                <option value="">Select schedule...</option>
                {CONTROLLED_SCHEDULES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="daw"
              checked={form.daw}
              onChange={setCheck("daw")}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <Label htmlFor="daw">Dispense as written (DAW)</Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Creating..." : "Create Prescription"}
        </Button>
      </div>
    </form>
  );
}
