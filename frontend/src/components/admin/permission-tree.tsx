"use client";

import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Icons } from "@/components/icons";
import { cn } from "@/lib/utils";

interface Permission {
  id: string;
  codename: string;
  description: string;
  resource: string;
  action: string;
}

interface PermissionTreeProps {
  permissions: Permission[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function PermissionTree({ permissions, selectedIds, onChange }: PermissionTreeProps) {
  const [search, setSearch] = useState("");

  const grouped = useMemo(() => {
    const map: Record<string, Permission[]> = {};
    for (const perm of permissions) {
      const key = perm.resource || "other";
      if (!map[key]) map[key] = [];
      map[key].push(perm);
    }
    return map;
  }, [permissions]);

  const filtered = useMemo(() => {
    if (!search.trim()) return grouped;
    const q = search.toLowerCase();
    const result: Record<string, Permission[]> = {};
    for (const [resource, perms] of Object.entries(grouped)) {
      const matched = perms.filter(
        (p) =>
          p.codename.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.resource.toLowerCase().includes(q) ||
          p.action.toLowerCase().includes(q),
      );
      if (matched.length) result[resource] = matched;
    }
    return result;
  }, [grouped, search]);

  const allSelected = useMemo(
    () => permissions.length > 0 && selectedIds.length === permissions.length,
    [permissions, selectedIds],
  );

  const resourceKeys = Object.keys(filtered);

  const toggleAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(permissions.map((p) => p.codename));
    }
  };

  const toggleResource = (resource: string) => {
    const perms = grouped[resource] ?? [];
    const allResourceIds = perms.map((p) => p.codename);
    const allInResource = allResourceIds.every((id) => selectedIds.includes(id));
    if (allInResource) {
      onChange(selectedIds.filter((id) => !allResourceIds.includes(id)));
    } else {
      const existing = new Set(selectedIds);
      for (const id of allResourceIds) existing.add(id);
      onChange(Array.from(existing));
    }
  };

  const allResourceSelected = (resource: string) => {
    const perms = grouped[resource] ?? [];
    return perms.length > 0 && perms.every((p) => selectedIds.includes(p.codename));
  };

  return (
    <div className="space-y-3">
      <div className="relative">
        <Icons.search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search permissions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      <label className="flex items-center gap-2 text-sm font-medium">
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleAll}
          className="h-4 w-4 rounded border-gray-300"
        />
        Select all
      </label>
      <div className="max-h-80 space-y-4 overflow-y-auto rounded-md border p-4">
        {resourceKeys.map((resource) => (
          <div key={resource}>
            <label className="mb-1 flex items-center gap-2 text-sm font-semibold capitalize">
              <input
                type="checkbox"
                checked={allResourceSelected(resource)}
                onChange={() => toggleResource(resource)}
                className="h-4 w-4 rounded border-gray-300"
              />
              {resource}
            </label>
            <div className="ml-5 space-y-1">
              {filtered[resource].map((perm) => (
                <label
                  key={perm.id}
                  className={cn(
                    "flex items-center gap-2 text-sm",
                    search.trim() && !perm.codename.toLowerCase().includes(search.toLowerCase()) &&
                      !perm.description.toLowerCase().includes(search.toLowerCase()) &&
                      "opacity-50",
                  )}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(perm.codename)}
                    onChange={() => {
                      onChange(
                        selectedIds.includes(perm.codename)
                          ? selectedIds.filter((id) => id !== perm.codename)
                          : [...selectedIds, perm.codename],
                      );
                    }}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="text-muted-foreground">{perm.description || perm.codename}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
        {resourceKeys.length === 0 && (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No permissions match your search.
          </p>
        )}
      </div>
    </div>
  );
}
