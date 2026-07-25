"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Prescription {
  id: string | number;
  patient_name: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  status: string;
  prescribed_by_name: string;
  is_controlled: boolean;
  controlled_schedule?: string;
  issued_date: string;
}

interface PrescriptionCardProps {
  prescription: Prescription;
  onClick: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  issued: "bg-blue-100 text-blue-700",
  partially_filled: "bg-yellow-100 text-yellow-700",
  filled: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
  expired: "bg-orange-100 text-orange-700",
};

export function PrescriptionCard({ prescription, onClick }: PrescriptionCardProps) {
  const statusClass = STATUS_COLORS[prescription.status] || "bg-gray-100 text-gray-700";

  return (
    <Card className="cursor-pointer transition-colors hover:border-primary" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-medium">{prescription.drug_name}</span>
              <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", statusClass)}>
                {prescription.status.replace(/_/g, " ")}
              </span>
              {prescription.is_controlled && (
                <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                  C-II{prescription.controlled_schedule ? `-${prescription.controlled_schedule}` : ""}
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {prescription.dosage} &middot; {prescription.frequency}
            </p>
            <p className="truncate text-sm text-muted-foreground">{prescription.patient_name}</p>
            <p className="text-xs text-muted-foreground">
              Rx by {prescription.prescribed_by_name} &middot;{" "}
              {new Date(prescription.issued_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
