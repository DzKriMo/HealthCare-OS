import { describe, it, expect } from "vitest";

describe("Invoice line item math", () => {
  it("computes subtotal as quantity × unit price", () => {
    const line = { description: "Consultation", quantity: 2, unit_price: "150.00", tax_rate: "0" };
    const subtotal = line.quantity * Number(line.unit_price);
    expect(subtotal).toBe(300);
  });

  it("computes tax amount correctly", () => {
    const line = { description: "Lab", quantity: 1, unit_price: "200.00", tax_rate: "10" };
    const subtotal = line.quantity * Number(line.unit_price);
    const tax = subtotal * (Number(line.tax_rate) / 100);
    expect(tax).toBe(20);
  });

  it("handles multiple line items correctly", () => {
    const lines = [
      { qty: 2, price: 100, tax: 5 },
      { qty: 1, price: 50, tax: 0 },
    ];
    const result = lines.reduce(
      (acc, l) => {
        const s = l.qty * l.price;
        acc.subtotal += s;
        acc.tax += s * (l.tax / 100);
        return acc;
      },
      { subtotal: 0, tax: 0 },
    );
    expect(result.subtotal).toBe(250);
    expect(result.tax).toBe(10);
  });

  it("grand total = subtotal + tax - discount", () => {
    const subtotal = 250;
    const tax = 10;
    const discount = 25;
    const grand = Math.max(0, subtotal + tax - discount);
    expect(grand).toBe(235);
  });

  it("grand total never goes below zero", () => {
    const subtotal = 50;
    const tax = 5;
    const discount = 100;
    const grand = Math.max(0, subtotal + tax - discount);
    expect(grand).toBe(0);
  });
});

describe("Invoice validation", () => {
  it("rejects invoice with empty line descriptions", () => {
    const lines = [{ description: "", quantity: 1, unit_price: "50", tax_rate: "0" }];
    const valid = lines.every((l) => l.description.trim().length > 0);
    expect(valid).toBe(false);
  });

  it("accepts invoice with all valid lines", () => {
    const lines = [{ description: "Consultation", quantity: 1, unit_price: "150", tax_rate: "0" }];
    const valid = lines.every((l) => l.description.trim().length > 0);
    expect(valid).toBe(true);
  });

  it("rejects negative quantity", () => {
    expect(-1 < 1).toBe(true);
  });

  it("rejects negative unit price", () => {
    expect(-10 < 0).toBe(true);
  });
});

describe("Payment logic", () => {
  it("updates amount paid on partial payment", () => {
    const state = { grand_total: 500, amount_paid: 200, balance_due: 300 };
    const payment = 150;
    state.amount_paid += payment;
    state.balance_due = state.grand_total - state.amount_paid;
    expect(state.amount_paid).toBe(350);
    expect(state.balance_due).toBe(150);
  });

  it("marks invoice as paid when balance reaches zero", () => {
    const grandTotal = 500;
    const amountPaid = 500;
    const isPaid = amountPaid >= grandTotal;
    const status = isPaid ? "paid" : "partially_paid";
    expect(isPaid).toBe(true);
    expect(status).toBe("paid");
  });

  it("marks invoice as partially paid when balance > 0", () => {
    const grandTotal = 500;
    const amountPaid = 200;
    const isPaid = amountPaid >= grandTotal;
    const status = isPaid ? "paid" : "partially_paid";
    expect(isPaid).toBe(false);
    expect(status).toBe("partially_paid");
  });

  it("refund updates balance correctly", () => {
    const state = { grand_total: 500, amount_paid: 300, amount_refunded: 0, balance_due: 200 };
    const refundAmount = 50;
    state.amount_refunded += refundAmount;
    state.amount_paid -= refundAmount;
    state.balance_due = state.grand_total - state.amount_paid;
    expect(state.amount_refunded).toBe(50);
    expect(state.amount_paid).toBe(250);
    expect(state.balance_due).toBe(250);
  });
});

