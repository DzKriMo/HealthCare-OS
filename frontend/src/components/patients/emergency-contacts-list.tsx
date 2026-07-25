"use client";

import { useState, useEffect } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";

interface ContactEntry {
  id: string;
  name: string;
  relationship: string;
  phone_primary: string;
  phone_secondary: string;
  email: string;
  address: string;
  is_primary: boolean;
}

interface Props {
  patientId: string;
}

export function EmergencyContactsList({ patientId }: Props) {
  const [contacts, setContacts] = useState<ContactEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [relationship, setRelationship] = useState("");
  const [phonePrimary, setPhonePrimary] = useState("");
  const [phoneSecondary, setPhoneSecondary] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.get<{ results: ContactEntry[] }>(
        `/patients/${patientId}/contacts/`,
      );
      setContacts(data.results);
    } catch {
      setError("Failed to load contacts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [patientId]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !relationship.trim() || !phonePrimary.trim()) {
      setFormError("Name, relationship, and phone are required");
      return;
    }
    setSubmitting(true);
    setFormError("");
    try {
      await api.post(`/patients/${patientId}/contacts/`, {
        patient: patientId,
        name: name.trim(),
        relationship: relationship.trim(),
        phone_primary: phonePrimary.trim(),
        phone_secondary: phoneSecondary,
        email,
        address,
        is_primary: isPrimary,
      });
      setName(""); setRelationship(""); setPhonePrimary(""); setPhoneSecondary("");
      setEmail(""); setAddress(""); setIsPrimary(false);
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
      await api.delete(`/patients/contacts/${id}/`);
      await load();
    } catch {
      setError("Failed to delete");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Emergency Contacts</CardTitle></CardHeader>
        <CardContent><div className="h-16 animate-pulse rounded-lg bg-muted" /></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Emergency Contacts</CardTitle>
          <p className="text-sm text-muted-foreground">
            {contacts.length} contact{contacts.length !== 1 ? "s" : ""}
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
                <Label>Name *</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Relationship *</Label>
                <Input value={relationship} onChange={(e) => setRelationship(e.target.value)} placeholder="e.g. Spouse" />
              </div>
              <div className="space-y-1">
                <Label>Phone *</Label>
                <Input value={phonePrimary} onChange={(e) => setPhonePrimary(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Alt. phone</Label>
                <Input value={phoneSecondary} onChange={(e) => setPhoneSecondary(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>Email</Label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={isPrimary} onChange={(e) => setIsPrimary(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300" />
                  Primary contact
                </label>
              </div>
            </div>
            <div className="space-y-1">
              <Label>Address</Label>
              <textarea value={address} onChange={(e) => setAddress(e.target.value)}
                className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            {formError && <p className="text-xs text-destructive">{formError}</p>}
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Adding..." : "Add Contact"}
            </Button>
          </form>
        )}

        {contacts.length === 0 && (
          <p className="text-sm text-muted-foreground">No emergency contacts on record.</p>
        )}

        <div className="space-y-2">
          {contacts.map((c) => (
            <div key={c.id} className="flex items-start justify-between rounded-lg border p-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{c.name}</span>
                  {c.is_primary && (
                    <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-800">
                      Primary
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">{c.relationship}</div>
                <div className="text-xs text-muted-foreground">{c.phone_primary}</div>
                {c.email && <div className="text-xs text-muted-foreground">{c.email}</div>}
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleDelete(c.id)}>
                <Icons.x className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
