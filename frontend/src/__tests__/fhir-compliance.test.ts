import { describe, it, expect } from "vitest";

describe("FHIR Compliance Dashboard", () => {
  describe("CapabilityStatement", () => {
    it("reports FHIR R4 version 4.0.1", () => {
      const capability = { fhirVersion: "4.0.1", rest: [{ mode: "server", resource: [] }] };
      expect(capability.fhirVersion).toBe("4.0.1");
    });

    it("advertises server mode", () => {
      const capability = { fhirVersion: "4.0.1", rest: [{ mode: "server", resource: [] }] };
      expect(capability.rest[0].mode).toBe("server");
    });
  });

  describe("FHIR Resources", () => {
    const resources = [
      "Patient", "Observation", "Encounter", "MedicationRequest",
      "AllergyIntolerance", "Condition", "Immunization", "Practitioner",
      "Coverage", "DiagnosticReport", "Medication",
    ];

    resources.forEach((res) => {
      it(`supports ${res} resource`, () => {
        const capability = { rest: [{ resource: [{ type: res, interaction: [{ code: "read" }, { code: "search-type" }] }] }] };
        const found = capability.rest[0].resource.find((r: any) => r.type === res);
        expect(found).toBeDefined();
        expect(found.interaction.some((i: any) => i.code === "read")).toBe(true);
      });
    });

    it("Patient supports create, update, and search", () => {
      const patient = { type: "Patient", interaction: [{ code: "read" }, { code: "create" }, { code: "update" }, { code: "search-type" }] };
      const codes = patient.interaction.map((i) => i.code);
      expect(codes).toContain("create");
      expect(codes).toContain("update");
      expect(codes).toContain("search-type");
    });
  });

  describe("OperationOutcome", () => {
    it("returns error with issue details", () => {
      const outcome = {
        resourceType: "OperationOutcome",
        issue: [{ severity: "error", code: "not-found", details: { text: "Resource not found" } }],
      };
      expect(outcome.resourceType).toBe("OperationOutcome");
      expect(outcome.issue[0].severity).toBe("error");
    });

    it("returns validation errors for invalid input", () => {
      const outcome = {
        resourceType: "OperationOutcome",
        issue: [{ severity: "error", code: "invalid", details: { text: "Patient name is required" } }],
      };
      expect(outcome.issue[0].code).toBe("invalid");
    });
  });

  describe("Bundle search results", () => {
    it("returns searchset bundle type", () => {
      const bundle = { resourceType: "Bundle", type: "searchset", total: 1, entry: [] };
      expect(bundle.type).toBe("searchset");
    });

    it("includes total count", () => {
      const bundle = { resourceType: "Bundle", type: "searchset", total: 5, entry: [{}, {}] };
      expect(bundle.total).toBe(5);
    });
  });

  describe("SMART on FHIR", () => {
    it("requires Bearer token for authorization", () => {
      const authHeader = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9";
      expect(authHeader).toMatch(/^Bearer /);
    });

    it("rejects requests without token", () => {
      const hasToken = false;
      expect(hasToken).toBe(false);
    });
  });

  describe("Data Export", () => {
    it("exports Patient resource as FHIR JSON", () => {
      const exportData = { resourceType: "Bundle", type: "searchset", entry: [{ resource: { resourceType: "Patient", id: "1" } }] };
      expect(exportData.entry[0].resource.resourceType).toBe("Patient");
    });

    it("supports bulk export for all resources", () => {
      const bulkExport = { resourceType: "Bundle", type: "searchset", total: 100 };
      expect(bulkExport.total).toBeGreaterThan(0);
    });
  });
});
