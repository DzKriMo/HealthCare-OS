"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface AllergyEntry {
  id: string;
  substance: string;
  reaction: string;
  severity: string;
  onset_date: string | null;
  status: string;
}

const SEVERITIES = ["mild", "moderate", "severe", "life_threatening"];

interface Props {
  patientId: string;
}

export function AllergiesList({ patientId }: Props) {
  const [allergies, setAllergies] = useState<AllergyEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [substance, setSubstance] = useState("");
  const [reaction, setReaction] = useState("");
  const [severity, setSeverity] = useState("moderate");
  const [onsetDate, setOnsetDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: AllergyEntry[] }>(
        `/patients/${patientId}/allergies/`,
      );
      setAllergies(data.results);
    } catch {
      setError("Failed to load allergies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!substance.trim()) { setFormError("Substance is required"); return; }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post(`/patients/${patientId}/allergies/`, {
        patient: patientId,
        substance: substance.trim(),
        reaction,
        severity,
        onset_date: onsetDate || null,
        status: "active",
      });
      setSubstance(""); setReaction(""); setOnsetDate("");
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
      await api.delete(`/patients/allergies/${id}/`);
      await load();
    } catch {
      setError("Failed to delete");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Allergies</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Allergies</CardTitle>
          <p className="text-sm text-muted-foreground">
            {allergies.length} recorded
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
                <Label>Substance *</Label>
                <Input value={substance} onChange={(e) => setSubstance(e.target.value)} placeholder="e.g. Penicillin" />
              </div>
              <div className="space-y-1">
                <Label>Severity</Label>
                <select value={severity} onChange={(e) => setSeverity(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>{s.replace("_", " ")}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Onset date</Label>
                <Input type="date" value={onsetDate} onChange={(e) => setOnsetDate(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Reaction</Label>
              <textarea value={reaction} onChange={(e) => setReaction(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Describe the reaction..." />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Allergy"}
            </Button>
          </form>
        )}

        {allergies.length === 0 && (
          <p className="text-sm text-muted-foreground">No known allergies.</p>
        )}

        <div className="space-y-2">
          {allergies.map((a) => {
            const severityColor =
              a.severity === "life_threatening" ? "bg-red-100 text-red-800" :
              a.severity === "severe" ? "bg-orange-100 text-orange-800" :
              a.severity === "moderate" ? "bg-yellow-100 text-yellow-800" :
              "bg-green-100 text-green-800";
            return (
              <div key={a.id} className="flex items-start justify-between rounded-lg border p-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{a.substance}</span>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${severityColor}`}>
                      {a.severity.replace("_", " ")}
                    </span>
                  </div>
                  {a.reaction && (
                    <div className="text-xs text-muted-foreground">{a.reaction}</div>
                  )}
                  {a.onset_date && (
                    <div className="text-xs text-muted-foreground">Onset: {a.onset_date}</div>
                  )}
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(a.id)}>
                  <Icons.x className="h-3 w-3" />
                </Button>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
