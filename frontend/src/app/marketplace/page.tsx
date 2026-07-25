"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface Plugin {
  id: string; name: string; slug: string; version: string; author: string;
  description: string; category: string; pricing_type: string;
  price: string; is_certified: boolean; install_count: number;
  average_rating: number; is_installed?: boolean;
}

const categoryLabels: Record<string, string> = {
  communication: "Communication",
  payment: "Payments",
  calendar: "Calendar",
  insurance: "Insurance",
  accounting: "Accounting",
  clinical: "Clinical",
  reporting: "Reporting",
  ai: "AI & Analytics",
  other: "Other",
};

export default function MarketplacePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [installedIds, setInstalledIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [installing, setInstalling] = useState<string | null>(null);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  const load = async () => {
    try {
      const [catalogRes, installedRes] = await Promise.all([
        api.get<{ results: Plugin[] }>("/integrations/marketplace/"),
        api.get<{ results: { plugin: string; id: string }[] }>("/integrations/marketplace/installed/"),
      ]);
      setPlugins(catalogRes.results);
      setInstalledIds(new Set(installedRes.results.map((i: any) => i.plugin)));
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleInstall = async (pluginId: string) => {
    setInstalling(pluginId);
    try {
      await api.post("/integrations/marketplace/installed/", { plugin: pluginId });
      setInstalledIds((prev) => new Set(prev).add(pluginId));
    } catch { /* ignore */ }
    finally { setInstalling(null); }
  };

  const filteredPlugins = plugins.filter((p) => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase()) && !p.description.toLowerCase().includes(search.toLowerCase())) return false;
    if (category && p.category !== category) return false;
    return true;
  });

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
          <p className="text-sm text-muted-foreground">Extend your Healthcare OS with integrated plugins</p>
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Search plugins..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-sm"
          />
          <select
            className="rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {Object.entries(categoryLabels).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1,2,3].map((i) => <Card key={i}><CardContent><div className="h-40 animate-pulse rounded-lg bg-muted" /></CardContent></Card>)}
          </div>
        ) : filteredPlugins.length === 0 ? (
          <Card><CardContent className="py-12 text-center text-sm text-muted-foreground">No plugins found.</CardContent></Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredPlugins.map((plugin) => (
              <Card key={plugin.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{plugin.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        {plugin.author} · v{plugin.version}
                      </p>
                    </div>
                    {plugin.is_certified && (
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                        Certified
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col">
                  <p className="flex-1 text-sm text-muted-foreground">{plugin.description}</p>
                  <div className="mt-4 flex items-center justify-between">
                    <div className="space-x-2">
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                        {categoryLabels[plugin.category] || plugin.category}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {plugin.install_count} installs
                      </span>
                    </div>
                    <div className="text-right">
                      {plugin.pricing_type === "free" ? (
                        <span className="text-sm font-medium text-green-600">Free</span>
                      ) : (
                        <span className="text-sm font-medium">${plugin.price}</span>
                      )}
                    </div>
                  </div>
                  <Button
                    className="mt-3"
                    size="sm"
                    variant={installedIds.has(plugin.id) ? "secondary" : "default"}
                    disabled={installedIds.has(plugin.id) || installing === plugin.id}
                    onClick={() => handleInstall(plugin.id)}
                  >
                    {installing === plugin.id ? "Installing..." : installedIds.has(plugin.id) ? "Installed" : "Install"}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
