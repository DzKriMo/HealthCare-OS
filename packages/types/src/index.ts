// ── Tenant ──────────────────────────────────────────────────

export interface TenantBranding {
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  dark_mode: boolean;
  typography: "default" | "modern" | "classic";
  clinic_name: string;
  language: string;
  currency: string;
}

export interface TenantSettings {
  notification_channels: {
    email: boolean;
    sms: boolean;
    whatsapp: boolean;
    push: boolean;
  };
  appointment_reminder_hours: number[];
  billing_grace_period_days: number;
  timezone: string;
  date_format: "DD/MM/YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";
  prescription_footer: string;
  invoice_footer: string;
}

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  branding: TenantBranding;
  settings: TenantSettings;
  enabled_modules: string[];
  created_at: string;
  updated_at: string;
}

// ── Identity ───────────────────────────────────────────────

export type PermissionAction =
  | "read"
  | "write"
  | "write_demographics"
  | "write_assessment"
  | "refund"
  | "adjust_stock"
  | "view_finance"
  | "export"
  | "access";

export type PermissionResource =
  | "patients"
  | "appointments"
  | "records"
  | "billing"
  | "inventory"
  | "reports"
  | "modules"
  | "audit"
  | "documents"
  | "notifications";

export type PermissionString = `${PermissionResource}.${PermissionAction}`;

export interface Role {
  id: string;
  tenant_id: string;
  name: string;
  is_system_role: boolean;
  permissions: PermissionString[];
}

export type BaseRoleName =
  | "receptionist"
  | "doctor"
  | "nurse"
  | "lab_technician"
  | "radiologist"
  | "pharmacist"
  | "manager"
  | "admin"
  | "super_admin";

export interface User {
  id: string;
  tenant_id?: string;
  tenant?: string | null;
  tenant_slug: string | null;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: string | Role;
  role_name: string | null;
  mfa_enabled?: boolean;
  is_active: boolean;
  last_login?: string | null;
}

/** Flat permission as returned by /auth/permissions/. */
export interface Permission {
  id: string;
  codename: string;
  description: string;
  resource: string;
  action: string;
}

// ── Patients ───────────────────────────────────────────────

export type Gender = "male" | "female" | "other" | "unknown";
export type BloodType = "A+" | "A-" | "B+" | "B-" | "AB+" | "AB-" | "O+" | "O-";
export type MaritalStatus = "single" | "married" | "divorced" | "widowed" | "unknown";

export interface PatientDemographics {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  blood_type: BloodType | null;
  marital_status: MaritalStatus;
  national_id: string | null;
}

export interface PatientContact {
  phone: string;
  email: string | null;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string | null;
  postal_code: string | null;
  country: string;
}

export interface Patient {
  id: string;
  tenant_id?: string;
  display_id: string;
  full_name: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_birth: string;
  age?: number;
  gender: Gender;
  blood_type: BloodType | "" | null;
  marital_status?: MaritalStatus;
  national_id?: string | null;
  phone_primary: string;
  phone_secondary?: string;
  email?: string | null;
  address_line1?: string;
  city?: string;
  country?: string;
  is_active?: boolean;
  created_by?: string;
  // Legacy nested shape (kept optional for backward compat)
  demographics?: PatientDemographics;
  contact?: PatientContact;
  registration_date?: string;
}

export interface Allergy {
  id: string;
  patient_id: string;
  substance: string;
  reaction: string;
  severity: "mild" | "moderate" | "severe" | "life_threatening";
  onset_date: string | null;
  status: "active" | "resolved" | "unknown";
}

export interface InsurancePolicy {
  id: string;
  patient_id: string;
  provider: string;
  policy_number: string;
  coverage_type: string;
  effective_date: string;
  expiration_date: string | null;
  is_primary: boolean;
}

export interface EmergencyContact {
  id: string;
  patient_id: string;
  name: string;
  relationship: string;
  phone: string;
  email: string | null;
}

// ── Appointments ───────────────────────────────────────────

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "arrived"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export type AppointmentType =
  | "consultation"
  | "follow_up"
  | "procedure"
  | "emergency"
  | "checkup"
  | "other";

export interface Appointment {
  id: string;
  tenant_id: string;
  patient_id: string;
  patient_name: string;
  practitioner_id: string;
  practitioner_name: string;
  start_time: string;
  end_time: string;
  type: AppointmentType;
  status: AppointmentStatus;
  notes: string | null;
  room: string | null;
  color: string | null;
  is_recurring: boolean;
  recurrence_rule: string | null;
}

export interface CalendarSlot {
  start_time: string;
  end_time: string;
  practitioner_id: string;
  is_available: boolean;
}

