"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface MedicalHistoryEntry {
  id: string;
  category: string;
  condition: string;
  description: string;
  onset_date: string;
  resolved_date: string | null;
  is_active: boolean;
  recorded_at: string;
  recorded_by_name: string;
}

const CATEGORIES = [
  { value: "chronic", label: "Chronic Condition" },
  { value: "surgery", label: "Past Surgery" },
  { value: "family", label: "Family History" },
  { value: "social", label: "Social History" },
  { value: "trauma", label: "Trauma" },
  { value: "other", label: "Other" },
];

interface Props {
  patientId: string;
}

export function MedicalHistoryEditor({ patientId }: Props) {
  const [entries, setEntries] = useState<MedicalHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [category, setCategory] = useState("chronic");
  const [condition, setCondition] = useState("");
  const [description, setDescription] = useState("");
  const [onsetDate, setOnsetDate] = useState("");
  const [resolvedDate, setResolvedDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: MedicalHistoryEntry[] }>(
        `/patients/${patientId}/history/`,
      );
      setEntries(data.results);
    } catch {
      setError("Failed to load medical history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!condition.trim()) { setFormError("Condition is required"); return; }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post(`/patients/${patientId}/history/`, {
        patient: patientId,
        category,
        condition: condition.trim(),
        description,
        onset_date: onsetDate || null,
        resolved_date: resolvedDate || null,
        is_active: true,
      });
      setCondition(""); setDescription(""); setOnsetDate(""); setResolvedDate("");
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/patients/history/${id}/`);
      await load();
    } catch {
      setError("Failed to delete entry");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Medical History</CardTitle></CardHeader>
        <CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  const activeEntries = entries.filter((e) => e.is_active);
  const resolvedEntries = entries.filter((e) => !e.is_active);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Medical History</CardTitle>
          <p className="text-sm text-muted-foreground">
            {entries.length} record{entries.length !== 1 ? "s" : ""}
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
                <Label>Category</Label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {CATEGORIES.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Condition *</Label>
                <Input value={condition} onChange={(e) => setCondition(e.target.value)} placeholder="e.g. Type 2 Diabetes" />
              </div>
              <div className="space-y-1">
                <Label>Onset date</Label>
                <Input type="date" value={onsetDate} onChange={(e) => setOnsetDate(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Resolved date</Label>
                <Input type="date" value={resolvedDate} onChange={(e) => setResolvedDate(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Description</Label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Additional details..." />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Record"}
            </Button>
          </form>
        )}

        {activeEntries.length === 0 && resolvedEntries.length === 0 && (
          <p className="text-sm text-muted-foreground">No medical history recorded.</p>
        )}

        {activeEntries.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">ACTIVE</p>
            {activeEntries.map((entry) => (
              <div key={entry.id} className="flex items-start justify-between rounded-lg border p-3">
                <div className="space-y-0.5">
                  <div className="text-sm font-medium">{entry.condition}</div>
                  <div className="text-xs text-muted-foreground">
                    {CATEGORIES.find((c) => c.value === entry.category)?.label || entry.category}
                    {entry.onset_date && ` · Onset: ${entry.onset_date}`}
                  </div>
                  {entry.description && (
                    <div className="text-xs text-muted-foreground">{entry.description}</div>
                  )}
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(entry.id)}>
                  <Icons.x className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {resolvedEntries.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">RESOLVED</p>
            {resolvedEntries.map((entry) => (
              <div key={entry.id} className="flex items-start justify-between rounded-lg border border-dashed p-3 opacity-60">
                <div className="space-y-0.5">
                  <div className="text-sm font-medium">{entry.condition}</div>
                  <div className="text-xs text-muted-foreground">
                    {CATEGORIES.find((c) => c.value === entry.category)?.label || entry.category}
                    {entry.resolved_date && ` · Resolved: ${entry.resolved_date}`}
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(entry.id)}>
                  <Icons.x className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
