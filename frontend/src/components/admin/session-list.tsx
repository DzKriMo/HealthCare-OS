"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { cn } from "@/lib/utils";

interface Session {
  id: string;
  device_name: string;
  device_type: string;
  ip_address: string;
  user_agent: string;
  location: string;
  created_at: string;
  expires_at: string;
  is_active: boolean;
}

export function SessionList() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revoking, setRevoking] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get<Session[]>("/auth/sessions/");
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleRevoke = async (sessionId: string) => {
    setRevoking(sessionId);
    setError("");
    try {
      await api.post("/auth/sessions/revoke/", { session_id: sessionId });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke session");
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAllOthers = async () => {
    setRevokingAll(true);
    setError("");
    try {
      await api.post("/auth/sessions/revoke/", { revoke_all_others: true });
      setSessions((prev) => prev.filter((s) => !s.is_active));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke sessions");
    } finally {
      setRevokingAll(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(dateStr));
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Active Sessions</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRevokeAllOthers}
          disabled={revokingAll || sessions.length <= 1}
        >
          {revokingAll ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          ) : (
            <Icons.x className="mr-1 h-4 w-4" />
          )}
          Revoke all others
        </Button>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        {sessions.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
            <Icons.settings className="mx-auto mb-3 h-8 w-8" />
            <p>No active sessions.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-3 pr-4 font-medium">Device</th>
                  <th className="pb-3 pr-4 font-medium">IP address</th>
                  <th className="pb-3 pr-4 font-medium">Location</th>
                  <th className="pb-3 pr-4 font-medium">Created</th>
                  <th className="pb-3 pr-4 font-medium">Expires</th>
                  <th className="pb-3 pr-4 font-medium">Status</th>
                  <th className="pb-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => (
                  <tr key={session.id} className="border-b last:border-0">
                    <td className="py-3 pr-4">
                      <div className="font-medium">{session.device_name || "Unknown"}</div>
                      <div className="text-xs text-muted-foreground">
                        {session.device_type || "—"}
                      </div>
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs">
                      {session.ip_address || "—"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {session.location || "—"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {formatDate(session.created_at)}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {formatDate(session.expires_at)}
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          session.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-gray-100 text-gray-500",
                        )}
                      >
                        {session.is_active ? "Active" : "Expired"}
                      </span>
                    </td>
                    <td className="py-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => handleRevoke(session.id)}
                        disabled={revoking === session.id || !session.is_active}
                      >
                        {revoking === session.id ? (
                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        ) : (
                          "Revoke"
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
