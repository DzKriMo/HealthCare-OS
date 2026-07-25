"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface VaccinationEntry {
  id: string;
  vaccine_name: string;
  dose_number: number;
  lot_number: string;
  administration_site: string;
  administered_date: string;
  next_due_date: string | null;
  notes: string;
  administered_by_name?: string;
}

interface Props {
  patientId: string;
}

export function VaccinationList({ patientId }: Props) {
  const [vaccinations, setVaccinations] = useState<VaccinationEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [vaccineName, setVaccineName] = useState("");
  const [doseNumber, setDoseNumber] = useState("");
  const [lotNumber, setLotNumber] = useState("");
  const [administrationSite, setAdministrationSite] = useState("");
  const [administeredDate, setAdministeredDate] = useState("");
  const [nextDueDate, setNextDueDate] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: VaccinationEntry[] }>(
        `/clinical/vaccinations/?patient=${patientId}`,
      );
      setVaccinations(data.results);
    } catch {
      setError("Failed to load vaccinations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vaccineName.trim() || !administeredDate) {
      setFormError("Vaccine name and administered date are required");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post("/clinical/vaccinations/", {
        patient: patientId,
        vaccine_name: vaccineName.trim(),
        dose_number: doseNumber ? Number(doseNumber) : null,
        lot_number: lotNumber.trim(),
        administration_site: administrationSite,
        administered_date: administeredDate,
        next_due_date: nextDueDate || null,
        notes,
      });
      setVaccineName(""); setDoseNumber(""); setLotNumber("");
      setAdministrationSite(""); setAdministeredDate(""); setNextDueDate("");
      setNotes("");
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Vaccinations</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Vaccinations</CardTitle>
          <p className="text-sm text-muted-foreground">
            {vaccinations.length} record{vaccinations.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          <Icons.plus className="mr-1 h-4 w-4" />
          {showForm ? "Cancel" : "Add"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}

        {showForm && (
          <form onSubmit={handleAdd} className="space-y-3 rounded-lg border p-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label>Vaccine name *</Label>
                <Input value={vaccineName} onChange={(e) => setVaccineName(e.target.value)} placeholder="e.g. Influenza" />
              </div>
              <div className="space-y-1">
                <Label>Dose number</Label>
                <Input type="number" min={1} value={doseNumber} onChange={(e) => setDoseNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Lot number</Label>
                <Input value={lotNumber} onChange={(e) => setLotNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Administration site</Label>
                <Input value={administrationSite} onChange={(e) => setAdministrationSite(e.target.value)} placeholder="e.g. Left deltoid" />
              </div>
              <div className="space-y-1">
                <Label>Administered date *</Label>
                <Input type="date" value={administeredDate} onChange={(e) => setAdministeredDate(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Next due date</Label>
                <Input type="date" value={nextDueDate} onChange={(e) => setNextDueDate(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Vaccination"}
            </Button>
          </form>
        )}

        {vaccinations.length === 0 && (
          <p className="text-sm text-muted-foreground">No vaccinations on record.</p>
        )}

        <div className="space-y-2">
          {vaccinations.map((v) => (
            <div key={v.id} className="flex items-start justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{v.vaccine_name}</span>
                  {v.dose_number && (
                    <span className="text-xs text-muted-foreground">Dose {v.dose_number}</span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  {v.administered_date}
                  {v.lot_number && ` · Lot: ${v.lot_number}`}
                  {v.administration_site && ` · Site: ${v.administration_site}`}
                </div>
                {v.next_due_date && (
                  <div className="text-xs font-medium text-amber-600">
                    Next due: {v.next_due_date}
                  </div>
                )}
                {v.administered_by_name && (
                  <div className="text-xs text-muted-foreground">By: {v.administered_by_name}</div>
                )}
                {v.notes && <div className="text-xs text-muted-foreground">{v.notes}</div>}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
