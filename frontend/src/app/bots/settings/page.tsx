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

interface BotSettings {
  whatsapp_enabled: boolean; whatsapp_from_number: string; whatsapp_business_account_id: string;
  voice_enabled: boolean; voice_from_number: string; voice_language: string;
  auto_reply_enabled: boolean; auto_reply_message: string;
  appointment_reminders_enabled: boolean; appointment_reminder_hours_before: number;
  follow_up_enabled: boolean; business_hours_only: boolean;
  business_hours_start: string; business_hours_end: string; timezone: string;
}

export default function BotSettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();
  const [settings, setSettings] = useState<BotSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);
  useEffect(() => {
    if (isAuthenticated) load();
  }, [isAuthenticated]);

  const load = async () => {
    try {
      const data = await api.get<BotSettings>("/bots/settings/");
      setSettings(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await api.put("/bots/settings/", settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const update = <K extends keyof BotSettings>(key: K, value: BotSettings[K]) => {
    if (!settings) return;
    setSettings({ ...settings, [key]: value });
  };

  if (authLoading || !user) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );

  if (loading) return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl"><Card><CardContent><div className="h-60 animate-pulse rounded-lg bg-muted" /></CardContent></Card></div>
    </DashboardShell>
  );

  if (!settings) return null;

  return (
    <DashboardShell user={user} onLogout={logout}>
      <div className="mx-auto max-w-2xl space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/bots")}>
          <Icons.chevronDown className="mr-1 h-4 w-4 rotate-90" /> Back
        </Button>

        <Card>
          <CardHeader><CardTitle>WhatsApp Bot Settings</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ToggleRow label="Enable WhatsApp Bot" checked={settings.whatsapp_enabled} onChange={(v) => update("whatsapp_enabled", v)} />
            {settings.whatsapp_enabled && (
              <>
                <Field label="WhatsApp From Number" value={settings.whatsapp_from_number} onChange={(v) => update("whatsapp_from_number", v)} placeholder="+1234567890" />
                <Field label="Business Account ID" value={settings.whatsapp_business_account_id} onChange={(v) => update("whatsapp_business_account_id", v)} />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Voice Bot Settings</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ToggleRow label="Enable Voice Bot" checked={settings.voice_enabled} onChange={(v) => update("voice_enabled", v)} />
            {settings.voice_enabled && (
              <>
                <Field label="Voice From Number" value={settings.voice_from_number} onChange={(v) => update("voice_from_number", v)} placeholder="+1234567890" />
                <Field label="TTS Language" value={settings.voice_language} onChange={(v) => update("voice_language", v)} placeholder="en-US" />
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Auto-Reply</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ToggleRow label="Enable Auto-Reply" checked={settings.auto_reply_enabled} onChange={(v) => update("auto_reply_enabled", v)} />
            {settings.auto_reply_enabled && (
              <div className="space-y-2">
                <Label>Default Auto-Reply Message</Label>
                <textarea
                  className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={settings.auto_reply_message}
                  onChange={(e) => update("auto_reply_message", e.target.value)}
                />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Appointment Reminders</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ToggleRow label="Send Appointment Reminders" checked={settings.appointment_reminders_enabled} onChange={(v) => update("appointment_reminders_enabled", v)} />
            {settings.appointment_reminders_enabled && (
              <Field label="Reminder Hours Before" value={String(settings.appointment_reminder_hours_before)} onChange={(v) => update("appointment_reminder_hours_before", parseInt(v) || 24)} />
            )}
            <ToggleRow label="Follow-Up Messages" checked={settings.follow_up_enabled} onChange={(v) => update("follow_up_enabled", v)} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Business Hours</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <ToggleRow label="Business Hours Only" checked={settings.business_hours_only} onChange={(v) => update("business_hours_only", v)} />
            {settings.business_hours_only && (
              <div className="grid gap-4 md:grid-cols-2">
                <Field label="Start Time" value={settings.business_hours_start} onChange={(v) => update("business_hours_start", v)} />
                <Field label="End Time" value={settings.business_hours_end} onChange={(v) => update("business_hours_end", v)} />
              </div>
            )}
            <Field label="Timezone" value={settings.timezone} onChange={(v) => update("timezone", v)} />
          </CardContent>
        </Card>

        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
        </Button>
      </div>
    </DashboardShell>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <span className="text-sm font-medium">{label}</span>
      <input type="checkbox" className="h-5 w-5" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    </div>
  );
}

function Field({ label, value, onChange, placeholder }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  );
}
