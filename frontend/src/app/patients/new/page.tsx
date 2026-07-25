"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import { ApiRequestError } from "@/lib/api/client";

const GENDERS = ["male", "female", "other", "unknown"];
const BLOOD_TYPES = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
const MARITAL = ["", "single", "married", "divorced", "widowed", "unknown"];

interface FormState {
  first_name: string;
  middle_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_type: string;
  marital_status: string;
  national_id: string;
  phone_primary: string;
  phone_secondary: string;
  email: string;
  address_line1: string;
  city: string;
  country: string;
}

const EMPTY: FormState = {
  first_name: "", middle_name: "", last_name: "", date_of_birth: "",
  gender: "unknown", blood_type: "", marital_status: "", national_id: "",
  phone_primary: "", phone_secondary: "", email: "",
  address_line1: "", city: "", country: "",
};

export default function NewPatientPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [form, setForm] = useState<FormState>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [correlationId, setCorrelationId] = useState<string | undefined>();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  const set = (k: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCorrelationId(undefined);

    if (!form.first_name.trim() || !form.last_name.trim() || !form.date_of_birth) {
      setError("First name, last name, and date of birth are required.");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = { ...form };
      // Drop empty optional fields
      Object.keys(payload).forEach((k) => {
        if (payload[k] === "") delete payload[k];
      });
      const created = await api.post<{ id: string }>("/patients/", payload);
      router.push(`/patients/${created.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
        setCorrelationId(err.correlationId);
      } else {
        setError("Failed to create patient. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Patient</h1>
          <p className="text-muted-foreground">Register a new patient record.</p>
        </div>

        {error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
            {correlationId && (
              <span className="mt-1 block text-xs opacity-70">Ref: {correlationId}</span>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Demographics</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="first_name">First name *</Label>
                <Input id="first_name" value={form.first_name} onChange={set("first_name")} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="last_name">Last name *</Label>
                <Input id="last_name" value={form.last_name} onChange={set("last_name")} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="middle_name">Middle name</Label>
                <Input id="middle_name" value={form.middle_name} onChange={set("middle_name")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="date_of_birth">Date of birth *</Label>
                <Input id="date_of_birth" type="date" value={form.date_of_birth} onChange={set("date_of_birth")} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="gender">Gender</Label>
                <select id="gender" value={form.gender} onChange={set("gender")}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {GENDERS.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="blood_type">Blood type</Label>
                <select id="blood_type" value={form.blood_type} onChange={set("blood_type")}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {BLOOD_TYPES.map((b) => <option key={b} value={b}>{b || "—"}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="marital_status">Marital status</Label>
                <select id="marital_status" value={form.marital_status} onChange={set("marital_status")}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                  {MARITAL.map((m) => <option key={m} value={m}>{m || "—"}</option>)}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="national_id">National ID</Label>
                <Input id="national_id" value={form.national_id} onChange={set("national_id")} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="phone_primary">Phone (primary)</Label>
                <Input id="phone_primary" value={form.phone_primary} onChange={set("phone_primary")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="phone_secondary">Phone (secondary)</Label>
                <Input id="phone_secondary" value={form.phone_secondary} onChange={set("phone_secondary")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={form.email} onChange={set("email")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="address_line1">Address</Label>
                <Input id="address_line1" value={form.address_line1} onChange={set("address_line1")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="city">City</Label>
                <Input id="city" value={form.city} onChange={set("city")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="country">Country</Label>
                <Input id="country" value={form.country} onChange={set("country")} />
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Create Patient"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.push("/patients")}>
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </DashboardShell>
  );
}
