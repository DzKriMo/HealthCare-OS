# Healthcare OS — Sprint Development Plan

> Based on [healthcare_os_blueprint.md](./healthcare_os_blueprint.md). MVP scope: Core platform + Dental module + Electron offline app + API foundation.

---

## Sprint Cadence

- **Sprint length**: 2 weeks
- **Total sprints**: 10 (20 weeks to MVP)
- **Team assumption**: 3-5 full-stack engineers, 1 designer, 1 PM
- **Ceremonies**: Sprint planning (Day 1), daily standup, sprint review + retro (last day)

---

## Sprint 0 — Project Foundation & Infrastructure

**Goal**: Every developer can run the full stack locally with one command. CI runs on every push.

### Tasks

| # | Task | Details |
|---|------|---------|
| 0.1 | Monorepo setup | Single repo with `backend/`, `frontend/`, `desktop/`, `docs/`, `infra/`. Turborepo or Nx for task orchestration. |
| 0.2 | Django project scaffold | `healthcare_os` project, Django 5.x, DRF, split into apps per bounded context: `identity`, `tenancy`, `patients`, `scheduling`, `billing`, `documents`, `notifications`, `reporting`, `audit`, `modules`, `sync`. |
| 0.3 | Next.js project scaffold | App Router, TypeScript strict, TailwindCSS, shadcn/ui initialized, folder structure per feature. |
| 0.4 | Docker Compose dev environment | PostgreSQL 16, Redis, MinIO, Django, Next.js, Nginx — all wired with hot reload. Single `docker compose up`. |
| 0.5 | Shared TypeScript types package | Extract shared types (tenant, user, patient, appointment, billing) into `packages/types`. |
| 0.6 | Shared Zod validation schemas | Reuse validation rules across frontend forms and backend serializers via `packages/validators`. |
| 0.7 | CI pipeline (GitHub Actions) | Lint (Ruff, ESLint, Prettier), type-check (mypy, tsc), test (pytest, vitest) on every PR. |
| 0.8 | Pre-commit hooks | Ruff, ESLint, Prettier, secrets detection (detect-secrets or gitleaks), migration safety check. |
| 0.9 | Database migration baseline | Initial Django migrations, SQLite schema versioning strategy for desktop, migration CI step. |
| 0.10 | Environment config | `.env.example`, settings split (base/dev/staging/prod), secrets via environment variables, never committed. |
| 0.11 | Design system foundation | shadcn/ui theme tokens mapped to white-label design tokens (colors, typography, spacing, radii). Dark mode toggle. |

### Deliverables
- [x] Repo is initialized and CI is green
- [x] `docker compose up` brings up the full stack
- [x] Django admin is accessible
- [x] Next.js renders the shell with shadcn/ui components
- [x] Linting and type-checking pass with zero errors

---

## Sprint 1 — Identity, Tenancy & RBAC

**Goal**: Users can log in, tenants are isolated, roles and permissions gate every action.

### Tasks

