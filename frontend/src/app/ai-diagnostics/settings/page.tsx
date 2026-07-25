"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface AISettings {
  provider: string; api_key: string; api_endpoint: string; model: string;
  temperature: number; max_tokens: number;
  enabled_features: Record<string, boolean>;
  require_human_review: boolean;
}

export default function AISettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [settings, setSettings] = useState<AISettings>({
    provider: "openai", api_key: "", api_endpoint: "", model: "gpt-4o-mini",
    temperature: 0.3, max_tokens: 1024,
    enabled_features: { icd10_suggestion: true, soap_generation: true, drug_interaction: true, symptom_analysis: true },
    require_human_review: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) loadSettings();
  }, [isAuthenticated]);

  const loadSettings = async () => {
    try {
      const data = await api.get<AISettings>("/ai/settings/");
      setSettings(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const toggleFeature = (key: string) => {
    setSettings((prev) => ({
      ...prev,
      enabled_features: { ...prev.enabled_features, [key]: !prev.enabled_features[key] },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/ai/settings/", settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/ai-diagnostics")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        <Card>
          <CardHeader><CardTitle>AI Settings</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <select
                id="provider"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={settings.provider}
                onChange={(e) => setSettings({ ...settings, provider: e.target.value })}
              >
                <option value="openai">OpenAI</option>
                <option value="local">Local / Offline</option>
                <option value="custom">Custom Endpoint</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <Input id="api_key" type="password" value={settings.api_key} onChange={(e) => setSettings({ ...settings, api_key: e.target.value })} placeholder="sk-..." />
            </div>

            <div className="space-y-2">
              <Label htmlFor="endpoint">Custom Endpoint (optional)</Label>
              <Input id="endpoint" value={settings.api_endpoint} onChange={(e) => setSettings({ ...settings, api_endpoint: e.target.value })} placeholder="https://..." />
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="model">Model</Label>
                <Input id="model" value={settings.model} onChange={(e) => setSettings({ ...settings, model: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input id="temperature" type="number" step="0.1" min="0" max="2" value={settings.temperature} onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_tokens">Max Tokens</Label>
                <Input id="max_tokens" type="number" min="1" max="8192" value={settings.max_tokens} onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) })} />
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium">Enabled Features</h3>
              <FeatureSwitch label="ICD-10 Code Suggestions" checked={settings.enabled_features.icd10_suggestion} onChange={() => toggleFeature("icd10_suggestion")} />
              <FeatureSwitch label="SOAP Note Generation" checked={settings.enabled_features.soap_generation} onChange={() => toggleFeature("soap_generation")} />
              <FeatureSwitch label="Drug Interaction Check" checked={settings.enabled_features.drug_interaction} onChange={() => toggleFeature("drug_interaction")} />
              <FeatureSwitch label="Symptom Analysis" checked={settings.enabled_features.symptom_analysis} onChange={() => toggleFeature("symptom_analysis")} />
            </div>

            <div className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <div className="text-sm font-medium">Require Human Review</div>
                <div className="text-xs text-muted-foreground">All AI suggestions must be approved by a clinician before use</div>
              </div>
              <input type="checkbox" className="h-5 w-5" checked={settings.require_human_review} onChange={(e) => setSettings({ ...settings, require_human_review: e.target.checked })} />
            </div>

            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}

function FeatureSwitch({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <span className="text-sm">{label}</span>
      <input type="checkbox" className="h-5 w-5" checked={checked} onChange={onChange} />
    </div>
  );
}
