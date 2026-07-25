"use client";

import { Card, CardContent } from "@/components/ui/card";

interface StudySummary {
  id: string;
  patient_name: string;
  modality: string;
  body_part: string;
  status: string;
  priority: string;
  performed_at: string | null;
  report_status: string;
}

interface Props {
  study: StudySummary;
  onClick?: () => void;
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

const REPORT_STATUS_BADGE: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  draft: "bg-gray-100 text-gray-800",
  signed: "bg-green-100 text-green-800",
  amended: "bg-blue-100 text-blue-800",
};

function badge(label: string, map: Record<string, string>): string {
  return map[label] || "bg-gray-100 text-gray-800";
}

export function StudyCard({ study, onClick }: Props) {
  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent"
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium">{study.patient_name}</p>
            <p className="text-xs text-muted-foreground">{study.body_part}</p>
          </div>
          {study.performed_at && (
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {new Date(study.performed_at).toLocaleDateString()}
            </span>
          )}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge(study.modality, MODALITY_BADGE)}`}
          >
            {study.modality}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge(study.status, STATUS_BADGE)}`}
          >
            {study.status.replace("_", " ")}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge(study.priority, PRIORITY_BADGE)}`}
          >
            {study.priority}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${badge(study.report_status, REPORT_STATUS_BADGE)}`}
          >
            {study.report_status.replace("_", " ")}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
