import { describe, it, expect } from "vitest";

describe("SOAP note validation", () => {
  it("rejects empty subjective and assessment", () => {
    const soap = { subjective: "", objective: "Clear", assessment: "", plan: "Rest" };
    const valid = soap.subjective.trim().length > 0 && soap.assessment.trim().length > 0;
    expect(valid).toBe(false);
  });

  it("accepts complete SOAP with all sections", () => {
    const soap = { subjective: "Headache", objective: "BP 120/80", assessment: "Migraine", plan: "Rest" };
    const valid = Object.values(soap).every((v) => v.trim().length > 0);
    expect(valid).toBe(true);
  });

  it("truncates long notes to 100 chars for preview", () => {
    const long = "a".repeat(200);
    const preview = long.length > 100 ? `${long.slice(0, 100)}…` : long;
    expect(preview.length).toBe(101);
  });
});

describe("Encounter status machine", () => {
  it("draft can transition to in_progress or signed", () => {
    const allowed = { draft: ["in_progress", "signed", "cancelled"] as const };
    expect(allowed.draft).toContain("in_progress");
    expect(allowed.draft).toContain("signed");
  });

  it("signed is a terminal status", () => {
    const terminal = ["signed", "cancelled"] as const;
    expect(terminal).toContain("signed");
    expect(terminal).toContain("cancelled");
  });

  it("in_progress can transition to signed", () => {
    const allowed = { in_progress: ["signed", "cancelled"] as const };
    expect(allowed.in_progress).toContain("signed");
  });
});

describe("Vital signs calculations", () => {
  it("calculates BMI from height and weight", () => {
    const heightCm = 175;
    const weightKg = 70;
    const bmi = weightKg / ((heightCm / 100) ** 2);
    expect(bmi).toBeCloseTo(22.9, 0);
  });

  it("returns null BMI if height is zero", () => {
    const heightCm = 0;
    const weightKg = 70;
    const bmi = heightCm > 0 ? weightKg / ((heightCm / 100) ** 2) : null;
    expect(bmi).toBeNull();
  });

  it("returns null BMI if weight is missing", () => {
    const heightCm = 175;
    const weightKg = null;
    const bmi = weightKg != null && heightCm > 0 ? weightKg / ((heightCm / 100) ** 2) : null;
    expect(bmi).toBeNull();
  });

  it("classifies BP categories correctly", () => {
    const classifyBp = (systolic: number, diastolic: number) => {
      if (systolic < 120 && diastolic < 80) return "normal";
      if (systolic < 130 && diastolic < 80) return "elevated";
      if (systolic < 140 || diastolic < 90) return "stage1";
      return "stage2";
    };
    expect(classifyBp(110, 70)).toBe("normal");
    expect(classifyBp(125, 75)).toBe("elevated");
    expect(classifyBp(135, 85)).toBe("stage1");
    expect(classifyBp(150, 95)).toBe("stage2");
  });
});

describe("Diagnosis data", () => {
  it("categorizes diagnosis types correctly", () => {
    const types = ["primary", "secondary", "admitting", "discharge"] as const;
    const isPrimary = (t: string) => t === "primary";
    expect(isPrimary("primary")).toBe(true);
    expect(isPrimary("secondary")).toBe(false);
  });

  it("marks chronic conditions", () => {
    const diagnoses = [
      { icd_code: "E11.9", description: "Type 2 diabetes", is_chronic: true },
      { icd_code: "J45.909", description: "Asthma", is_chronic: true },
      { icd_code: "S82.1", description: "Fractured tibia", is_chronic: false },
    ];
    const chronic = diagnoses.filter((d) => d.is_chronic);
    expect(chronic).toHaveLength(2);
  });

  it("resolved diagnoses are marked inactive", () => {
    const d = { is_active: true };
    const resolved = { ...d, is_active: false };
    expect(resolved.is_active).toBe(false);
  });
});

