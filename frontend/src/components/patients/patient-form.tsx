"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiRequestError } from "@/lib/api/client";

const GENDERS = ["male", "female", "other", "unknown"];
const BLOOD_TYPES = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
const MARITAL = ["", "single", "married", "divorced", "widowed", "unknown"];

export interface PatientFormData {
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
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

interface Props {
  initialData?: Partial<PatientFormData>;
  patientId?: string;
  isEdit?: boolean;
}

export function PatientForm({ initialData = {}, patientId, isEdit }: Props) {
  const router = useRouter();
  const [form, setForm] = useState<PatientFormData>({
    first_name: "", middle_name: "", last_name: "", date_of_birth: "",
    gender: "unknown", blood_type: "", marital_status: "", national_id: "",
    phone_primary: "", phone_secondary: "", email: "",
    address_line1: "", address_line2: "", city: "", state: "", postal_code: "", country: "US",
    ...initialData,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof PatientFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [correlationId, setCorrelationId] = useState<string | undefined>();

  const set = (k: keyof PatientFormData) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = (): boolean => {
    const errs: Partial<Record<keyof PatientFormData, string>> = {};
    if (!form.first_name.trim()) errs.first_name = "Required";
    if (!form.last_name.trim()) errs.last_name = "Required";
    if (!form.date_of_birth) errs.date_of_birth = "Required";
    if (form.date_of_birth && !/^\d{4}-\d{2}-\d{2}$/.test(form.date_of_birth)) {
      errs.date_of_birth = "Must be YYYY-MM-DD";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError("");
    setCorrelationId(undefined);
    if (!validate()) return;

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(form)) {
        if (v !== "") payload[k] = v;
      }

      if (isEdit && patientId) {
        await api.put(`/patients/${patientId}/`, payload);
        router.push(`/patients/${patientId}`);
      } else {
        const created = await api.post<{ id: string }>("/patients/", payload);
        router.push(`/patients/${created.id}`);
      }
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setSubmitError(err.message);
        setCorrelationId(err.correlationId);
      } else {
        setSubmitError("Failed to save patient. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const Field = ({ name, label, type, required, placeholder }: {
    name: keyof PatientFormData;
    label: string;
    type?: string;
    required?: boolean;
    placeholder?: string;
  }) => (
    <div className="space-y-1.5">
      <Label htmlFor={name}>{label}{required && " *"}</Label>
      <Input id={name} type={type || "text"} value={form[name]} onChange={set(name)} required={required} placeholder={placeholder} />
      {errors[name] && <p className="text-xs text-destructive">{errors[name]}</p>}
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {submitError && (
        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
          {submitError}
          {correlationId && (
            <span className="mt-1 block text-xs opacity-70">Ref: {correlationId}</span>
          )}
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>Demographics</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field name="first_name" label="First name" required />
          <Field name="middle_name" label="Middle name" />
          <Field name="last_name" label="Last name" required />
          <Field name="date_of_birth" label="Date of birth" type="date" required />
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
              {BLOOD_TYPES.map((b) => <option key={b} value={b}>{b || "\u2014"}</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="marital_status">Marital status</Label>
            <select id="marital_status" value={form.marital_status} onChange={set("marital_status")}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
              {MARITAL.map((m) => <option key={m} value={m}>{m || "\u2014"}</option>)}
            </select>
          </div>
          <Field name="national_id" label="National ID" placeholder="SSN, passport, etc." />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Contact</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field name="phone_primary" label="Phone (primary)" placeholder="+1 (555) 123-4567" />
          <Field name="phone_secondary" label="Phone (secondary)" />
          <Field name="email" label="Email" type="email" />
          <Field name="address_line1" label="Address line 1" />
          <Field name="address_line2" label="Address line 2" />
          <Field name="city" label="City" />
          <Field name="state" label="State / Province" />
          <Field name="postal_code" label="Postal code" />
          <Field name="country" label="Country" placeholder="US" />
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : isEdit ? "Save Changes" : "Create Patient"}
        </Button>
        <Button type="button" variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
