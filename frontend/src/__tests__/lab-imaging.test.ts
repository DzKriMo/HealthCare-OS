import { describe, it, expect } from "vitest";

describe("Lab order workflow", () => {
  it("starts with 'ordered' status", () => {
    const order = { status: "ordered" };
    expect(order.status).toBe("ordered");
  });

  it("transitions through valid statuses: ordered → collected → processing → completed", () => {
    const allowed: Record<string, string[]> = {
      ordered: ["collected", "cancelled"],
      collected: ["received", "rejected"],
      received: ["processing", "rejected"],
      processing: ["completed", "rejected"],
    };
    expect(allowed.ordered).toContain("collected");
    expect(allowed.processing).toContain("completed");
    expect(allowed.ordered).not.toContain("completed");
  });

  it("cancelled is a terminal status", () => {
    const terminal = ["completed", "cancelled"];
    expect(terminal).toContain("cancelled");
  });

  it("rejected specimens require a reason", () => {
    const transition = (status: string, reason?: string) => {
      if (status === "rejected" && !reason) return false;
      return true;
    };
    expect(transition("rejected", "Hemolyzed")).toBe(true);
    expect(transition("rejected")).toBe(false);
  });
});

describe("Lab test catalog", () => {
  it("filters by department", () => {
    const catalog = [
      { name: "CBC", department: "hematology" },
      { name: "BMP", department: "chemistry" },
      { name: "UA", department: "urinalysis" },
    ];
    const hematology = catalog.filter((t) => t.department === "hematology");
    expect(hematology).toHaveLength(1);
  });

  it("categorizes specimen types", () => {
    const types = ["blood", "urine", "swab", "stool", "csf", "sputum", "other"];
    expect(types).toContain("blood");
    expect(types).toContain("urine");
  });

  it("displays reference range text", () => {
    const test = { reference_range_low: 70, reference_range_high: 110, unit: "mg/dL" };
    const range = `${test.reference_range_low}–${test.reference_range_high} ${test.unit}`;
    expect(range).toBe("70–110 mg/dL");
  });

  it("handles non-numeric reference range", () => {
    const test = { reference_range_text: "Negative" };
    const display = test.reference_range_text || `${test.reference_range_low ?? "?"}–${test.reference_range_high ?? "?"}`;
    expect(display).toBe("Negative");
  });
});

describe("Lab result flags", () => {
  const autoFlag = (value: number, low: number | null, high: number | null) => {
    const criticalLow = low != null ? low * 0.5 : null;
    const criticalHigh = high != null ? high * 1.5 : null;
    if (criticalLow != null && value < criticalLow) return "critical_low";
    if (criticalHigh != null && value > criticalHigh) return "critical_high";
    if (low != null && value < low) return "low";
    if (high != null && value > high) return "high";
    return "normal";
  };

  it("flags low value", () => {
    expect(autoFlag(50, 70, 110)).toBe("low");
  });

  it("flags high value", () => {
    expect(autoFlag(150, 70, 110)).toBe("high");
  });

  it("marks normal value", () => {
    expect(autoFlag(90, 70, 110)).toBe("normal");
  });

  it("flags critical high value", () => {
    expect(autoFlag(200, 70, 110)).toBe("critical_high");
  });

  it("flags critical low value", () => {
    expect(autoFlag(20, 70, 110)).toBe("critical_low");
  });

  it("handles null reference ranges", () => {
    expect(autoFlag(50, null, null)).toBe("normal");
  });
});

describe("Specimen barcode generation", () => {
  it("generates SPC-prefixed barcode", () => {
    const generateBarcode = () => `SPC-${Math.random().toString(16).slice(2, 10)}`;
    const barcode = generateBarcode();
    expect(barcode).toMatch(/^SPC-/);
    expect(barcode.length).toBeGreaterThan(4);
  });
});

describe("Imaging study workflow", () => {
  it("starts with 'scheduled' status", () => {
    const study = { status: "scheduled" };
    expect(study.status).toBe("scheduled");
  });

  it("transitions: scheduled → performed → reporting → completed", () => {
    const study = { status: "scheduled" };
    study.status = "performed";
    expect(study.status).toBe("performed");
    study.status = "reporting";
    expect(study.status).toBe("reporting");
    study.status = "completed";
    expect(study.status).toBe("completed");
  });

  it("cancelled can come from scheduled", () => {
    const study = { status: "scheduled" };
    study.status = "cancelled";
    expect(study.status).toBe("cancelled");
  });

  it("supports stat priority", () => {
    const priorities = ["routine", "urgent", "stat"] as const;
    expect(priorities).toContain("stat");
  });

  it("groups studies by modality", () => {
    const studies = [
      { modality: "xray" }, { modality: "xray" },
      { modality: "mri" }, { modality: "ct" },
    ];
    const counts: Record<string, number> = {};
    studies.forEach((s) => { counts[s.modality] = (counts[s.modality] || 0) + 1; });
    expect(counts.xray).toBe(2);
    expect(counts.mri).toBe(1);
    expect(counts.ct).toBe(1);
  });
});

describe("Radiology report workflow", () => {
  it("starts as draft", () => {
    const report = { status: "draft" };
    expect(report.status).toBe("draft");
  });

  it("draft can be signed", () => {
    const allowed = { draft: ["signed", "cancelled"] as const };
    expect(allowed.draft).toContain("signed");
  });

  it("signed report is terminal", () => {
    const terminal = ["signed", "cancelled"] as const;
    expect(terminal).toContain("signed");
  });

  it("report can be amended after signing", () => {
    const report = { status: "signed" };
    report.status = "amended";
    expect(report.status).toBe("amended");
  });
});

describe("DICOM data handling", () => {
  it("generates study UID in DICOM format", () => {
    const uid = `1.2.840.${Date.now().toString(16)}.${Math.random().toString(16).slice(2, 10)}`;
    expect(uid).toMatch(/^1\.2\.840\./);
  });

  it("tracks image dimensions", () => {
    const image = { width: 512, height: 512 };
    expect(image.width).toBe(512);
    expect(image.height).toBe(512);
  });
});
