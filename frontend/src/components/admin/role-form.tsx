"use client";

import { useState } from "react";
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

interface RoleFormProps {
  initial?: {
    name?: string;
    description?: string;
  };
  permissionsByResource: Record<string, { id: string; codename: string; description: string; action: string }[]>;
  selectedIds: string[];
  onPermissionsChange: (ids: string[]) => void;
  onSubmit: (data: { name: string; description: string; permission_ids: string[] }) => Promise<void>;
  loading: boolean;
}

export function RoleForm({
  initial,
  permissionsByResource,
  selectedIds,
  onPermissionsChange,
  onSubmit,
  loading,
}: RoleFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");

  const togglePermission = (codename: string) => {
    onPermissionsChange(
      selectedIds.includes(codename)
        ? selectedIds.filter((id) => id !== codename)
        : [...selectedIds, codename],
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await onSubmit({
      name: name.trim(),
      description: description.trim(),
      permission_ids: selectedIds,
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>{initial ? "Edit Role" : "Create Role"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="role_name">Role name</Label>
            <Input
              id="role_name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="e.g. Senior Doctor"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role_description">Description</Label>
            <Input
              id="role_description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What this role can do"
            />
          </div>
          <div className="space-y-2">
            <Label>Permissions</Label>
            <div className="max-h-72 space-y-4 overflow-y-auto rounded-md border p-4">
              {Object.entries(permissionsByResource).map(([resource, perms]) => (
                <div key={resource}>
                  <h4 className="mb-1 text-sm font-semibold capitalize">{resource}</h4>
                  <div className="space-y-1">
                    {perms.map((perm) => (
                      <label
                        key={perm.id}
                        className="flex items-center gap-2 text-sm"
                      >
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(perm.codename)}
                          onChange={() => togglePermission(perm.codename)}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <span className="text-muted-foreground">{perm.description || perm.codename}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-end gap-2">
          <Button type="submit" disabled={!name.trim() || loading}>
            {loading ? "Saving..." : initial ? "Update Role" : "Create Role"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
