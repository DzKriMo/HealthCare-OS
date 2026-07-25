"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface InvoiceSummary {
  id: string; invoice_number: string; status: string;
  grand_total: string; amount_paid: string; balance_due: string;
  due_date: string | null; created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700", issued: "bg-blue-100 text-blue-700",
  partially_paid: "bg-yellow-100 text-yellow-700", paid: "bg-green-100 text-green-700",
  overdue: "bg-red-100 text-red-700", cancelled: "bg-gray-100 text-gray-500",
};

interface Props { patientId: string; }

export function PatientBillingHistory({ patientId }: Props) {
  const router = useRouter();
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<{ results: InvoiceSummary[] }>(`/billing/invoices/?patient=${patientId}`);
        setInvoices(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  const money = (v: string | number) => Number(v || 0).toFixed(2);
  const totalBalance = invoices.reduce((s, i) => s + Number(i.balance_due || 0), 0);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Billing History</CardTitle>
          <p className="text-sm text-muted-foreground">{invoices.length} invoice{invoices.length !== 1 ? "s" : ""} · Balance: ${money(totalBalance)}</p>
        </div>
        <Button size="sm" onClick={() => router.push(`/billing/new?patient=${patientId}`)}>
          <Icons.plus className="mr-1 h-4 w-4" /> New Invoice
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {invoices.length === 0 ? (
          <p className="text-sm text-muted-foreground">No invoices for this patient.</p>
        ) : (
          invoices.map((inv) => (
            <div key={inv.id} className="flex items-center justify-between rounded-lg border p-3 cursor-pointer hover:bg-muted/50" onClick={() => router.push(`/billing/${inv.id}`)}>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{inv.invoice_number}</span>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUS_COLORS[inv.status] || ""}`}>
                    {inv.status.replace("_", " ")}
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {new Date(inv.created_at).toLocaleDateString()}
                  {inv.due_date && ` · Due: ${new Date(inv.due_date).toLocaleDateString()}`}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">${money(inv.grand_total)}</div>
                {Number(inv.balance_due) > 0 && <div className="text-xs text-red-600">${money(inv.balance_due)} due</div>}
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