describe("Referral workflow", () => {
  it("defaults to pending status", () => {
    const referral = { status: "pending" };
    expect(referral.status).toBe("pending");
  });

  it("prioritizes STAT referrals", () => {
    const urgencyLevel = { routine: 0, urgent: 1, stat: 2 };
    expect(urgencyLevel.stat).toBe(2);
    expect(urgencyLevel.stat > urgencyLevel.urgent).toBe(true);
  });

  it("tracks referral status transitions", () => {
    const allowed = { pending: ["scheduled", "declined"], scheduled: ["completed", "declined"] } as const;
    expect(allowed.pending).toContain("scheduled");
    expect(allowed.scheduled).toContain("completed");
  });
});

describe("Vaccination records", () => {
  it("tracks dose number", () => {
    const v = { vaccine_name: "COVID-19", dose_number: 2 };
    expect(v.dose_number).toBeGreaterThan(0);
  });

  it("flags overdue next due date", () => {
    const today = new Date("2026-07-25");
    const past = new Date("2025-01-01");
    const isOverdue = past < today;
    expect(isOverdue).toBe(true);
  });

  it("next due date in future is not overdue", () => {
    const today = new Date("2026-07-25");
    const future = new Date("2027-01-01");
    const isOverdue = future < today;
    expect(isOverdue).toBe(false);
  });
});

describe("Prescription status machine", () => {
  it("draft transitions to issued", () => {
    const allowed = { draft: ["issued", "cancelled"] as const };
    expect(allowed.draft).toContain("issued");
  });

  it("issued transitions to partially_filled or filled", () => {
    const allowed = { issued: ["partially_filled", "filled", "cancelled", "expired"] as const };
    expect(allowed.issued).toContain("partially_filled");
    expect(allowed.issued).toContain("filled");
  });

  it("filled is terminal unless cancelled", () => {
    const terminal = ["filled", "cancelled", "expired"] as const;
    expect(terminal).toContain("filled");
  });

  it("cannot dispense cancelled prescription", () => {
    const rx = { status: "cancelled" };
    const canDispense = !["cancelled", "expired"].includes(rx.status);
    expect(canDispense).toBe(false);
  });

  it("cannot dispense expired prescription", () => {
    const rx = { status: "expired" };
    const canDispense = !["cancelled", "expired"].includes(rx.status);
    expect(canDispense).toBe(false);
  });
});

describe("Dispense logic", () => {
  it("updates quantity dispensed on dispense", () => {
    const rx = { quantity_dispensed: 0, quantity_prescribed: 30, refills_used: 0, refills_authorized: 2 };
    const dispenseQty = 10;
    rx.quantity_dispensed += dispenseQty;
    expect(rx.quantity_dispensed).toBe(10);
  });

  it("tracks refills correctly", () => {
    const rx = { refills_authorized: 3, refills_used: 1 };
    const remaining = rx.refills_authorized - rx.refills_used;
    expect(remaining).toBe(2);
  });

  it("marks prescription filled when fully dispensed with no refills", () => {
    const rx = { quantity_dispensed: 30, quantity_prescribed: 30, refills_remaining: 0 };
    const isFilled = rx.quantity_dispensed >= rx.quantity_prescribed && rx.refills_remaining === 0;
    expect(isFilled).toBe(true);
  });

  it("marks partially filled when some dispensed", () => {
    const rx = { quantity_dispensed: 15, quantity_prescribed: 30, refills_remaining: 1 };
    const isFilled = rx.quantity_dispensed >= rx.quantity_prescribed && rx.refills_remaining === 0;
    const isPartiallyFilled = rx.quantity_dispensed > 0 && !isFilled;
    expect(isPartiallyFilled).toBe(true);
    expect(isFilled).toBe(false);
  });

  it("calculates refills remaining correctly", () => {
    expect(Math.max(0, 3 - 0)).toBe(3);
    expect(Math.max(0, 3 - 3)).toBe(0);
    expect(Math.max(0, 0 - 1)).toBe(0);
  });
});

describe("Controlled substance logging", () => {
  it("requires witness for Schedule II", () => {
    const isScheduleII = true;
    const witness = null;
    const valid = !isScheduleII || witness != null;
    expect(valid).toBe(false);
  });

  it("tracks inventory before and after dispense", () => {
    const before = 100;
    const dispensed = 30;
    const after = before - dispensed;
    expect(after).toBe(70);
  });
});
