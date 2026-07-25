"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface LabOrder {
  id: string;
  patient_name: string;
  patient_id: string;
  status: string;
  priority: string;
  test_names: string[];
  ordered_at: string;
  ordered_by_name?: string;
  encounter?: string;
  notes?: string;
}

interface Props {
  order: LabOrder;
  onClick: () => void;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  ordered: "bg-blue-100 text-blue-700",
  collected: "bg-yellow-100 text-yellow-700",
  received: "bg-purple-100 text-purple-700",
  in_progress: "bg-indigo-100 text-indigo-700",
  completed: "bg-green-100 text-green-700",
  reviewed: "bg-teal-100 text-teal-700",
  cancelled: "bg-red-100 text-red-700",
};

const PRIORITY_STYLES: Record<string, string> = {
  routine: "border-gray-300 text-gray-600",
  urgent: "border-amber-300 text-amber-700 bg-amber-50",
  stat: "border-red-300 text-red-700 bg-red-50",
};

export function LabOrderCard({ order, onClick }: Props) {
  const statusStyle = STATUS_STYLES[order.status] || "bg-gray-100 text-gray-700";
  const priorityStyle = PRIORITY_STYLES[order.priority] || PRIORITY_STYLES.routine;

  return (
    <Card className="cursor-pointer transition-colors hover:border-primary" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate font-medium">{order.patient_name}</span>
              <span
                className={cn(
                  "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase",
                  priorityStyle,
                )}
              >
                {order.priority}
              </span>
              <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", statusStyle)}>
                {order.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-1 truncate text-sm text-muted-foreground">
              {order.test_names?.join(", ") || "No tests"}
            </p>
            <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
              <span>{new Date(order.ordered_at).toLocaleDateString()}</span>
              {order.ordered_by_name && (
                <span>Ordered by {order.ordered_by_name}</span>
              )}
            </div>
            {order.notes && (
              <p className="mt-1 truncate text-xs text-muted-foreground">{order.notes}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
