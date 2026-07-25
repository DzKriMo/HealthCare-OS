"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface ReferralEntry {
  id: string;
  specialist_name: string;
  specialty: string;
  reason: string;
  urgency: string;
  status: string;
  notes: string;
  created_at: string;
}

const URGENCIES = ["routine", "urgent", "stat"];

const URGENCY_BADGE: Record<string, string> = {
  routine: "bg-green-100 text-green-800",
  urgent: "bg-amber-100 text-amber-800",
  stat: "bg-red-100 text-red-800",
};

interface Props {
  patientId: string;
  encounterId?: string;
}

export function ReferralList({ patientId, encounterId }: Props) {
  const [referrals, setReferrals] = useState<ReferralEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [specialistName, setSpecialistName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [reason, setReason] = useState("");
  const [urgency, setUrgency] = useState("routine");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const params = encounterId
        ? `/clinical/referrals/?encounter=${encounterId}`
        : `/clinical/referrals/?patient=${patientId}`;
      const data = await api.get<{ results: ReferralEntry[] }>(params);
      setReferrals(data.results);
    } catch {
      setError("Failed to load referrals");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId, encounterId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!specialistName.trim() || !specialty.trim() || !reason.trim()) {
      setFormError("Specialist name, specialty, and reason are required");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post("/clinical/referrals/", {
        patient: patientId,
        encounter: encounterId || null,
        specialist_name: specialistName.trim(),
        specialty: specialty.trim(),
        reason: reason.trim(),
        urgency,
        notes,
      });
      setSpecialistName(""); setSpecialty(""); setReason(""); setNotes("");
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
        <CardHeader><CardTitle>Referrals</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Referrals</CardTitle>
          <p className="text-sm text-muted-foreground">
            {referrals.length} referral{referrals.length !== 1 ? "s" : ""}
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
                <Label>Specialist name *</Label>
                <Input value={specialistName} onChange={(e) => setSpecialistName(e.target.value)} placeholder="e.g. Dr. Smith" />
              </div>
              <div className="space-y-1">
                <Label>Specialty *</Label>
                <Input value={specialty} onChange={(e) => setSpecialty(e.target.value)} placeholder="e.g. Cardiology" />
              </div>
              <div className="space-y-1">
                <Label>Urgency</Label>
                <select value={urgency} onChange={(e) => setUrgency(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {URGENCIES.map((u) => (
                    <option key={u} value={u}>{u}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <Label>Reason *</Label>
              <textarea value={reason} onChange={(e) => setReason(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Reason for referral..." />
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Referral"}
            </Button>
          </form>
        )}

        {referrals.length === 0 && (
          <p className="text-sm text-muted-foreground">No referrals on record.</p>
        )}

        <div className="space-y-2">
          {referrals.map((r) => (
            <div key={r.id} className="flex items-start justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{r.specialist_name}</span>
                  <span className="text-xs text-muted-foreground">{r.specialty}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${URGENCY_BADGE[r.urgency] || ""}`}>
                    {r.urgency}
                  </span>
                  <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                    {r.status}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">{r.reason}</div>
                {r.notes && <div className="text-xs text-muted-foreground">{r.notes}</div>}
                <div className="text-xs text-muted-foreground">
                  {new Date(r.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
