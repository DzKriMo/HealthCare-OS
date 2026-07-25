"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { formatName } from "@/lib/utils";
import type { Patient } from "@healthcare-os/types";

export default function PatientsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } =
    useAuthStore();

  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) loadPatients();
  }, [isAuthenticated]);

  const loadPatients = async () => {
    try {
      const data = await api.get<{ results: Patient[] }>("/patients/");
      setPatients(data.results);
    } catch {
      setPageError("Failed to load patients.");
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searchQuery.length < 2) {
      loadPatients();
      return;
    }
    setIsSearching(true);
    try {
      const data = await api.get<{ results: Patient[] }>(
        `/patients/?q=${encodeURIComponent(searchQuery)}`,
      );
      setPatients(data.results);
    } catch {
      setPageError("Search failed.");
    } finally {
      setIsSearching(false);
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
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Patients</h1>
            <p className="text-muted-foreground">
              {patients.length} active patient{patients.length !== 1 ? "s" : ""}
            </p>
          </div>
          <Button onClick={() => router.push("/patients/new")}>
            <Icons.plus className="mr-2 h-4 w-4" />
            New Patient
          </Button>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <Input
            placeholder="Search by name, phone, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-md"
          />
          <Button type="submit" variant="secondary" disabled={isSearching}>
            <Icons.search className="mr-2 h-4 w-4" />
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </form>

        {pageError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {pageError}
          </div>
        )}

        {/* Patient list */}
        <div className="space-y-2">
          {patients.map((patient) => (
            <Card
              key={patient.id}
              className="cursor-pointer transition-colors hover:border-primary"
              onClick={() => router.push(`/patients/${patient.id}`)}
            >
              <CardContent className="flex items-center gap-4 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                  {patient.first_name?.[0]}{patient.last_name?.[0]}
                </div>
                <div className="flex-1">
                  <div className="font-medium">
                    {formatName(patient.first_name, patient.last_name)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {patient.display_id || patient.id?.slice(0, 8)} ·{" "}
                    {patient.date_of_birth} · {patient.gender}
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {patient.phone_primary}
                </div>
                <Icons.chevronDown className="h-4 w-4 rotate-270 text-muted-foreground" />
              </CardContent>
            </Card>
          ))}

          {patients.length === 0 && !isSearching && (
            <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
              <Icons.users className="mx-auto mb-3 h-8 w-8" />
              <p className="font-medium">No patients found</p>
              <p className="text-sm mt-1">
                {searchQuery
                  ? "Try a different search term."
                  : "Register your first patient to get started."}
              </p>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
