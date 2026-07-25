"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface PrescriptionSummary {
  id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  patient_name: string;
  quantity_prescribed: number;
  quantity_dispensed: number;
  refills_remaining: number;
  status: string;
}

interface DispenseFormData {
  prescription: string;
  quantity: number;
  copay_charged: number;
  is_refill: boolean;
  notes: string;
}

interface DispenseFormProps {
  onSubmit: (data: DispenseFormData) => Promise<void>;
  loading: boolean;
  onCancel: () => void;
  prescriptions: PrescriptionSummary[];
}

export function DispenseForm({ onSubmit, loading, onCancel, prescriptions }: DispenseFormProps) {
  const [form, setForm] = useState<DispenseFormData>({
    prescription: "",
    quantity: 0,
    copay_charged: 0,
    is_refill: false,
    notes: "",
  });

  const selectedRx = prescriptions.find((p) => p.id === form.prescription);

  const set = (k: keyof DispenseFormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const setNum = (k: keyof DispenseFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: Number(e.target.value) }));

  const setCheck = (k: keyof DispenseFormData) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => setForm((f) => ({ ...f, [k]: e.target.checked }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(form);
  };

  const selectCls = "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Dispense Medication</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="prescription">Prescription *</Label>
            <select
              id="prescription"
              value={form.prescription}
              onChange={set("prescription")}
              required
              className={selectCls}
            >
              <option value="">Search/select prescription...</option>
              {prescriptions.map((rx) => (
                <option key={rx.id} value={rx.id}>
                  {rx.drug_name} &mdash; {rx.patient_name} ({rx.status.replace(/_/g, " ")})
                </option>
              ))}
            </select>
          </div>

          {selectedRx && (
            <div className="sm:col-span-2 space-y-1 rounded-md bg-muted p-3 text-sm">
              <p><strong>{selectedRx.drug_name}</strong> &middot; {selectedRx.dosage} &middot; {selectedRx.frequency}</p>
              <p>Patient: {selectedRx.patient_name}</p>
              <p>Prescribed: {selectedRx.quantity_prescribed} &middot; Dispensed: {selectedRx.quantity_dispensed} &middot; Refills left: {selectedRx.refills_remaining}</p>
              <p>Status: {selectedRx.status.replace(/_/g, " ")}</p>
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="quantity">Quantity *</Label>
            <Input id="quantity" type="number" min={1} value={form.quantity || ""} onChange={setNum("quantity")} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="copay_charged">Copay charged ($)</Label>
            <Input id="copay_charged" type="number" min={0} step="0.01" value={form.copay_charged || ""} onChange={setNum("copay_charged")} />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_refill"
              checked={form.is_refill}
              onChange={setCheck("is_refill")}
              className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <Label htmlFor="is_refill">This is a refill</Label>
          </div>
          <div className="space-y-1.5 sm:col-span-2">
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

      <div className="flex gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Dispensing..." : "Dispense"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
