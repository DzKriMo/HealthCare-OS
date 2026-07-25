import { z } from "zod";

// ── Patient validators ─────────────────────────────────────

export const patientDemographicsSchema = z.object({
  first_name: z.string().min(1, "First name is required").max(100),
  last_name: z.string().min(1, "Last name is required").max(100),
  date_of_birth: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be YYYY-MM-DD"),
  gender: z.enum(["male", "female", "other", "unknown"]),
  blood_type: z
    .enum(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
    .nullable(),
  marital_status: z.enum(["single", "married", "divorced", "widowed", "unknown"]),
  national_id: z.string().max(50).nullable(),
});

export const patientContactSchema = z.object({
  phone: z.string().min(5, "Phone is required").max(30),
  email: z.string().email("Invalid email").nullable(),
  address_line1: z.string().min(1, "Address is required").max(200),
  address_line2: z.string().max(200).nullable(),
  city: z.string().min(1, "City is required").max(100),
  state: z.string().max(100).nullable(),
  postal_code: z.string().max(20).nullable(),
  country: z.string().min(1, "Country is required").max(100),
});

export const patientCreateSchema = z.object({
  demographics: patientDemographicsSchema,
  contact: patientContactSchema,
});

// ── Appointment validators ─────────────────────────────────

export const appointmentCreateSchema = z.object({
  patient_id: z.string().uuid(),
  practitioner_id: z.string().uuid(),
  start_time: z.string().datetime(),
  end_time: z.string().datetime(),
  type: z.enum([
    "consultation",
    "follow_up",
    "procedure",
    "emergency",
    "checkup",
    "other",
  ]),
  notes: z.string().max(2000).nullable(),
  room: z.string().max(50).nullable(),
}).refine(
  (data) => new Date(data.end_time) > new Date(data.start_time),
  { message: "End time must be after start time", path: ["end_time"] },
);

// ── Billing validators ─────────────────────────────────────

export const invoiceLineItemSchema = z.object({
  billing_item_id: z.string().uuid(),
  description: z.string().max(500),
  quantity: z.number().positive("Quantity must be positive"),
  unit_price: z.string().regex(/^\d+(\.\d{1,2})?$/, "Invalid price format"),
  tax_rate: z.string().regex(/^\d+(\.\d{1,2})?$/, "Invalid tax rate"),
  discount_amount: z.string().regex(/^\d+(\.\d{1,2})?$/, "Invalid discount"),
});

export const invoiceCreateSchema = z.object({
  patient_id: z.string().uuid(),
  line_items: z.array(invoiceLineItemSchema).min(1, "At least one line item required"),
  due_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  notes: z.string().max(2000).nullable(),
});

// ── Auth validators ────────────────────────────────────────

export const loginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password is required"),
  tenant_slug: z.string().min(1, "Tenant is required"),
});

export const passwordResetRequestSchema = z.object({
  email: z.string().email("Invalid email"),
  tenant_slug: z.string().min(1, "Tenant is required"),
});

export const passwordResetConfirmSchema = z.object({
  token: z.string().min(1),
  new_password: z
    .string()
    .min(10, "Password must be at least 10 characters")
    .max(128),
});

// ── User validators ────────────────────────────────────────

export const userCreateSchema = z.object({
  email: z.string().email("Invalid email"),
  first_name: z.string().min(1).max(100),
  last_name: z.string().min(1).max(100),
  role_id: z.string().uuid(),
  department_ids: z.array(z.string().uuid()).optional(),
  practitioner_profile: z
    .object({
      license_number: z.string().max(100).optional(),
      specialty: z.string().max(100).optional(),
    })
    .optional(),
});

// ── Document validators ────────────────────────────────────

export const documentUploadSchema = z.object({
  patient_id: z.string().uuid(),
  encounter_id: z.string().uuid().nullable(),
  category: z.enum([
    "consent",
    "lab",
    "referral",
    "imaging",
    "prescription",
    "invoice",
    "report",
    "other",
  ]),
  tags: z.array(z.string().max(50)).max(20),
});

// Type inference
export type PatientCreateInput = z.infer<typeof patientCreateSchema>;
export type AppointmentCreateInput = z.infer<typeof appointmentCreateSchema>;
export type InvoiceCreateInput = z.infer<typeof invoiceCreateSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
export type UserCreateInput = z.infer<typeof userCreateSchema>;
export type DocumentUploadInput = z.infer<typeof documentUploadSchema>;
