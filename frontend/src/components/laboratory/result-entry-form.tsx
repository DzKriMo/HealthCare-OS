"use client";

import { useState, useEffect, useMemo } from "react";
import { api, ApiRequestError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CatalogItem {
  id: string;
  name: string;
  short_name: string;
  department: string;
  unit: string;
  reference_range_low: number | null;
  reference_range_high: number | null;
  reference_range_text: string;
}

interface ResultFormData {
  test: string;
  specimen?: string;
  value?: number;
  value_text?: string;
  notes?: string;
}

interface Props {
  orderId: string;
  onSubmit: (data: ResultFormData) => Promise<void>;
}

export function ResultEntryForm({ orderId, onSubmit }: Props) {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [specimens, setSpecimens] = useState<{ id: string; barcode: string; specimen_type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [testId, setTestId] = useState("");
  const [specimenId, setSpecimenId] = useState("");
  const [value, setValue] = useState("");
  const [valueText, setValueText] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [catData, specData] = await Promise.all([
          api.get<{ results: CatalogItem[] }>("/lab/catalog/"),
          api.get<{ results: { id: string; barcode: string; specimen_type: string }[] }>(
            `/lab/specimens/?lab_order=${orderId}`,
          ),
        ]);
        if (!cancelled) {
          setCatalog(catData.results.filter((t) => t.id));
          setSpecimens(specData.results);
        }
      } catch {
        if (!cancelled) setError("Failed to load catalog or specimens");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [orderId]);

  const selectedTest = useMemo(
    () => catalog.find((t) => t.id === testId),
    [catalog, testId],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testId) {
      setError("Please select a test");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await onSubmit({
        test: testId,
        specimen: specimenId || undefined,
        value: value ? Number(value) : undefined,
        value_text: valueText || undefined,
        notes: notes || undefined,
      });
      setValue("");
      setValueText("");
      setNotes("");
      setSpecimenId("");
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.message : "Failed to save result",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Enter Result</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 animate-pulse rounded-lg bg-muted" />
        </CardContent>
      </Card>
    );
  }

  const selectCls =
    "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Enter Result</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="space-y-1.5">
            <Label htmlFor="test">Test *</Label>
            <select
              id="test"
              value={testId}
              onChange={(e) => {
                setTestId(e.target.value);
                setValue("");
                setValueText("");
              }}
              required
              className={selectCls}
            >
              <option value="">Select a test...</option>
              {catalog.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.short_name || t.name} ({t.department})
                </option>
              ))}
            </select>
          </div>

          {selectedTest && (
            <div className="rounded-md bg-muted p-3 text-sm">
              <p>
                <strong>{selectedTest.short_name || selectedTest.name}</strong>
                {selectedTest.unit && (
                  <span className="text-muted-foreground"> ({selectedTest.unit})</span>
                )}
              </p>
              {selectedTest.reference_range_text ? (
                <p className="mt-0.5 text-muted-foreground">
                  Ref: {selectedTest.reference_range_text}
                </p>
              ) : selectedTest.reference_range_low != null ? (
                <p className="mt-0.5 text-muted-foreground">
                  Ref: {selectedTest.reference_range_low} – {selectedTest.reference_range_high}{" "}
                  {selectedTest.unit}
                </p>
              ) : (
                <p className="mt-0.5 text-muted-foreground">No reference range</p>
              )}
            </div>
          )}

          {specimens.length > 0 && (
            <div className="space-y-1.5">
              <Label htmlFor="specimen">Specimen (optional)</Label>
              <select
                id="specimen"
                value={specimenId}
                onChange={(e) => setSpecimenId(e.target.value)}
                className={selectCls}
              >
                <option value="">No specimen</option>
                {specimens.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.barcode} — {s.specimen_type}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedTest?.unit && (
            <div className="space-y-1.5">
              <Label htmlFor="value">
                Value ({selectedTest.unit})
              </Label>
              <Input
                id="value"
                type="number"
                step="any"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={`Enter numeric value in ${selectedTest.unit}`}
              />
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="value_text">
              {selectedTest?.unit ? "Value text (if no numeric value)" : "Value"}
            </Label>
            <Input
              id="value_text"
              value={valueText}
              onChange={(e) => setValueText(e.target.value)}
              placeholder="e.g. Positive, Negative, Not detected, etc."
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="notes">Notes</Label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              placeholder="Any additional notes..."
            />
          </div>

          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Save Result"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
