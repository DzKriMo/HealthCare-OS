"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Icons } from "@/components/icons";
import { SkeletonTable } from "@/components/ui/skeleton";
import { api } from "@/lib/api/client";

export default function DocumentsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, fetchCurrentUser, logout } = useAuthStore();
  const [documents, setDocuments] = useState<{ id: string; name: string; category: string; uploaded_at: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) {
      api.get<{ results: typeof documents }>("/documents/")
        .then((d) => setDocuments(d.results))
        .catch(() => setError("Failed to load documents."))
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated]);

  if (isLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  return (
    <DashboardShell user={user} onLogout={logout} breadcrumbs={[{ label: "Documents" }]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
            <p className="text-muted-foreground">Files, forms, and records</p>
          </div>
          <Button><Icons.plus className="mr-2 h-4 w-4" />Upload</Button>
        </div>
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        {loading ? <SkeletonTable rows={4} /> : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <Card key={doc.id} className="cursor-pointer hover:border-primary transition-colors">
                <CardContent className="flex items-center gap-4 py-4">
                  <Icons.fileText className="h-8 w-8 text-muted-foreground" />
                  <div className="flex-1">
                    <div className="font-medium">{doc.name}</div>
                    <div className="text-sm text-muted-foreground">{doc.category}</div>
                  </div>
                  <div className="text-xs text-muted-foreground">{new Date(doc.uploaded_at).toLocaleDateString()}</div>
                </CardContent>
              </Card>
            ))}
            {documents.length === 0 && (
              <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
                <Icons.fileText className="mx-auto mb-3 h-8 w-8" />
                <p>No documents uploaded yet.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
