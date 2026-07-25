"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface ConsentEntry {
  id: string;
  consent_type: string;
  form_name: string;
  form_version: string;
  status: string;
  notes: string;
  granted_at: string;
  granted_by_name: string;
  withdrawn_at: string | null;
  withdrawal_reason: string;
  expires_at: string | null;
}

const CONSENT_TYPES = [
  { value: "treatment", label: "Treatment Consent" },
  { value: "data_sharing", label: "Data Sharing" },
  { value: "marketing", label: "Marketing" },
  { value: "research", label: "Research" },
  { value: "telehealth", label: "Telehealth" },
  { value: "photography", label: "Clinical Photography" },
  { value: "other", label: "Other" },
];

interface Props {
  patientId: string;
}

export function ConsentManager({ patientId }: Props) {
  const [consents, setConsents] = useState<ConsentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [consentType, setConsentType] = useState("treatment");
  const [formName, setFormName] = useState("");
  const [formVersion, setFormVersion] = useState("1.0");
  const [notes, setNotes] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: ConsentEntry[] }>(
        `/patients/${patientId}/consents/`,
      );
      setConsents(data.results);
    } catch {
      setError("Failed to load consents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) { setFormError("Form name is required"); return; }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post(`/patients/${patientId}/consents/`, {
        patient: patientId,
        consent_type: consentType,
        form_name: formName.trim(),
        form_version: formVersion,
        notes,
        expires_at: expiresAt || null,
      });
      setFormName(""); setNotes(""); setExpiresAt("");
      setShowForm(false);
      await load();
    } catch (err) {
      setFormError(err instanceof ApiRequestError ? err.message : "Failed to add");
    } finally {
      setSubmitting(false);
    }
  };

  const handleWithdraw = async (id: string) => {
    try {
      await api.post(`/patients/consents/${id}/withdraw/`, { reason: "Withdrawn by staff" });
      await load();
    } catch {
      setError("Failed to withdraw consent");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Consents</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  const activeConsents = consents.filter((c) => c.status === "granted");
  const otherConsents = consents.filter((c) => c.status !== "granted");

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Consents</CardTitle>
          <p className="text-sm text-muted-foreground">
            {activeConsents.length} active
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
                <Label>Type</Label>
                <select value={consentType} onChange={(e) => setConsentType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {CONSENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Form name *</Label>
                <Input value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="e.g. HIPAA Release" />
              </div>
              <div className="space-y-1">
                <Label>Form version</Label>
                <Input value={formVersion} onChange={(e) => setFormVersion(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Expires at</Label>
                <Input type="datetime-local" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Record Consent"}
            </Button>
          </form>
        )}

        {consents.length === 0 && (
          <p className="text-sm text-muted-foreground">No consent records.</p>
        )}

        {activeConsents.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">ACTIVE</p>
            {activeConsents.map((c) => (
              <div key={c.id} className="flex items-start justify-between rounded-lg border border-green-200 p-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {CONSENT_TYPES.find((t) => t.value === c.consent_type)?.label || c.consent_type}
                    </span>
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-800">
                      {c.status}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {c.form_name} (v{c.form_version}) · {new Date(c.granted_at).toLocaleDateString()}
                    {c.expires_at && ` · Expires ${new Date(c.expires_at).toLocaleDateString()}`}
                  </div>
                  {c.granted_by_name && (
                    <div className="text-xs text-muted-foreground">By: {c.granted_by_name}</div>
                  )}
                </div>
                <Button variant="outline" size="sm" className="text-destructive border-destructive/30" onClick={() => handleWithdraw(c.id)}>
                  Withdraw
                </Button>
              </div>
            ))}
          </div>
        )}

        {otherConsents.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">HISTORY</p>
            {otherConsents.map((c) => (
              <div key={c.id} className="flex items-start justify-between rounded-lg border border-dashed p-3 opacity-60">
                <div className="space-y-0.5">
                  <div className="text-sm font-medium">
                    {CONSENT_TYPES.find((t) => t.value === c.consent_type)?.label || c.consent_type}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {c.form_name} · {c.status}
                    {c.withdrawn_at && ` · Withdrawn ${new Date(c.withdrawn_at).toLocaleDateString()}`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
