"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface InsuranceEntry {
  id: string;
  provider: string;
  policy_number: string;
  group_number: string;
  coverage_type: string;
  plan_name: string;
  effective_date: string;
  expiration_date: string | null;
  is_verified: boolean;
  is_active: boolean;
}

const COVERAGE_TYPES = ["primary", "secondary", "tertiary"];

interface Props {
  patientId: string;
}

export function InsuranceList({ patientId }: Props) {
  const [policies, setPolicies] = useState<InsuranceEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [provider, setProvider] = useState("");
  const [policyNumber, setPolicyNumber] = useState("");
  const [groupNumber, setGroupNumber] = useState("");
  const [coverageType, setCoverageType] = useState("primary");
  const [planName, setPlanName] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [expirationDate, setExpirationDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: InsuranceEntry[] }>(
        `/patients/${patientId}/insurance/`,
      );
      setPolicies(data.results);
    } catch {
      setError("Failed to load insurance");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!provider.trim() || !policyNumber.trim() || !effectiveDate) {
      setFormError("Provider, policy number, and effective date are required");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post(`/patients/${patientId}/insurance/`, {
        patient: patientId,
        provider: provider.trim(),
        policy_number: policyNumber.trim(),
        group_number: groupNumber,
        coverage_type: coverageType,
        plan_name: planName,
        effective_date: effectiveDate,
        expiration_date: expirationDate || null,
      });
      setProvider(""); setPolicyNumber(""); setGroupNumber(""); setPlanName("");
      setEffectiveDate(""); setExpirationDate("");
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
      await api.delete(`/patients/insurance/${id}/`);
      await load();
    } catch {
      setError("Failed to delete");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Insurance</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Insurance</CardTitle>
          <p className="text-sm text-muted-foreground">
            {policies.length} polic{policies.length !== 1 ? "ies" : "y"}
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
                <Label>Provider *</Label>
                <Input value={provider} onChange={(e) => setProvider(e.target.value)} placeholder="e.g. Blue Cross" />
              </div>
              <div className="space-y-1">
                <Label>Coverage type</Label>
                <select value={coverageType} onChange={(e) => setCoverageType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {COVERAGE_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label>Policy number *</Label>
                <Input value={policyNumber} onChange={(e) => setPolicyNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Group number</Label>
                <Input value={groupNumber} onChange={(e) => setGroupNumber(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Plan name</Label>
                <Input value={planName} onChange={(e) => setPlanName(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Effective date *</Label>
                <Input type="date" value={effectiveDate} onChange={(e) => setEffectiveDate(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Expiration date</Label>
                <Input type="date" value={expirationDate} onChange={(e) => setExpirationDate(e.target.value)} />
              </div>
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Policy"}
            </Button>
          </form>
        )}

        {policies.length === 0 && (
          <p className="text-sm text-muted-foreground">No insurance policies on record.</p>
        )}

        <div className="space-y-2">
          {policies.map((p) => (
            <div key={p.id} className="flex items-start justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{p.provider}</span>
                  <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                    {p.coverage_type}
                  </span>
                  {p.is_verified && (
                    <span className="text-xs text-green-600">Verified</span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  Policy: {p.policy_number}
                  {p.plan_name && ` · ${p.plan_name}`}
                </div>
                <div className="text-xs text-muted-foreground">
                  {p.effective_date} — {p.expiration_date || "No expiry"}
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleDelete(p.id)}>
                <Icons.x className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
