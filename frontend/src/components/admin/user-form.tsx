"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface UserFormProps {
  initial?: {
    email?: string;
    first_name?: string;
    last_name?: string;
    role_id?: string;
    is_active?: boolean;
    license_number?: string;
    specialty?: string;
  };
  roles: { id: string; name: string }[];
  onSubmit: (data: UserFormData) => Promise<void>;
  loading: boolean;
}

export interface UserFormData {
  email: string;
  first_name: string;
  last_name: string;
  role_id: string;
  password?: string;
  is_active?: boolean;
  license_number?: string;
  specialty?: string;
}

export function UserForm({ initial, roles, onSubmit, loading }: UserFormProps) {
  const isEdit = !!initial;
  const [email, setEmail] = useState(initial?.email ?? "");
  const [firstName, setFirstName] = useState(initial?.first_name ?? "");
  const [lastName, setLastName] = useState(initial?.last_name ?? "");
  const [roleId, setRoleId] = useState(initial?.role_id ?? "");
  const [password, setPassword] = useState("");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [licenseNumber, setLicenseNumber] = useState(initial?.license_number ?? "");
  const [specialty, setSpecialty] = useState(initial?.specialty ?? "");

  const valid = useMemo(
    () =>
      email.trim() &&
      firstName.trim() &&
      lastName.trim() &&
      roleId &&
      (isEdit || password.length >= 8),
    [email, firstName, lastName, roleId, password, isEdit],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid) return;
    const payload: UserFormData = {
      email: email.trim(),
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      role_id: roleId,
      license_number: licenseNumber.trim() || undefined,
      specialty: specialty.trim() || undefined,
    };
    if (!isEdit) {
      payload.password = password;
    } else {
      payload.is_active = isActive;
    }
    await onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>{isEdit ? "Edit User" : "Create User"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="first_name">First name</Label>
              <Input
                id="first_name"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input
                id="last_name"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role_id">Role</Label>
            <select
              id="role_id"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              required
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">Select a role</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          {!isEdit && (
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!isEdit}
                minLength={8}
                placeholder="Min. 8 characters"
              />
            </div>
          )}
          {isEdit && (
            <div className="flex items-center gap-2">
              <input
                id="is_active"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="license_number">License number</Label>
              <Input
                id="license_number"
                value={licenseNumber}
                onChange={(e) => setLicenseNumber(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="specialty">Specialty</Label>
              <Input
                id="specialty"
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Button type="submit" disabled={!valid || loading}>
            {loading ? "Saving..." : isEdit ? "Update User" : "Create User"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