// ── Billing ────────────────────────────────────────────────

export type InvoiceStatus =
  | "draft"
  | "issued"
  | "partially_paid"
  | "paid"
  | "overdue"
  | "cancelled";

export type PaymentMethod = "cash" | "card" | "transfer" | "insurance" | "other";

export interface BillingItem {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  price: string;
  tax_rate: string;
  category: string;
  accounting_code: string | null;
  is_active: boolean;
}

export interface InvoiceLineItem {
  billing_item_id: string;
  description: string;
  quantity: number;
  unit_price: string;
  tax_rate: string;
  discount_amount: string;
  total: string;
}

export interface Invoice {
  id: string;
  tenant_id: string;
  patient_id: string;
  patient_name: string;
  invoice_number: string;
  status: InvoiceStatus;
  line_items: InvoiceLineItem[];
  subtotal: string;
  tax_total: string;
  discount_total: string;
  grand_total: string;
  amount_paid: string;
  balance_due: string;
  issued_date: string;
  due_date: string;
  notes: string | null;
}

export interface Payment {
  id: string;
  tenant_id: string;
  invoice_id: string;
  amount: string;
  method: PaymentMethod;
  reference: string | null;
  payment_date: string;
  is_refund: boolean;
  refunded_payment_id: string | null;
}

// ── Documents ──────────────────────────────────────────────

export type DocumentCategory =
  | "consent"
  | "lab"
  | "referral"
  | "imaging"
  | "prescription"
  | "invoice"
  | "report"
  | "other";

export interface Document {
  id: string;
  tenant_id: string;
  patient_id: string;
  encounter_id: string | null;
  file_name: string;
  file_size: number;
  mime_type: string;
  category: DocumentCategory;
  tags: string[];
  uploaded_by: string;
  uploaded_at: string;
  download_url: string;
}

// ── Clinical ───────────────────────────────────────────────

export type RecordStatus =
  | "draft"
  | "in_progress"
  | "finalized"
  | "signed"
  | "amended"
  | "archived"
  | "voided";

export interface Encounter {
  id: string;
  tenant_id: string;
  patient_id: string;
  practitioner_id: string;
  appointment_id: string | null;
  status: RecordStatus;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  diagnoses: string[];
  prescriptions: string[];
  attachments: string[];
  created_at: string;
  updated_at: string;
  signed_at: string | null;
  signed_by: string | null;
}

// ── Audit ──────────────────────────────────────────────────

export interface AuditEvent {
  id: string;
  tenant_id: string;
  actor_id: string;
  actor_name: string;
  session_id: string | null;
  entity_type: string;
  entity_id: string;
  action: string;
  before_value: Record<string, unknown> | null;
  after_value: Record<string, unknown> | null;
  correlation_id: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

// ── Sync ───────────────────────────────────────────────────

export type SyncOperationType = "create" | "update" | "delete";
export type SyncStatus = "pending" | "syncing" | "synced" | "failed" | "conflict";

export interface SyncOperation {
  id: string;
  tenant_id: string;
  device_id: string;
  user_id: string;
  entity_type: string;
  entity_id: string;
  operation_type: SyncOperationType;
  payload: Record<string, unknown>;
  base_version: number;
  local_timestamp: string;
  dependencies: string[];
  status: SyncStatus;
  error: string | null;
  retry_count: number;
}

// ── Notifications ──────────────────────────────────────────

export type NotificationChannel = "email" | "sms" | "whatsapp" | "push";
export type NotificationEventType =
  | "appointment_scheduled"
  | "appointment_reminder"
  | "appointment_cancelled"
  | "missed_appointment"
  | "invoice_issued"
  | "payment_received"
  | "result_ready"
  | "follow_up_due"
  | "prescription_ready"
  | "stock_below_threshold";

export interface NotificationEvent {
  id: string;
  tenant_id: string;
  recipient_id: string;
  event_type: NotificationEventType;
  channel: NotificationChannel;
  template_id: string;
  status: "pending" | "sent" | "delivered" | "failed";
  sent_at: string | null;
  error: string | null;
}

// ── Module Registry ────────────────────────────────────────

export interface ModuleDefinition {
  name: string;
  version: string;
  display_name: string;
  description: string;
  permissions: { codename: string; description: string }[];
  appointment_types: Record<string, unknown>[];
  patient_tabs: { label: string; icon: string; permission: string }[];
  menu_items: { label: string; icon: string; path: string; permission: string }[];
  dashboard_widgets: Record<string, unknown>[];
  billing_item_types: Record<string, unknown>[];
}

// ── API ────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  error: {
    type: string;
    detail: unknown;
    correlation_id: string;
  };
}
