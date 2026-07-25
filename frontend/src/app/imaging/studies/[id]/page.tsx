"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuthStore } from "@/features/auth/auth-store";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { SkeletonDetail } from "@/components/ui/skeleton";
import { ReportForm } from "@/components/imaging/report-form";
import { api } from "@/lib/api/client";

interface StudyReport {
  id: string;
  findings: string;
  impression: string;
  recommendations: string;
  status: string;
  created_by_name: string;
  created_at: string;
}

interface StudyDetail {
  id: string;
  patient_name: string;
  modality: string;
  body_part: string;
  status: string;
  priority: string;
  performed_at: string | null;
  ordered_by: string;
  reason: string;
  protocol: string;
  report_status: string;
  report: StudyReport | null;
}

const MODALITY_BADGE: Record<string, string> = {
  xray: "bg-blue-100 text-blue-800",
  ct: "bg-purple-100 text-purple-800",
  mri: "bg-indigo-100 text-indigo-800",
  ultrasound: "bg-cyan-100 text-cyan-800",
  mammography: "bg-pink-100 text-pink-800",
  nuclear: "bg-amber-100 text-amber-800",
  dexa: "bg-teal-100 text-teal-800",
  other: "bg-gray-100 text-gray-800",
};

const STATUS_BADGE: Record<string, string> = {
  scheduled: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const PRIORITY_BADGE: Record<string, string> = {
  routine: "bg-slate-100 text-slate-800",
  urgent: "bg-orange-100 text-orange-800",
  stat: "bg-red-100 text-red-800",
};

function badge(label: string, map: Record<string, string>): string {
  return map[label] || "bg-gray-100 text-gray-800";
}

export default function StudyDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { user, isAuthenticated, isLoading: authLoading, fetchCurrentUser, logout } = useAuthStore();

  const [study, setStudy] = useState<StudyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [signing, setSigning] = useState(false);
  const [reportCreated, setReportCreated] = useState(false);

  useEffect(() => { fetchCurrentUser(); }, [fetchCurrentUser]);
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) loadStudy();
  }, [isAuthenticated, reportCreated]);

  const loadStudy = async () => {
    setLoading(true);
    try {
      const data = await api.get<StudyDetail>(`/imaging/studies/${params.id}/`);
      setStudy(data);
    } catch { setPageError("Failed to load study."); }
    finally { setLoading(false); }
  };

  const handleCreateReport = async (data: { findings: string; impression: string; recommendations: string }) => {
    setReportSubmitting(true);
    try {
      await api.post("/imaging/reports/", { study: params.id, ...data });
      setReportCreated((prev) => !prev);
    } finally {
      setReportSubmitting(false);
    }
  };

  const handleSignReport = async () => {
    if (!study?.report) return;
    setSigning(true);
    try {
      await api.post(`/imaging/reports/${study.report.id}/sign/`);
      loadStudy();
    } finally {
      setSigning(false);
    }
  };

  if (authLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>;
  }

  if (loading) {
    return (
      <DashboardShell user={user} onLogout={logout}>
        <SkeletonDetail />
      </DashboardShell>
    );
  }

  if (!study) {
    return (
      <DashboardShell user={user} onLogout={logout}>
        <div className="rounded-lg border border-dashed p-12 text-center text-muted-foreground">
          <p>{pageError || "Study not found."}</p>
          <Button variant="outline" className="mt-4" onClick={() => router.push("/imaging")}>Back to Imaging</Button>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell
      user={user}
      onLogout={logout}
      breadcrumbs={[
        { label: "Imaging", href: "/imaging" },
        { label: `${study.patient_name} — ${study.body_part}` },
      ]}
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="ghost" size="icon" onClick={() => router.push("/imaging")}>
              <Icons.chevronDown className="h-5 w-5 rotate-90" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight">{study.patient_name}</h1>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge(study.modality, MODALITY_BADGE)}`}>
              {study.modality}
            </span>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge(study.status, STATUS_BADGE)}`}>
              {study.status.replace("_", " ")}
            </span>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge(study.priority, PRIORITY_BADGE)}`}>
              {study.priority}
            </span>
          </div>
        </div>

        {pageError && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{pageError}</div>}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Study Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Body Part</p>
                  <p className="font-medium">{study.body_part}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Protocol</p>
                  <p className="font-medium">{study.protocol || "—"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Ordered By</p>
                  <p className="font-medium">{study.ordered_by || "—"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Performed At</p>
                  <p className="font-medium">
                    {study.performed_at ? new Date(study.performed_at).toLocaleString() : "—"}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Reason</p>
                <p className="text-sm">{study.reason || "—"}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Report</CardTitle>
            </CardHeader>
            <CardContent>
              {study.report ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      study.report.status === "signed" ? "bg-green-100 text-green-800" :
                      study.report.status === "draft" ? "bg-gray-100 text-gray-800" :
                      "bg-amber-100 text-amber-800"
                    }`}>
                      {study.report.status}
                    </span>
                    {study.report.status === "draft" && (
                      <Button size="sm" onClick={handleSignReport} disabled={signing}>
                        {signing ? "Signing…" : "Sign Report"}
                      </Button>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Findings</p>
                    <p className="text-sm whitespace-pre-wrap">{study.report.findings || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Impression</p>
                    <p className="text-sm whitespace-pre-wrap">{study.report.impression || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Recommendations</p>
                    <p className="text-sm whitespace-pre-wrap">{study.report.recommendations || "—"}</p>
                  </div>
                  {study.report.created_by_name && (
                    <p className="text-xs text-muted-foreground">
                      By {study.report.created_by_name} on {new Date(study.report.created_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              ) : (
                <ReportForm onSubmit={handleCreateReport} loading={reportSubmitting} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardShell>
  );
}
