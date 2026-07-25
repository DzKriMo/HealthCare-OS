"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface CatalogItem {
  id: string;
  name: string;
  short_name: string;
  department: string;
  specimen_type: string;
  unit: string;
  reference_range_low: number | null;
  reference_range_high: number | null;
  reference_range_text: string;
  turnaround_minutes: number;
  price: string;
  is_active: boolean;
}

type Department =
  | "hematology"
  | "chemistry"
  | "microbiology"
  | "immunology"
  | "pathology"
  | "urinalysis"
  | "other";

const DEPARTMENTS: { value: Department; label: string }[] = [
  { value: "hematology", label: "Hematology" },
  { value: "chemistry", label: "Chemistry" },
  { value: "microbiology", label: "Microbiology" },
  { value: "immunology", label: "Immunology" },
  { value: "pathology", label: "Pathology" },
  { value: "urinalysis", label: "Urinalysis" },
  { value: "other", label: "Other" },
];

interface Props {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function TestCatalogSelect({ selectedIds, onChange }: Props) {
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const data = await api.get<{ results: CatalogItem[] }>("/lab/catalog/");
        if (!cancelled) setItems(data.results.filter((t) => t.is_active));
      } catch {
        /* silently fail */
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.short_name.toLowerCase().includes(q) ||
        t.department.toLowerCase().includes(q),
    );
  }, [items, search]);

  const grouped = useMemo(() => {
    const map: Record<string, CatalogItem[]> = {};
    for (const item of filtered) {
      const dept = item.department || "other";
      if (!map[dept]) map[dept] = [];
      map[dept].push(item);
    }
    return map;
  }, [filtered]);

  const toggle = (id: string) => {
    const next = selectedIds.includes(id)
      ? selectedIds.filter((x) => x !== id)
      : [...selectedIds, id];
    onChange(next);
  };

  const toggleDepartment = (dept: string, deptItems: CatalogItem[]) => {
    const deptIds = deptItems.map((t) => t.id);
    const allSelected = deptIds.every((id) => selectedIds.includes(id));
    const next = allSelected
      ? selectedIds.filter((id) => !deptIds.includes(id))
      : [...new Set([...selectedIds, ...deptIds])];
    onChange(next);
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-10 animate-pulse rounded-md bg-muted" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-8 animate-pulse rounded bg-muted" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <Input
        placeholder="Search tests by name or department..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground">No tests found.</p>
      )}
      <div className="max-h-96 space-y-2 overflow-y-auto">
        {DEPARTMENTS.filter((d) => grouped[d.value]).map((dept) => {
          const deptItems = grouped[dept.value];
          const allSelected = deptItems.every((t) => selectedIds.includes(t.id));
          const someSelected = deptItems.some((t) => selectedIds.includes(t.id));
          return (
            <div key={dept.value}>
              <button
                type="button"
                onClick={() => toggleDepartment(dept.value, deptItems)}
                className={cn(
                  "flex w-full items-center gap-2 rounded px-2 py-1 text-left text-xs font-semibold uppercase tracking-wider transition-colors hover:bg-muted",
                  allSelected && "text-primary",
                  someSelected && !allSelected && "text-primary/70",
                )}
              >
                <div
                  className={cn(
                    "flex h-4 w-4 items-center justify-center rounded border",
                    allSelected
                      ? "border-primary bg-primary text-primary-foreground"
                      : someSelected
                        ? "border-primary/50 bg-primary/10"
                        : "border-input",
                  )}
                >
                  {(allSelected || someSelected) && (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-3 w-3"
                    >
                      {allSelected ? (
                        <polyline points="20 6 9 17 4 12" />
                      ) : (
                        <line x1="5" y1="12" x2="19" y2="12" />
                      )}
                    </svg>
                  )}
                </div>
                {dept.label}
                <span className="ml-auto text-muted-foreground">
                  {deptItems.length}
                </span>
              </button>
              <div className="ml-4 space-y-0.5">
                {deptItems.map((item) => (
                  <label
                    key={item.id}
                    className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm transition-colors hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={() => toggle(item.id)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <span className="font-medium">{item.short_name || item.name}</span>
                    {item.unit && (
                      <span className="text-xs text-muted-foreground">{item.unit}</span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
