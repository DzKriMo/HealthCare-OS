"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";
import { formatName } from "@/lib/utils";
import type { Patient } from "@healthcare-os/types";

const PAGE_SIZE = 20;

export default function PatientsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [patients, setPatients] = useState<Patient[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setPage(1);
    }, 300);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [searchQuery]);

  useEffect(() => {
    if (isAuthenticated) loadPatients();
  }, [isAuthenticated, page, debouncedQuery]);

  const loadPatients = useCallback(async () => {
    setLoading(true);
    setPageError("");
    try {
      const q = debouncedQuery ? `&q=${encodeURIComponent(debouncedQuery)}` : "";
      const offset = (page - 1) * PAGE_SIZE;
      const data = await api.get<{ count: number; results: Patient[] }>(
        `/patients/?limit=${PAGE_SIZE}&offset=${offset}${q}`,
      );
      setPatients(data.results);
      setTotalCount(data.count);
      setTotalPages(Math.max(1, Math.ceil(data.count / PAGE_SIZE)));
    } catch {
      setPageError("Failed to load patients.");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedQuery]);

  if (authLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Patients</h1>
            <p className="text-muted-foreground">
              {totalCount} patient{totalCount !== 1 ? "s" : ""}
              {debouncedQuery && ` matching "${debouncedQuery}"`}
            </p>
          </div>
          <Button onClick={() => router.push("/patients/new")}>
            <Icons.plus className="mr-2 h-4 w-4" />
            New Patient
          </Button>
        </div>

        <Input
          placeholder="Search by name, phone, or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-md"
        />

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {pageError}
            <Button variant="link" size="sm" onClick={loadPatients}>Retry</Button>
          </div>
        )}

        {loading ? (
          <SkeletonTable rows={8} />
        ) : (
          <>
            <div className="space-y-2">
              {patients.map((patient) => (
                <Card
                  key={patient.id}
                  className="transition-colors hover:border-primary"
                >
                  <CardContent className="flex items-center gap-4 p-4">
                    <div
                      className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary"
                      onClick={() => router.push(`/patients/${patient.id}`)}
                    >
                      {patient.first_name?.[0]}{patient.last_name?.[0]}
                    </div>
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => router.push(`/patients/${patient.id}`)}
                    >
                      <div className="font-medium">
                        {formatName(patient.first_name, patient.last_name)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {patient.display_id || patient.id?.slice(0, 8)} ·{" "}
                        {patient.date_of_birth} · {patient.gender}
                      </div>
                    </div>
                    <div
                      className="hidden text-sm text-muted-foreground sm:block cursor-pointer"
                      onClick={() => router.push(`/patients/${patient.id}`)}
                    >
                      {patient.phone_primary}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => router.push(`/appointments/new?patient=${patient.id}`)}
                        title="Book appointment"
                      >
                        <Icons.calendar className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => router.push(`/billing/new?patient=${patient.id}`)}
                        title="Create invoice"
                      >
                        <Icons.creditCard className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost" size="sm"
                        onClick={() => router.push(`/patients/${patient.id}#timeline`)}
                        title="View timeline"
                      >
                        <Icons.barChart className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {patients.length === 0 && !loading && (
                <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                  <Icons.users className="mx-auto mb-3 h-8 w-8" />
                  <p className="font-medium">No patients found</p>
                  <p className="text-sm mt-1">
                    {debouncedQuery
                      ? "Try a different search term."
                      : "Register your first patient to get started."}
                  </p>
                </div>
              )}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline" size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline" size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardShell>
  );
}