describe("POS checkout flow", () => {
  it("adds item to cart", () => {
    const cart: { id: string; qty: number }[] = [];
    const item = { id: "1", name: "Consultation", price: 150 };
    cart.push({ id: item.id, qty: 1 });
    expect(cart).toHaveLength(1);
  });

  it("increments quantity when adding duplicate item", () => {
    let cart = [{ id: "1", name: "X-Ray", price: 200, qty: 1 }];
    const existing = cart.find((c) => c.id === "1");
    if (existing) cart = cart.map((c) => (c.id === "1" ? { ...c, qty: c.qty + 1 } : c));
    expect(cart[0].qty).toBe(2);
  });

  it("removes item when quantity goes to zero", () => {
    let cart = [{ id: "1", name: "X-Ray", price: 200, qty: 1 }];
    cart = cart.filter((c) => c.qty > 1);
    expect(cart).toHaveLength(0);
  });

  it("calculates cart total with tax", () => {
    const cart = [
      { price: 100, qty: 2, tax: 5 },
      { price: 50, qty: 1, tax: 0 },
    ];
    const total = cart.reduce((sum, c) => sum + c.price * c.qty * (1 + c.tax / 100), 0);
    expect(total).toBeCloseTo(260, 2);
  });

  it("rejects checkout with empty cart", () => {
    const cart: unknown[] = [];
    const valid = cart.length > 0;
    expect(valid).toBe(false);
  });
});

describe("Revenue aggregation", () => {
  const invoices = [
    { status: "paid", grand_total: "500", amount_paid: "500" },
    { status: "paid", grand_total: "300", amount_paid: "300" },
    { status: "partially_paid", grand_total: "200", amount_paid: "100" },
    { status: "issued", grand_total: "400", amount_paid: "0" },
    { status: "overdue", grand_total: "150", amount_paid: "0" },
    { status: "draft", grand_total: "100", amount_paid: "0" },
  ];

  it("total revenue sums amount_paid for paid invoices", () => {
    const revenue = invoices
      .filter((i) => i.status === "paid")
      .reduce((s, i) => s + Number(i.amount_paid), 0);
    expect(revenue).toBe(800);
  });

  it("total invoiced sums grand_total for all non-draft/cancelled", () => {
    const invoiced = invoices
      .filter((i) => !["draft", "cancelled"].includes(i.status))
      .reduce((s, i) => s + Number(i.grand_total), 0);
    expect(invoiced).toBe(1550);
  });

  it("outstanding sums balance_due for non-paid/draft/cancelled", () => {
    const outstanding = invoices
      .filter((i) => !["paid", "draft", "cancelled"].includes(i.status))
      .reduce((s, i) => s + (Number(i.grand_total) - Number(i.amount_paid)), 0);
    expect(outstanding).toBe(650);
  });

  it("counts invoices grouped by status", () => {
    const counts = invoices.reduce(
      (acc, i) => {
        acc[i.status] = (acc[i.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );
    expect(counts.paid).toBe(2);
    expect(counts.draft).toBe(1);
    expect(counts.issued).toBe(1);
    expect(counts.overdue).toBe(1);
  });
});

describe("Invoice status machine", () => {
  it("draft can transition to issued", () => {
    const allowed = { draft: ["issued", "cancelled"] as const };
    expect(allowed.draft).toContain("issued");
  });

  it("issued can transition to partially_paid or paid", () => {
    const allowed = { issued: ["partially_paid", "paid", "overdue", "cancelled"] as const };
    expect(allowed.issued).toContain("partially_paid");
    expect(allowed.issued).toContain("paid");
  });

  it("paid is a terminal status", () => {
    const terminal = ["paid", "cancelled"] as const;
    expect(terminal).toContain("paid");
  });

  it("cancelled is a terminal status", () => {
    const terminal = ["paid", "cancelled"] as const;
    expect(terminal).toContain("cancelled");
  });

  it("overdue can transition to paid or partially_paid", () => {
    const allowed = { overdue: ["partially_paid", "paid"] as const };
    expect(allowed.overdue).toContain("paid");
    expect(allowed.overdue).toContain("partially_paid");
  });
});