| # | Task | Details |
|---|------|---------|
| 1.1 | Custom user model | Extend `AbstractBaseUser` with tenant FK, role FK, practitioner profile, MFA flag. Email or username login. |
| 1.2 | Tenant model & middleware | `Tenant` model with slug, name, branding JSON, enabled modules JSON, settings JSON. Tenant-aware request middleware that sets `request.tenant` from subdomain or header. |
| 1.3 | Tenant isolation guards | Base queryset/manager that automatically scopes by `request.tenant`. Tenant-mismatch detection in every view. |
| 1.4 | Role and permission models | `Role` (name, tenant, is_system_role) with M2M to `Permission`. Permission format: `resource.action` (e.g., `patients.read`, `billing.refund`). |
| 1.5 | Permission enforcement | DRF permission class that checks `request.user` permissions against required permission string. Decorator for function views. |
| 1.6 | JWT auth endpoints | Login (returns access + refresh tokens), logout (blacklist refresh), token refresh. SimpleJWT configured with short-lived access (15 min) and rotating refresh tokens. |
| 1.7 | 2FA foundation | TOTP-based 2FA model, enable/disable endpoint, verification step in login flow. Optional per-role enforcement. |
| 1.8 | Session & device management | Track active sessions, show user their sessions, allow revocation. Device fingerprint basics. |
| 1.9 | Auth frontend | Login page, 2FA challenge, password reset flow, session list. Tenant-resolved branding on login screen. |
| 1.10 | Role & permission admin UI | Admin panel for creating/editing roles, assigning permissions, assigning users to roles. Role templates (pre-built sets for Receptionist, Doctor, Admin, etc.). |
| 1.11 | Tenant provisioning flow | Admin-only: create tenant, assign admin user, configure branding basics, enable modules. Tenant onboarding wizard step 1. |
| 1.12 | Tests | Auth flow tests (login, refresh, revoke), permission enforcement tests (access denied for missing permission), tenant isolation tests (cannot see another tenant's data). |

### Deliverables
- [x] Login with JWT, token refresh, logout
- [x] Tenants are fully isolated — zero cross-tenant data leaks
- [x] RBAC gates every API endpoint
- [x] Tenant admin can create roles and assign permissions

---

## Sprint 2 — Patient Master Data

**Goal**: Full patient CRUD with demographics, medical history, insurance, emergency contacts. Tenant-scoped and permission-gated.

### Tasks

| # | Task | Details |
|---|------|---------|
| 2.1 | Patient model | UUID PK, tenant FK, demographics (name, DOB, gender, blood type, marital status), contact info, national ID / SSN (encrypted at rest), created_at, updated_at, created_by. |
| 2.2 | Patient list & search API | Paginated list, search by name/phone/ID/email, tenant-scoped. PostgreSQL `tsvector` for full-text search. Filter by status, registration date range. |
| 2.3 | Patient CRUD API | Create, read, update, delete (soft delete → archive). Permission-gated: `patients.read`, `patients.write_demographics`. |
| 2.4 | Medical history model | Chronic conditions, past surgeries, family history, social history (smoking, alcohol). Versioned — edits create new versions, not overwrites. |
| 2.5 | Allergy & medication list | Allergy model (substance, reaction, severity, onset, status). Current medications (drug, dose, frequency, start date, prescribed by). |
| 2.6 | Insurance model | Insurance provider, policy number, coverage type, effective dates, primary/secondary. M2M to patient. |
| 2.7 | Emergency contacts | Name, relationship, phone, email, address. Multiple per patient. |
| 2.8 | Patient timeline API | Unified chronological feed of all events for a patient: appointments, encounters, invoices, lab results, documents, notes. |
| 2.9 | Patient frontend | Patient list page with search, filters, quick actions. Patient detail with tabbed layout (demographics, history, insurance, documents, timeline). Registration form with validation. |
| 2.10 | Consent management | Consent model (patient FK, consent type, form version, status: granted/withdrawn/expired, timestamp, IP, device). Consent check middleware for data access. |
| 2.11 | Tests | Patient CRUD, search accuracy, tenant isolation, medical history versioning, consent enforcement. |

### Deliverables
- [x] Full patient registration and profile management
- [x] Search works across name, phone, ID
- [x] Medical history with versioning
- [x] Insurance and emergency contacts
- [x] Consent records are tracked and enforced

---

## Sprint 3 — Appointments & Scheduling

**Goal**: Calendar-driven appointment management with recurring appointments, provider scheduling, waiting list, and queue board.

### Tasks

| # | Task | Details |
|---|------|---------|
| 3.1 | Appointment model | UUID PK, tenant FK, patient FK, practitioner FK, start/end datetime, type (consultation, follow-up, procedure, etc.), status (scheduled/confirmed/arrived/in_progress/completed/cancelled/no_show), notes, room, color. |
| 3.2 | Practitioner schedule model | Availability slots per practitioner per day, breaks, room assignments, max concurrent appointments. |
| 3.3 | Appointment CRUD API | Create, update, reschedule, cancel (with reason), status transitions. Conflict detection. Permission-gated. |
| 3.4 | Calendar views API | Daily, weekly, monthly aggregated views. Practitioner filter, room filter, status filter. Optimized queries for calendar rendering. |
| 3.5 | Recurring appointments | RRULE-based recurrence rules. Generate instances for a date range. Edit single instance vs edit series. Exception tracking. |
| 3.6 | Waiting list | Patient can be added to waiting list with preferred date range, practitioner preference, priority. Auto-suggest when slot opens. |
| 3.7 | Check-in workflow | Arrival check-in (reception), practitioner check-in (start encounter), completion, no-show marking. Status machine enforced. |
| 3.8 | Online booking API | Public endpoint for available slots, book appointment (rate-limited, CAPTCHA-protected). Confirmation via notification. |
| 3.9 | Queue board API | Real-time view of today's appointments grouped by practitioner/room, with status indicators. WebSocket updates via Django Channels. |
| 3.10 | Calendar frontend | FullCalendar or custom calendar with day/week/month views. Drag-to-reschedule. Click to create/edit. Color coding by status/type. Practitioner and room filters. |
| 3.11 | Queue board frontend | Live-updating board showing today's patients, status badges, wait times, next-up indicators. Designed for a wall-mounted display. |
| 3.12 | Appointment reminder rules | Configurable reminder schedule (24h before, 1h before) per tenant. Background job to trigger notifications. |
| 3.13 | Tests | Appointment CRUD, conflict detection, recurrence expansion, status transitions, tenant isolation, practitioner schedule constraints. |

### Deliverables
- [x] Full-featured calendar with day/week/month views
- [x] Appointment booking with conflict detection
- [x] Recurring appointments
- [x] Queue board with live updates
- [x] Online booking public page (basic)

---

## Sprint 4 — Billing & Payments

**Goal**: End-to-end billing workflow from quote to invoice to payment, with tax, discount, and insurance claim support.

### Tasks

| # | Task | Details |
|---|------|---------|
| 4.1 | Billing item catalog | Service items, product items, package items. Price, tax rate, category, accounting code. Tenant-scoped. |
| 4.2 | Quote model & workflow | Quote → accept → convert to invoice. Line items, totals, taxes, expiration. PDF generation. |
| 4.3 | Invoice model & workflow | Draft → issued → partially paid → paid → overdue → cancelled. Line items, tax calculation, discount application, notes. Invoice number sequence per tenant. |
| 4.4 | Payment model | Payment against invoice(s), amount, method (cash/card/transfer/insurance), reference, timestamp. Refund support with original payment link. |
| 4.5 | POS checkout flow | Quick sale: select items → apply discount → select payment method → record payment → print receipt. For reception desk walk-in payments. |
| 4.6 | Insurance claim basics | Claim model (invoice FK, insurance policy FK, status, submitted date, response). Basic claim status tracking. Full EDI integration deferred to Phase 2. |
| 4.7 | Tax engine | Tax rate per item category, compound tax support, tax-exempt patient flag. Tax summary report. |
| 4.8 | Revenue dashboard API | Daily/weekly/monthly revenue, by practitioner, by service category, by payment method. Collections vs outstanding. |
| 4.9 | Billing frontend | Quote builder, invoice list with status filters, payment recording modal, POS checkout screen. Patient billing history tab. |
| 4.10 | Invoice PDF template | Tenant-branded PDF with logo, colors, line items, tax breakdown, payment instructions. |
| 4.11 | Tests | Invoice calculation accuracy (including edge cases: multi-tax, discount before/after tax), payment allocation, refund workflow, tenant isolation. |

### Deliverables
- [x] Quote → invoice → payment workflow
- [x] POS quick checkout
- [x] Tenant-branded invoice PDFs
- [x] Revenue dashboard (basic)
- [x] Billing calculations are correct to the cent

---

## Sprint 5 — Files, Documents & Notifications

**Goal**: File upload/storage with tenant-aware object paths, notification orchestration across channels.

### Tasks

| # | Task | Details |
|---|------|---------|
| 5.1 | File upload API | Chunked upload support for large files (>10MB). MIME type validation, file size limits per tenant config. Virus scanning hook (ClamAV or SaaS antivirus API). |
| 5.2 | Object storage integration | MinIO/S3 client, tenant-aware bucket/prefix: `{tenant_slug}/patients/{uuid}/documents/`. Signed URL generation for secure access (expiring, scope-limited). |
| 5.3 | Document model | File reference, category (consent/lab/referral/imaging/prescription/other), patient FK, encounter FK, tags, uploader, version tracking. |
| 5.4 | File metadata extraction | Async job: extract EXIF, page count (PDF), duration (audio), dimensions (image). Store in searchable metadata JSON. |
| 5.5 | File categorization | Auto-categorize based on upload context + manual override. Filter by category in patient document view. |
| 5.6 | Signature capture | Signature pad integration (web canvas), store as SVG + timestamp + metadata. Attach to encounters, consents, invoices. |
| 5.7 | Notification event model | Event type enum (appointment_reminder, payment_due, result_ready, etc.), template FK, recipient, channel, status, sent_at, error. |
| 5.8 | Notification template engine | Template model with Jinja2/Django template variables. Per-tenant override. Multi-language template support. HTML + plain text. |
| 5.9 | Channel backends | Email (SMTP/SES), SMS (Twilio or generic HTTP gateway), WhatsApp (WhatsApp Business API), push notification (FCM/APNs stub). Abstract channel interface so new channels are pluggable. |
| 5.10 | Notification orchestration | Event → resolve tenant preferences → select channel → render template → dispatch → log result. Retry with exponential backoff. |
| 5.11 | File manager frontend | Patient document gallery with thumbnails (image/PDF preview), upload with drag-and-drop, category filter, signed URL download. |
| 5.12 | Notification settings frontend | Tenant admin: enable/disable channels, configure templates, set reminder rules, view notification log. |
| 5.13 | Tests | File upload (including chunked), signed URL access control, notification dispatch (mock channels), template rendering, tenant isolation on object paths. |

### Deliverables
- [x] File upload with tenant-scoped storage
- [x] Document gallery with previews
- [x] Signature capture
- [x] Notification engine with email + SMS + WhatsApp backends
- [x] Tenant-configurable notification templates

---

## Sprint 6 — Audit, Reports & Dashboards

**Goal**: Immutable audit trail on all sensitive actions. Operational, financial, and clinical reports. Role-aware dashboard engine.

### Tasks

| # | Task | Details |
|---|------|---------|
| 6.1 | Audit event model | Actor, tenant, session_id, entity_type, entity_id, action, before_value (JSON), after_value (JSON), correlation_id, ip_address, user_agent, created_at (immutable). |
| 6.2 | Audit middleware & decorators | Automatic audit capture for all write operations. Manual audit annotation for reads of sensitive data. Async write to audit table (don't block the main request). |
| 6.3 | Audit viewer | Filterable audit log by actor, entity type, entity ID, action, date range, correlation ID. Export to CSV/PDF. Permission: `audit.read`. |
| 6.4 | Report engine foundation | Report definition model (name, type, query/template, parameters, permissions). Scheduled report generation. Async execution via Celery. |
| 6.5 | Operational reports | Appointments by day/provider/branch. No-show rates. Queue wait times. Staff utilization. Patient registration trend. |
| 6.6 | Financial reports | Revenue by period/practitioner/category. Outstanding balances. Collections rate. Refund analysis. Insurance receivables aging. |
| 6.7 | Dashboard engine | Widget definition model (type, config JSON, position, size, permissions, module dependency). Tenant dashboard configuration. Role-based default dashboard. |
| 6.8 | Dashboard widgets (v1) | Appointments today, revenue today, new patients this month, pending invoices, low stock alerts, queue status. |
| 6.9 | Reports & dashboard frontend | Report list → configure parameters → generate → view/download. Dashboard with grid layout, drag-to-rearrange widgets, role-based defaults. |
| 6.10 | Audit log frontend | Searchable, filterable audit table. Detail modal showing before/after diff. Export button. |
| 6.11 | Tests | Audit immutability (cannot modify/delete audit records), report accuracy against known data, dashboard widget data correctness, permission enforcement on reports, audit export format. |

### Deliverables
- [x] Immutable audit trail on all sensitive operations
- [x] Operational + financial reports
- [x] Role-aware dashboards with configurable widgets
- [x] Audit viewer with export

---

## Sprint 7 — Dental Module (First Specialty)

**Goal**: Prove the module registry architecture by shipping a deep, production-quality dental module. This is the template for all future specialties.

### Tasks

| # | Task | Details |
|---|------|---------|
| 7.1 | Module registry engine | `ModuleRegistry` in Django: modules register themselves with name, version, permissions, appointment types, patient tabs, menu items, dashboard widgets, report definitions, billing item types, settings sections. Module enable/disable per tenant. |
| 7.2 | Module registry frontend | Module list showing enabled/disabled per tenant. Install/enable/disable with confirmation. Tenant admin settings page shows each module's settings section. |
| 7.3 | Dental data models | Odontogram (patient FK, last_updated), Tooth (number, FDI/Universal notation, status, condition), ToothProcedure (tooth FK, procedure type, date, practitioner, notes, attachments), Implant (tooth, brand, size, placement date, follow-up), Crown (tooth, material, cementation date, lab). |
| 7.4 | Tooth charting API | CRUD for tooth state. Batch update for quadrant-level changes. Tooth history timeline. |
| 7.5 | Dental procedure templates | Pre-built procedure sets (composite filling, root canal, crown prep, extraction, cleaning, whitening). Template → appointment conversion. |
| 7.6 | Treatment plan (dental) | Multi-tooth treatment plan with phases, estimated costs, insurance estimates, consent attachments per procedure. Plan approval workflow. |
| 7.7 | Dental billing items | Register dental-specific billing codes into the billing item catalog. Link procedures to billing items. |
| 7.8 | Dental reports | Tooth chart summary, treatment plan progress, procedure mix by dentist, implant/crown tracking report. |
| 7.9 | Dental dashboard widgets | Today's procedures, pending treatment plans, overdue follow-ups, procedure completion rate. |
| 7.10 | Odontogram UI | Interactive tooth chart (FDI notation), click tooth → see history → add finding → plan procedure. Color-coded tooth states (healthy, treated, needs treatment, missing, implant, crown). Keyboard accessible. |
| 7.11 | Treatment plan UI | Phase-based plan builder, drag procedures between phases, cost estimates per phase, consent attachment per procedure, approval buttons. |
| 7.12 | Dental module registration | Wire everything into the module registry: permissions (`dental.*`), menu items (Tooth Chart, Treatment Plans, Dental Reports), patient tabs (Dental History), appointment types (Dental Consultation, Procedure), dashboard widgets, billing items. |
| 7.13 | Tests | Tooth chart CRUD, treatment plan calculations, module registry enable/disable behavior (dental menus should vanish when module is off), tenant isolation, permission enforcement on dental views. |

### Deliverables
- [x] Module registry is functional — enabling/disabling Dental toggles all related UI
- [x] Interactive odontogram with tooth charting
- [x] Dental treatment plans with phased costing
- [x] Dental reports and dashboard widgets
- [x] Module registry contract is proven and documented for future specialties

---

## Sprint 8 — Online Booking & API Foundation

**Goal**: Public-facing online booking portal. Internal and external REST API foundation with documentation.

### Tasks

| # | Task | Details |
|---|------|---------|
| 8.1 | Public booking page | Standalone Next.js route(s) for patient-facing booking. Tenant-resolved by subdomain. Slot picker → patient info form → confirmation. CAPTCHA on submission. |
| 8.2 | Booking confirmation flow | After booking: confirmation page, email/SMS confirmation, calendar invite (.ics) generation, "add to calendar" links. |
| 8.3 | Booking cancellation/reschedule | Token-authenticated links in confirmation emails for patient self-service cancel/reschedule. Time window restrictions. |
| 8.4 | Internal API documentation | OpenAPI/Swagger spec auto-generated from DRF. All endpoints documented with request/response examples, permission requirements, error codes. |
| 8.5 | External API foundation | API key model (per tenant, scoped permissions, rate limits). API versioning via URL prefix (`/api/v1/`). Rate limiting middleware. |
| 8.6 | External API endpoints | `GET /api/v1/appointments/slots`, `POST /api/v1/appointments`, `GET /api/v1/patients/{id}`. Scoped to the API key's permissions. |
| 8.7 | Webhook system | Webhook endpoint model (URL, events, secret, active). Event → dispatch to matching webhooks with HMAC signature. Retry with backoff. Delivery log. |
| 8.8 | WebSocket documentation | AsyncAPI spec for real-time channels (queue board updates, notification events, sync status). |
| 8.9 | API key management frontend | Tenant admin: create/revoke API keys, set scopes, view usage. |
| 8.10 | Tests | Booking flow end-to-end, CAPTCHA enforcement, API key auth and scoping, rate limiting, webhook delivery and retry, OpenAPI spec validity. |

### Deliverables
- [x] Public online booking with confirmation
- [x] OpenAPI docs for all internal endpoints
- [x] External API with key management
- [x] Webhook system with delivery guarantees

---

## Sprint 9 — Electron Desktop App & Offline Sync

**Goal**: Electron desktop app with local SQLite, offline-first operation, and cloud sync engine.

### Tasks

| # | Task | Details |
|---|------|---------|
| 9.1 | Electron shell | Electron app scaffold, window management, tray icon, auto-updater (electron-updater), app menu. Code signing setup. |
| 9.2 | SQLite local DB schema | Mirror of core working tables (patients, appointments, billing items, documents metadata). Sync metadata tables (operation queue, sync state, device info). SQLCipher for encryption at rest. |
| 9.3 | Local data layer | TanStack Query with SQLite persistence adapter. Reads hit local DB first. Writes go to local DB + sync queue. UI never waits for cloud. |
| 9.4 | Sync queue engine | Capture every local mutation as a sync operation (ID, tenant, device, user, entity, operation type, payload diff, base version, timestamp, dependencies). Queue persistence. |
| 9.5 | Sync protocol | HTTP-based sync: `POST /api/sync/push` (send queued operations), `GET /api/sync/pull` (get changes since last sync timestamp). Idempotency keys on every operation. |
| 9.6 | Conflict detection & resolution | Server-side: version check on push, reject if base version != current version. Client-side: receive conflict response, apply resolution strategy. LWW for non-clinical data. Three-way merge for demographics. Manual review required for clinical conflicts (diagnoses, prescriptions, signed notes). |
| 9.7 | Sync status & telemetry | Real-time sync status indicator (synced, syncing, offline, conflict). Sync health dashboard (queue depth, failure rate, last successful sync per device). |
| 9.8 | Offline-aware UI patterns | Network status detection (online/offline/slow). Optimistic updates with rollback. Stale data indicators. Sync-in-progress spinners on affected records. "You're offline" banner with last sync timestamp. |
| 9.9 | Desktop-specific features | Global shortcuts (quick patient search, new appointment). System notifications for reminders (bypass browser restrictions). Print support (thermal + A4). Barcode scanner input handling. |
| 9.10 | Electron security hardening | Context isolation on, nodeIntegration off, CSP headers, IPC whitelisting, ASAR integrity, code signing verification on auto-update. |
| 9.11 | Conflict resolution UI | Side-by-side diff view for conflicting records. "Accept local", "Accept remote", "Merge" actions. Clinical conflicts flagged with warning and require explicit confirmation. |
| 9.12 | Tests | Offline CRUD → online sync replay, conflict scenarios (two devices editing same record), idempotency (duplicate push), SQLite schema migration, sync after 100+ queued operations, network drop mid-sync recovery, Electron security headers. |

### Deliverables
- [x] Electron app launches, authenticates, and displays tenant-branded UI
- [x] Full offline operation: create patients, book appointments, record payments without internet
- [x] Sync replays queued operations on reconnect
- [x] Conflicts are detected and surfaced for resolution
- [x] Clinical conflicts require manual review (never auto-resolved)
- [x] Auto-updater works with code signing verification

---

## Sprint 10 — Integration, Polish & Launch Prep

**Goal**: SMS/WhatsApp live, performance optimized, security audited, white-label proven, production-ready.

### Tasks

| # | Task | Details |
|---|------|---------|
| 10.1 | SMS integration live | Twilio or regional SMS provider. Tenant-configurable sender ID. Delivery status tracking. Cost tracking. |
| 10.2 | WhatsApp integration | WhatsApp Business API integration. Template approval workflow. Message delivery and read receipts. |
| 10.3 | White-label theming engine | Resolve tenant branding at runtime: logo, colors (primary/secondary), typography, dark mode, login screen assets. CSS custom properties driven by tenant config. |
| 10.4 | White-label domain mapping | Tenant custom domain support (clinicname.com → tenant slug resolution). SSL certificate automation (optional, Phase 2). |
| 10.5 | Performance optimization | Django query optimization (N+1 elimination, select_related/prefetch_related audit). Frontend bundle analysis and code splitting. Image optimization pipeline (resize, format, lazy load). Redis caching for frequently-read config and tenant settings. |
| 10.6 | Security audit | Dependency audit (pip-audit, npm-audit). OWASP ZAP scan against staging. JWT configuration review. CSRF hardening. Rate limiting tuned per endpoint. SQL injection check on all raw queries. File upload security review. |
| 10.7 | Accessibility audit | Lighthouse accessibility score ≥ 90 on all critical screens. Keyboard navigation pass on odontogram, calendar, forms. Screen reader test on patient registration and appointment booking flows. |
| 10.8 | Error handling & edge cases | Global error boundary (React) + DRF exception handler with correlation IDs. Graceful degradation when optional services are down (email, SMS). 429/503 pages. Network retry with exponential backoff on all API calls. |
| 10.9 | Admin runbook | Document: tenant provisioning, backup/restore procedure, incident response, scaling checklist, sync troubleshooting, module installation guide. |
| 10.10 | Tenant onboarding wizard | Step-by-step setup: clinic info → branding → enable modules → configure roles → invite staff → configure notifications → go live checklist. |
| 10.11 | Production deployment | Docker production config, PostgreSQL with PITR, Redis with persistence, MinIO with replication, Nginx with TLS, environment secrets, monitoring (Sentry + Prometheus + Grafana dashboards), alerting rules. |
| 10.12 | Smoke tests & launch checklist | Automated smoke tests against production for core flows. Go/no-go checklist: all sprints' tests passing, security scan clean, accessibility score ≥ 90, performance targets met, backup/restore tested, sync tested with 3+ devices. |

### Deliverables
- [x] Live SMS and WhatsApp notifications
- [x] White-label theming per tenant (logo, colors, domain)
- [x] Performance targets met (p95 API < 200ms read, LCP < 2.5s)
- [x] Security audit passed
- [x] Accessibility score ≥ 90
- [x] Production deployment with monitoring and alerting
- [x] Admin runbook documented
- [x] MVP launch-ready

---

## Dependency Graph

```
Sprint 0 (Infrastructure)
    │
    ▼
Sprint 1 (Identity, Tenancy, RBAC)
    │
    ├──────────────────────────────────────────────┐
    ▼                                              ▼
Sprint 2 (Patients)                        Sprint 5 (Files & Notifications)
    │                                              │
    ▼                                              │
Sprint 3 (Appointments)                            │
    │                                              │
    ▼                                              │
Sprint 4 (Billing)                                 │
    │                                              │
    ├──────────────────────────────────────────────┤
    ▼                                              ▼
Sprint 6 (Audit, Reports, Dashboards) ◄────────────┘
    │
    ▼
Sprint 7 (Dental Module — module registry proof)
    │
    ├──────────────────────────┐
    ▼                          ▼
Sprint 8 (Online Booking,  Sprint 9 (Electron Desktop &
          API Foundation)              Offline Sync)
    │                          │
    └──────────┬───────────────┘
               ▼
       Sprint 10 (Integration, Polish, Launch)
```

- **Sprints 2–5 can be partially parallelized** if the team is large enough (one squad on Patients+Appointments, another on Files+Notifications), but Billing depends on Patients being done.
- **Sprints 8 and 9 can run in parallel** — they touch different codebases and have minimal overlap.
- **Sprint 7 (Dental)** is the architectural risk-mitigation sprint — if the module registry works for Dental, it will work for everything else.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Sync conflict complexity underestimated | High | High | Spike a sync prototype during Sprint 2. Use Sprint 9 buffer. |
| Module registry too rigid for dental | Medium | High | Design registry iteratively during Sprint 7. Refactor interface if needed before locking. |
| Performance issues with multi-tenant queries at scale | Medium | Medium | Add tenant_id to every index from day one. Load test with realistic data volumes in Sprint 6. |
| Electron + SQLite brings unexpected platform issues | Medium | Medium | Test on Windows + macOS from Sprint 9 day one. CI runs on both platforms. |
| Team spread too thin across 10 sprints | Medium | High | Stick ruthlessly to MVP scope. Defer everything not in the sprint plan to Phase 2. |
| Compliance/regulatory gap discovered late | Low | High | Engage a healthcare compliance consultant during Sprint 1 to review data model and consent flows. |
| Third-party API instability (SMS, WhatsApp) | Low | Medium | Abstract all integrations behind interfaces. Mock in dev. Circuit-breaker pattern in production. |

---

## Next Actions (This Week)

1. **Decide the open design questions** from the blueprint (§ Recommended Next Design Decisions):
   - Tenant isolation: shared schema with `tenant_id` on every row (simpler for MVP) vs schema-per-tenant.
   - Sync protocol: start with simple operation queue + version-based conflict detection.
   - Clinical record finalization: draft → finalized → amended (never overwrite finalized).

2. **Set up the monorepo** — Sprint 0.1 through 0.5.

3. **Define the module registry contract** — what exactly a module can register. Write the `ModuleRegistry` base class and the `DentalModule` as the first concrete implementation to validate the interface.

4. **Design the database schema** — ERD for the core entities (Tenant, User, Role, Permission, Patient, Appointment, Invoice, Document, AuditEvent). Review with the team before writing migrations.

5. **Prototype the sync engine** — a spike in Django to validate: queue → push → version check → accept/reject → ack. Don't build the full engine yet, just prove the protocol works.

---

## Phase 2+ (Beyond MVP — Not Scheduled)

The blueprint describes these phases. They are intentionally deferred:

- **Phase 2 (Expansion Modules)**: Laboratory, Imaging, Pharmacy, Dermatology, Ophthalmology — following the Dental module pattern.
- **Phase 3 (Ecosystem)**: Patient mobile app, Doctor mobile app, Plugin marketplace, Insurance/Accounting connectors, Public FHIR API.
- **Phase 4 (Interoperability & AI)**: FHIR resource exposure, SMART on FHIR third-party app access, AI assistant (note summarization, SOAP draft, ICD/CPT suggestions, image analysis), governance controls.

The key insight: **if Sprint 7 (Dental Module) proves the module registry works, every future specialty reuses the same architecture at a fraction of the cost.**
