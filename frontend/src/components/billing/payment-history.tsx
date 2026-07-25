"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiRequestError } from "@/lib/api/client";

interface PaymentEntry {
  id: string; patient_name: string; amount: string;
  method: string; reference: string; payment_date: string;
  is_refund: boolean; refund_reason: string;
  recorded_by_name: string;
}

interface Props {
  patientId?: string;
}

export function PaymentHistory({ patientId }: Props) {
  const [payments, setPayments] = useState<PaymentEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const q = patientId ? `?patient=${patientId}` : "";
        const data = await api.get<{ results: PaymentEntry[] }>(`/billing/payments/${q}`);
        setPayments(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  if (loading) return <div className="h-20 animate-pulse rounded-lg bg-muted" />;

  if (payments.length === 0) return null;

  return (
    <Card>
      <CardHeader><CardTitle className="text-lg">Payment History</CardTitle></CardHeader>
      <CardContent className="space-y-2 text-sm">
        {payments.map((p) => (
          <div key={p.id} className={`flex items-center justify-between rounded-lg border p-3 ${p.is_refund ? "border-red-200 bg-red-50" : ""}`}>
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-medium">{p.is_refund ? "Refund" : p.method}</span>
                {p.reference && <span className="text-xs text-muted-foreground">#{p.reference}</span>}
              </div>
              <div className="text-xs text-muted-foreground">
                {new Date(p.payment_date).toLocaleDateString()}
                {p.recorded_by_name && ` · by ${p.recorded_by_name}`}
              </div>
              {p.is_refund && p.refund_reason && (
                <div className="text-xs text-red-600">{p.refund_reason}</div>
              )}
            </div>
            <span className={`font-semibold ${p.is_refund ? "text-red-600" : "text-green-600"}`}>
              {p.is_refund ? "-" : "+"}${Number(p.amount).toFixed(2)}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
