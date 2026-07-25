"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface DiagnosisEntry {
  id: string;
  icd_code: string;
  description: string;
  diagnosis_type: string;
  is_chronic: boolean;
  onset_date: string | null;
  resolved_date: string | null;
  is_active: boolean;
  notes: string;
}

const DIAGNOSIS_TYPES = ["primary", "secondary", "admitting", "discharge"];

interface Props {
  patientId: string;
  encounterId?: string;
}

export function DiagnosisList({ patientId, encounterId }: Props) {
  const [diagnoses, setDiagnoses] = useState<DiagnosisEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [icdCode, setIcdCode] = useState("");
  const [description, setDescription] = useState("");
  const [diagnosisType, setDiagnosisType] = useState("primary");
  const [isChronic, setIsChronic] = useState(false);
  const [onsetDate, setOnsetDate] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const params = encounterId
        ? `/clinical/diagnoses/?encounter=${encounterId}`
        : `/clinical/diagnoses/?patient=${patientId}`;
      const data = await api.get<{ results: DiagnosisEntry[] }>(params);
      setDiagnoses(data.results);
    } catch {
      setError("Failed to load diagnoses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId, encounterId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!icdCode.trim() || !description.trim()) {
      setFormError("ICD code and description are required");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post("/clinical/diagnoses/", {
        patient: patientId,
        encounter: encounterId || null,
        icd_code: icdCode.trim(),
        description: description.trim(),
        diagnosis_type: diagnosisType,
        is_chronic: isChronic,
        onset_date: onsetDate || null,
        notes,
      });
      setIcdCode(""); setDescription(""); setOnsetDate(""); setNotes("");
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (d: DiagnosisEntry) => {
    try {
      await api.put(`/clinical/diagnoses/${d.id}/`, { is_active: !d.is_active });
      await load();
    } catch {
      setError("Failed to update diagnosis");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Diagnoses</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Diagnoses</CardTitle>
          <p className="text-sm text-muted-foreground">
            {diagnoses.length} recorded
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
                <Label>ICD Code *</Label>
                <Input value={icdCode} onChange={(e) => setIcdCode(e.target.value)} placeholder="e.g. E11.9" />
              </div>
              <div className="space-y-1">
                <Label>Type</Label>
                <select value={diagnosisType} onChange={(e) => setDiagnosisType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {DIAGNOSIS_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Description *</Label>
                <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Type 2 diabetes mellitus" />
              </div>
              <div className="space-y-1">
                <Label>Onset date</Label>
                <Input type="date" value={onsetDate} onChange={(e) => setOnsetDate(e.target.value)} />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="is-chronic" checked={isChronic} onChange={(e) => setIsChronic(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300" />
              <Label htmlFor="is-chronic">Chronic condition</Label>
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Diagnosis"}
            </Button>
          </form>
        )}

        {diagnoses.length === 0 && (
          <p className="text-sm text-muted-foreground">No diagnoses recorded.</p>
        )}

        <div className="space-y-2">
          {diagnoses.map((d) => {
            const typeColor =
              d.diagnosis_type === "primary" ? "bg-blue-100 text-blue-800" :
              d.diagnosis_type === "secondary" ? "bg-gray-100 text-gray-800" :
              d.diagnosis_type === "admitting" ? "bg-purple-100 text-purple-800" :
              "bg-orange-100 text-orange-800";
            return (
              <div key={d.id} className={`flex items-start justify-between rounded-lg border p-3 ${!d.is_active ? "opacity-50" : ""}`}>
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{d.icd_code}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${typeColor}`}>
                      {d.diagnosis_type}
                    </span>
                    {d.is_chronic && (
                      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800">
                        Chronic
                      </span>
                    )}
                    {!d.is_active && (
                      <span className="text-xs text-muted-foreground">Resolved</span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">{d.description}</div>
                  {d.onset_date && (
                    <div className="text-xs text-muted-foreground">Onset: {d.onset_date}</div>
                  )}
                  {d.notes && (
                    <div className="text-xs text-muted-foreground">{d.notes}</div>
                  )}
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleToggleActive(d)}>
                  {d.is_active ? <Icons.x className="h-3 w-3" /> : <Icons.plus className="h-3 w-3" />}
                </Button>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
