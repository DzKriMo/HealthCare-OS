# Healthcare OS — Build Guide

## Two Product Editions

```
┌──────────────────────────────────────────────────────────────┐
│                  Healthcare OS Platform                       │
├────────────────────────────┬─────────────────────────────────┤
│  Desktop Offline Edition   │      Cloud Edition              │
│                            │                                 │
│  • Self-contained .exe     │  • Web app (Next.js)            │
│  • Local SQLite database   │  • Desktop app (offline + sync) │
│  • Full offline operation  │  • All cloud features           │
│  • No AI / WhatsApp /      │  • Online payments (Stripe)     │
│    online payments         │  • Notifications (SMS/WhatsApp) │
│  • Optional cloud sync     │  • Patient online booking       │
│  • Single-tenant           │  • Multi-tenant + white-label   │
│  • One-time license        │  • Subscription model           │
│                            │                                 │
│  SELLABLE: End of Sprint 8 │  SELLABLE: End of Sprint 15    │
└────────────────────────────┴─────────────────────────────────┘
```

---

## Current State (Sprint 0 — What Exists Today)

### Backend (Django REST) — 80% production-ready
| Module | Status | Notes |
|--------|--------|-------|
| Auth (JWT, MFA) | ✅ Complete | Login, refresh, logout, TOTP flow |
| RBAC (9 roles, 46 permissions) | ✅ Complete | Enforced via permission decorators |
| Tenant isolation | ✅ Complete | Row-level scoping, middleware, tests |
| Patients CRUD | ✅ Complete | Full-text search, medical history, allergies, insurance |
| Appointments | ✅ Complete | 7-state status machine, conflict detection, recurring (RRULE) |
| Billing | ✅ Complete | Quotes → invoices → payments, POS, tax engine |
| Documents | ✅ Complete | S3/MinIO upload, signed URLs, signatures, versioning |
| Notifications | 🔶 Framework | Orchestration engine works, SMS/WhatsApp backends are stubs |
| Audit trail | ✅ Complete | Immutable events, middleware auto-capture, viewer |
| Sync engine | ✅ Complete | Push/pull protocol, 5 conflict strategies, idempotency |
| Clinical encounters | ✅ Complete | SOAP notes, ICD-10 diagnoses, referrals, vitals |
| All specialties (12) | ✅ Complete | Derm, ophth, cardio, peds, gyn, ortho, ent, physio, dialysis, onc, er, vet |
| Inventory | ✅ Complete | Items, stock movements, batches, suppliers, purchase orders |
| Pharmacy | ✅ Complete | Prescriptions, dispensing, controlled substance logs |
| Laboratory | ✅ Complete | Test catalog, specimens, orders, results, approval workflow |
| Imaging | ✅ Complete | Studies, series, DICOM metadata, radiology reports |
| FHIR layer | ✅ Complete | FHIR R4 resource mapping, API endpoints |
| Integrations | ✅ Complete | API keys (scoped, rate-limited), webhooks (HMAC-signed), OAuth2 |
| **83 backend tests** | ✅ Passing | pytest across all modules |
| Docker Compose (dev) | ✅ Works | Postgres, Redis, MinIO, Django, Nginx |
| CI pipeline | ✅ Configured | 3-job GitHub Actions (backend, frontend, packages) |

### Frontend (Next.js) — 30% production-ready
| Page | Status | Notes |
|------|--------|-------|
| Login | ✅ Built | MFA flow, tenant slug input. Password reset is TODO |
| Dashboard | 🔶 Scaffolded | Hardcoded widget values, not connected to real API |
| Patient list | 🔶 Scaffolded | API call wired, search works, no pagination |
| Patient detail | ⬜ Empty | File exists at `patients/[id]/` but mostly blank |
| Patient create | ⬜ Empty | File exists, minimal content |
| Appointment list | 🔶 Scaffolded | API call wired, day/week toggle, no real calendar |
| Appointment detail | ⬜ Empty | File exists |
| Appointment create | ⬜ Empty | File exists |
| Billing list | 🔶 Scaffolded | API call wired, basic invoice list |
| Billing detail | ⬜ Empty | File exists |
| Billing create | ⬜ Empty | File exists |
| Frontend tests | ❌ None | Vitest configured but zero test files |

### Desktop (Electron) — 10% production-ready
| Component | Status | Notes |
|-----------|--------|-------|
| Window management | ✅ Scaffolded | Creates window, loads Next.js URL |
| System tray | 🔶 Stub | Shows "Sync Status: Connected" (always) |
| Global shortcuts | 🔶 Stub | Registered but no handlers wired |
| SQLite database | 🔶 Schema written | `database.ts` has full schema, `initLocalDatabase()` is a no-op |
| Sync client | 🔶 Stub | Full TypeScript class written, not connected to Electron |
| Auto-updater | ❌ None | Commented out |
| Code signing | ❌ None | Not configured |
| Desktop build pipeline | ❌ None | `electron-builder` in package.json but untested |

### Infrastructure — 40% production-ready
| Component | Status | Notes |
|-----------|--------|-------|
| Docker Compose (dev) | ✅ Works | Full stack on `docker compose up` |
| Docker Compose (prod) | 🔶 Skeleton | References gunicorn not in requirements.txt |
| CI pipeline | ✅ Configured | Never run (no commits) |
| pre-commit hooks | ✅ Configured | Ruff, ESLint, secrets detection |
| .env.example | ✅ Complete | All env vars documented |
| **Git** | ❌ Empty | Zero commits, nothing staged |

---

## Sprint Cadence

- **Sprint length**: 2 weeks (3 weeks for heavy ones)
- **Total**: 15 sprints (~34 weeks to Cloud Edition launch)
- **Milestone 1**: Desktop Offline Edition sellable at Sprint 8 (~18 weeks)
- **Milestone 2**: Cloud Edition sellable at Sprint 15 (~34 weeks)

---

## Phase 1 — Frontend Core (Sprints 1–4)

**Goal**: Every frontend page is connected to the real backend API with loading, empty, error states. Full CRUD workflows work end-to-end.

---

### Sprint 1 — Git, Data & Frontend Foundation

**Goal**: Repo initialized, migrations correct, frontend shell production-ready.

| # | Task | Details |
|---|------|---------|
| 1.1 | **Git init** | First commit with `.gitignore`, signed commit setup. Push to `main` on GitHub. |
| 1.2 | **Regenerate Django migrations** | Drop `--run-syncdb` approach. Run `makemigrations` for all apps. Test forward + rollback. |
| 1.3 | **Seed data scripts** | `seed_demo.py` creates a real tenant with sample patients, appointments, invoices, users with different roles. |
| 1.4 | **API smoke test** | Script that hits every endpoint and confirms 200/401/403 as expected. Documented in CI. |
| 1.5 | **Remove hardcoded demo creds** | `frontend/src/app/page.tsx:161` — extract to env or remove. |
| 1.6 | **Frontend error boundary** | Global error boundary with correlation ID display and retry button. |
| 1.7 | **Loading states** | Skeleton loaders on every list/detail page. Consistent pattern. |
| 1.8 | **Empty states** | Every list page shows helpful empty state with CTA. |
| 1.9 | **API client hardening** | Consistent error handling, timeout support, retry logic on network flakiness. |
| 1.10 | **Dashboard shell polish** | Responsive sidebar nav, user menu, role-aware menu items, breadcrumbs. |
| 1.11 | **Password reset flow** | Implement the TODO in login page. Forgot password → email → reset form. |
| 1.12 | **CI goes green** | First CI run passes: Ruff, ESLint, Prettier, mypy, tsc, pytest, vitest (even with 0 tests). |

**Deliverables**: Git repo with history. `docker compose up` → login → see dashboard. CI green.

---

### Sprint 2 — Patients (Frontend)

**Goal**: Full patient management UI — register, search, view, edit, archive. Timeline view works.

| # | Task | Details |
|---|------|---------|
| 2.1 | **Patient detail page** | Tabbed layout: Demographics, Medical History, Allergies, Insurance, Emergency Contacts, Documents, Timeline. |
| 2.2 | **Patient registration form** | Multi-section form with Zod validation. Show validation errors inline. |
| 2.3 | **Patient edit form** | Same form in edit mode. Show change history. |
| 2.4 | **Patient search** | Real-time search as user types (debounced 300ms). Results with highlight. |
| 2.5 | **Patient list pagination** | Infinite scroll or page-based with page size. |
| 2.6 | **Patient quick actions** | From list: quick book appointment, create invoice, view timeline. |
| 2.7 | **Patient timeline** | Chronological feed of all events (appointments, encounters, invoices, documents, notes). |
| 2.8 | **Medical history editor** | Add/edit chronic conditions, surgeries, family history, social history. |
| 2.9 | **Insurance and emergency contacts** | Add/edit/remove. Primary/secondary insurance. |
| 2.10 | **Consent management UI** | View/add consent records. Show consent status on patient header. |
| 2.11 | **Frontend tests** | Patient form validation, search debounce, timeline rendering. |

**Deliverables**: Full patient lifecycle in the browser. Search, register, view timeline. Tests pass.

---

### Sprint 3 — Appointments & Scheduling (Frontend)

**Goal**: Interactive calendar, appointment CRUD, queue board. Real-time-ish via polling.

| # | Task | Details |
|---|------|---------|
| 3.1 | **Calendar view** | FullCalendar or custom: day/week/month views. Color-coded by type/status. |
| 3.2 | **Create appointment** | Date/time picker → select patient → select practitioner → set type/notes → confirm. Conflict warning shown inline. |
| 3.3 | **Appointment detail** | Patient info, practitioner, time, status, notes. Action buttons: confirm, arrive, start, complete, cancel, no-show. |
| 3.4 | **Edit / reschedule** | Drag on calendar to reschedule. Edit form for other fields. |
| 3.5 | **Recurring appointments** | Set recurrence rule. Show recurring series indicator. Edit single vs edit series. |
| 3.6 | **Queue board** | Today's appointments grouped by practitioner. Status badges. Next-up indicator. Auto-refresh every 30s. |
| 3.7 | **Waiting list** | Add patient to waiting list. Show when slots open. |
| 3.8 | **Practitioner schedule view** | See availability slots, breaks, max patients. |
| 3.9 | **Status machine enforcement** | UI only allows valid transitions (e.g., can't mark no-show before confirmed). |
| 3.10 | **Frontend tests** | Calendar rendering, appointment CRUD, status transitions, conflict detection display. |

**Deliverables**: Drag-to-reschedule calendar. Queue board refreshes live. Full appointment lifecycle.

---

### Sprint 4 — Billing (Frontend)

**Goal**: Create quotes/invoices, record payments, POS checkout. All calculations match the backend.

| # | Task | Details |
|---|------|---------|
| 4.1 | **Invoice list** | Filter by status (draft/issued/paid/overdue), date range, patient. Sort by date, amount, status. |
| 4.2 | **Invoice detail** | Line items, subtotal, tax, discount, total. Payment history. Refund button. |
| 4.3 | **Create invoice** | Add line items (search billing catalog), set quantities/prices, apply tax, add discount. Preview before issue. |
| 4.4 | **Edit invoice** | Only draft invoices. Locked after issued. |
| 4.5 | **Record payment** | Modal: amount, method (cash/card/transfer), reference, date. Partial payment support. |
| 4.6 | **POS checkout** | Quick mode: search items → select → total → payment → receipt. For walk-in payments. |
| 4.7 | **Invoice PDF** | Download tenant-branded PDF. Preview before download. |
| 4.8 | **Patient billing history** | Tab on patient detail showing all invoices, payments, balances. |
| 4.9 | **Revenue widgets** | Today's revenue, outstanding balance, overdue count. Live data (not hardcoded). |
| 4.10 | **Frontend tests** | Invoice calculation, payment recording, POS flow, PDF generation. |

**Deliverables**: Quote → invoice → payment workflow end-to-end in the browser. Sales ready.

---

## Phase 2 — Desktop Offline Edition (Sprints 5–8)

**Goal**: Desktop app with full offline CRUD, local SQLite, sync engine. **First sellable product.**

---

### Sprint 5 — Electron & Local Database

**Goal**: Electron app launches with Next.js UI, local SQLite stores and retrieves data offline.

| # | Task | Details |
|---|------|---------|
| 5.1 | **Electron + Next.js integration** | Production build of Next.js served by Electron. Dev mode loads from localhost. |
| 5.2 | **better-sqlite3 integration** | Replace stub. WAL mode for concurrent reads. Migrations on first launch. |
| 5.3 | **Data access layer** | Repository pattern: reads from SQLite first, falls back to API when online. |
| 5.4 | **Offline CRUD — Patients** | Create, read, update, delete patients entirely offline. |
| 5.5 | **Offline CRUD — Appointments** | Create, reschedule, cancel appointments offline. Conflict markers. |
| 5.6 | **Offline CRUD — Billing** | Create invoices, record payments offline. Invoice number sequence locally. |
| 5.7 | **Offline indicator** | Green dot (online) / amber (syncing) / red (offline) in system tray + app bar. |
| 5.8 | **Desktop build pipeline** | `electron-builder` config for Windows (NSIS), macOS (DMG), Linux (AppImage). |
| 5.9 | **Desktop app menu** | File, Edit, View, Help menus with standard shortcuts. |
| 5.10 | **IPC bridge** | `contextBridge` API exposed. Renderer communicates with main process for DB + sync. |
| 5.11 | **Tests** | SQLite CRUD, Electron window creation, IPC roundtrip, offline/online detection. |

**Deliverables**: Launch Electron app → create patient offline → quit → relaunch → data persists.

---

### Sprint 6 — Sync Engine (Desktop)

**Goal**: Background sync pushes local changes to cloud, pulls remote changes to local. Conflicts handled.

| # | Task | Details |
|---|------|---------|
| 6.1 | **Wire SyncClient to IPC** | `sync-client.ts` calls `window.healthcareOS` methods → main process → SQLite + HTTP. |
| 6.2 | **Push local changes** | Every local mutation enqueues to `sync_queue`. Background worker pushes every 30s. |
| 6.3 | **Pull remote changes** | Poll `/api/sync/pull/` for changes since last cursor. Apply to local SQLite. |
| 6.4 | **Idempotency** | Every operation has unique key. Server deduplicates. |
| 6.5 | **Conflict detection** | Version mismatch → log to `sync_conflict_log`. Default: server-wins for scheduling/billing, client-wins for notes. |
| 6.6 | **Conflict resolution UI** | Side-by-side diff for conflicted records. Accept local / accept remote / keep both. |
| 6.7 | **Sync status dashboard** | Queue depth, last sync time, failure count, conflict count. Accessible from tray. |
| 6.8 | **Exponential backoff** | Failed sync retries: 30s → 1min → 2min → 4min → 5min cap. |
| 6.9 | **Sync health telemetry** | Log sync attempts, failures, conflicts. Report in admin dashboard. |
| 6.10 | **Tests** | Offline → create → online → sync verifies. Two devices editing same record → conflict logged. 100 ops queue → all sync successfully. Network drop mid-sync → no data loss. |

**Deliverables**: Work offline → go online → data appears on web. Conflicts are caught and resolvable.

---

### Sprint 7 — Desktop Experience & Polish

**Goal**: Desktop feels like a native app. Printing, shortcuts, notifications, auto-update.

| # | Task | Details |
|---|------|---------|
| 7.1 | **Global shortcuts** | `Ctrl+Shift+P` patient search, `Ctrl+Shift+N` new appointment, `Ctrl+Shift+I` new invoice. |
| 7.2 | **System tray** | Right-click: Open, Sync Status, New Patient, New Appointment, Quit. |
| 7.3 | **Native notifications** | System notification for upcoming appointments, sync conflicts, low stock. |
| 7.4 | **Print support** | Thermal receipt printing for POS. A4 invoice printing. Prescription printing. |
| 7.5 | **Barcode / QR scanning** | Input field that listens to barcode scanner (keyboard wedge). Auto-submit on scan. |
| 7.6 | **Auto-updater** | `electron-updater` with staged rollouts (10% → 50% → 100%). Forced update for critical patches. |
| 7.7 | **Code signing** | Windows EV certificate. macOS notarization. Signature verification before update. |
| 7.8 | **Desktop installer** | Clean NSIS installer for Windows. DMG for macOS. AppImage for Linux. |
| 7.9 | **Offline splash screen** | Show cached data freshness info. "Last synced: 2 hours ago" with sync-now button. |
| 7.10 | **Performance** | App startup < 3s. Patient search < 200ms. Calendar render < 500ms. |
| 7.11 | **Tests** | Shortcut registration, print spooler mock, auto-updater config validation, installer build. |

**Deliverables**: Installable, signed, auto-updating desktop app. Printing works. Shortcuts feel native.

---

### Sprint 8 — Desktop Offline Edition Launch

**Goal**: Ship Desktop Offline Edition v1.0 as a paid product.

| # | Task | Details |
|---|------|---------|
| 8.1 | **Licensing** | License key validation (offline-friendly: public-key signed tokens). Offline activation fallback. |
| 8.2 | **One-click backup** | Export entire SQLite DB to encrypted file. Restore from backup on first-launch wizard. |
| 8.3 | **First-launch wizard** | Select language → Create admin account → Import data or start fresh → Quick tour. |
| 8.4 | **User documentation** | Role-specific guides for Receptionist, Doctor, Admin. In-app tooltips. |
| 8.5 | **Installation guide** | System requirements, install steps, network setup (if sync enabled). |
| 8.6 | **Landing page** | Product page for Desktop Offline Edition. Feature list, screenshots, pricing. |
| 8.7 | **Trial mode** | 14-day free trial with all features. Watermark on exports until licensed. |
| 8.8 | **Analytics** | Opt-in usage telemetry (anonymized). Crash reporting via Sentry. |
| 8.9 | **Support channel** | In-app "Send feedback" with log attachment. Support email. |
| 8.10 | **Acceptance testing** | Install on clean Windows 10/11, macOS 14+, Ubuntu 22+. Test all core workflows offline. |

**Deliverables**: ✅ **Desktop Offline Edition v1.0 — Ready to sell.**

---

## Phase 3 — Cloud Edition (Sprints 9–12)

**Goal**: Web + desktop with online payments, notifications, booking, multi-tenant. **Second sellable product.**

---

### Sprint 9 — Online Payments

**Goal**: Patients can pay invoices online via credit card. Stripe integrated.

| # | Task | Details |
|---|------|---------|
| 9.1 | **Stripe Connect integration** | Stripe account creation per tenant. Onboarding flow. |
| 9.2 | **Payment intent API** | Backend creates Stripe PaymentIntent. Webhook handles `payment_intent.succeeded`. |
| 9.3 | **Card payment form** | Stripe Elements in frontend. SCA-ready. Saved cards for repeat use. |
| 9.4 | **Invoice payment page** | Patient receives link → sees invoice → pays with card → receipt. |
| 9.5 | **Payment reconciliation** | Stripe payout → mark invoice paid. Partial payments. Refunds. |
| 9.6 | **Payment methods** | Card + bank transfer (manual) + cash (POS). Unified payment record. |
| 9.7 | **Receipt email** | Send receipt on successful payment. PDF attachment. |
| 9.8 | **Subscription billing** | Recurring invoices for subscription plans. Retry on failure. Dunning. |
| 9.9 | **Tests** | Payment intent creation, webhook handling, refund flow, receipt generation. |

**Deliverables**: Pay invoice with credit card. Money lands in Stripe. Invoice auto-marks paid.

---

### Sprint 10 — Notifications (SMS / WhatsApp / Email)

**Goal**: Patients get appointment reminders, payment due notices, lab result alerts.

| # | Task | Details |
|---|------|---------|
| 10.1 | **Email provider** | SendGrid or Mailgun integration. Verified sender. Open/click tracking. |
| 10.2 | **SMS integration** | Twilio. Tenant-configurable sender ID. Delivery status tracking. |
| 10.3 | **WhatsApp Business** | Full WhatsApp Business API. Template approval workflow. Message receipts. |
| 10.4 | **Notification templates** | Tenant-customizable templates for each event type. Preview before save. |
| 10.5 | **Reminder scheduling** | Configurable: when to send (24h, 2h, 30min before). Per appointment type. |
| 10.6 | **Notification preferences** | Per-tenant channel enable/disable. Per-patient opt-out. |
| 10.7 | **Notification log** | Search sent notifications. See status (sent/delivered/failed). Resend button. |
| 10.8 | **Tests** | Email delivery, SMS delivery (mock Twilio), WhatsApp template validation, reminder schedule calculation. |

**Deliverables**: Appointment reminders go out. Patients get SMS/WhatsApp. Log shows delivery status.

---

### Sprint 11 — Online Booking & Patient Portal

**Goal**: Patients book appointments online. View their own records. Self-service.

| # | Task | Details |
|---|------|---------|
| 11.1 | **Public booking page** | Tenant-resolved subdomain. Slot picker → patient info → book → confirm. CAPTCHA. |
| 11.2 | **Booking confirmation** | Confirmation page with "Add to Calendar" (.ics). Email/SMS confirmation. |
| 11.3 | **Self-service cancel/reschedule** | Token-authenticated link in confirmation. Time-window restrictions. |
| 11.4 | **Patient portal** | Login → view upcoming appointments → view past encounters → view invoices → update profile. |
| 11.5 | **Portal notifications** | Patients opt into email/SMS reminders. Choose 24h/2h/30min. |
| 11.6 | **Online intake forms** | Patient fills demographics, medical history, consent before first appointment. |
| 11.7 | **Tests** | Booking flow end-to-end, CAPTCHA, cancellation within window, portal authentication. |

**Deliverables**: Patient books online → appears in calendar → receives confirmation. No staff involvement.

---

### Sprint 12 — Multi-Tenant & White-Label

**Goal**: Each clinic gets their own domain, logo, colors. Onboarding is self-service.

| # | Task | Details |
|---|------|---------|
| 12.1 | **Tenant onboarding wizard** | Step-by-step: clinic info → branding → enable modules → create roles → invite staff → configure notifications → go-live checklist. |
| 12.2 | **Custom domain mapping** | `clinicname.com` → resolves to tenant. SSL cert automation via Let's Encrypt. |
| 12.3 | **White-label theming** | Logo, colors, fonts, login screen background. Persisted in tenant branding JSON. |
| 12.4 | **Module enable/disable** | Per-tenant module toggle. Turn off specialties the clinic doesn't use. |
| 12.5 | **Role templates** | Pre-built roles: Receptionist, Doctor, Lab Tech, Pharmacist, Admin, Super Admin. One-click apply. |
| 12.6 | **Branded email templates** | Clinic logo and colors in notification emails. |
| 12.7 | **Branded PDF exports** | Invoice, prescription, lab report with clinic branding. |
| 12.8 | **Tests** | Domain resolution, SSL cert generation (mock Let's Encrypt), branding CSS injection, module toggle hides/shows UI. |

**Deliverables**: New clinic signs up → uploads logo → gets `clinicname.healthcare-os.com` → invites staff → goes live in 15 minutes.

---

## Phase 4 — Production Launch (Sprints 13–15)

**Goal**: Secure, scalable, monitored. Ready for enterprise customers.

---

### Sprint 13 — Security & Compliance

**Goal**: Pass HIPAA technical assessment. OWASP Top 10 clean.

| # | Task | Details |
|---|------|---------|
| 13.1 | **Secret rotation** | Auto-rotate DB passwords (monthly), JWT keys (quarterly). Dual-credential window. |
| 13.2 | **TLS everywhere** | Let's Encrypt on all endpoints. HSTS preload. HTTP→HTTPS redirect. |
| 13.3 | **CSP headers** | Strict Content-Security-Policy. `script-src 'self'`. No inline scripts. |
| 13.4 | **Rate limiting** | Login: 5/min per IP. API: 1000/min per tenant. Configurable. |
| 13.5 | **File upload security** | ClamAV scan on upload. Magic byte validation. Size limits at Nginx + Django. |
| 13.6 | **Audit log completeness** | Every PHI access (read + write) produces audit event. Automated verification. |
| 13.7 | **PHI data flow map** | Document every place PHI touches. Verify encryption at rest + in transit. |
| 13.8 | **Penetration test** | OWASP ZAP against staging. Fix all medium+ findings. |
| 13.9 | **Dependency audit** | `pip-audit` + `npm audit` in CI. Weekly automated PRs for updates. |
| 13.10 | **Break-glass access** | Emergency admin access: triggers alert, 15-min timeout, full audit trail. |

**Deliverables**: Security scan passes. HIPAA technical safeguards documented. Audit log covers every PHI touch.

---

### Sprint 14 — Testing, Performance & Monitoring

**Goal**: Sleep at night. Know about problems before users do.

| # | Task | Details |
|---|------|---------|
| 14.1 | **Frontend tests** | Vitest tests for all pages, stores, hooks, API client. Aim 60%+ coverage on `lib/` and `features/`. |
| 14.2 | **E2E smoke tests** | Playwright: login → dashboard → patient → appointment → invoice → payment → logout. Runs in CI. |
| 14.3 | **Load tests** | k6: 500 concurrent users booking appointments. p95 < 500ms. |
| 14.4 | **Performance audit** | N+1 elimination. Missing indexes. Redis caching for tenant settings + role permissions. |
| 14.5 | **Bundle optimization** | Code-split routes. Lazy-load heavy components. Tree-shake unused shadcn/ui. |
| 14.6 | **Structured logging** | JSON logs with correlation_id, tenant_id, user_id, duration_ms. Ship to Loki. |
| 14.7 | **Metrics** | Prometheus: request rate, error rate, p50/p95/p99 latency, DB query count, Celery queue depth. |
| 14.8 | **Grafana dashboards** | Platform Overview + Business Metrics (appointments/day, revenue/day) + Sync Health. |
| 14.9 | **Alerting** | PagerDuty alerts: error rate > 1%, p95 latency > 1s, sync backlog > 500, Celery worker down. |
| 14.10 | **Sentry** | Django + React error tracking. Source maps in production. Alert on new error types. |

**Deliverables**: Load test passes. E2E tests pass in CI. Dashboard shows real-time metrics. Alerts fire on anomalies.

---

### Sprint 15 — Cloud Edition Launch

**Goal**: Production deployment. Customer onboarding pipeline. **Ready to sell.**

| # | Task | Details |
|---|------|---------|
| 15.1 | **Production infrastructure** | RDS Multi-AZ, ElastiCache Redis, ECS Fargate (Django + Celery), S3 + CloudFront. Terraform-managed. |
| 15.2 | **Blue-green deploy** | Two stacks. Deploy to inactive, health-check, swap traffic. Rollback in < 2 min. |
| 15.3 | **Database backup** | Daily full backup. WAL archival for PITR. Weekly restore test (automated). |
| 15.4 | **Disaster recovery drill** | Simulate primary DB failure. Failover → verify → document recovery time. |
| 15.5 | **SLA targets** | 99.5% uptime. p95 API < 200ms. Sync replay < 30s for 100 ops. RPO < 1h, RTO < 4h. |
| 15.6 | **Customer onboarding** | Create tenant → configure domain → branding → modules → roles → invite staff → go-live. < 30 min. |
| 15.7 | **Admin runbook** | Tenant provisioning, backup/restore, incident response, scaling, key rotation. |
| 15.8 | **Pricing page** | Desktop Offline (one-time) vs Cloud (monthly per provider). Feature comparison. |
| 15.9 | **Trial → paid conversion** | Cloud: 14-day free trial. Automated email sequence. In-app upgrade prompts. |
| 15.10 | **Acceptance testing** | Full workflow test: sign up → onboard → use for a week → no data loss → upgrade → success. |

**Deliverables**: ✅ **Cloud Edition v1.0 — Ready to sell.**

---

## Edition Feature Matrix

| Feature | Desktop Offline | Cloud (Web) | Cloud (Desktop) |
|---------|:-:|:-:|:-:|
| Patients CRUD | ✅ | ✅ | ✅ |
| Appointments & Calendar | ✅ | ✅ | ✅ |
| Billing & Payments (offline) | ✅ | ✅ | ✅ |
| Documents & Signatures | ✅ | ✅ | ✅ |
| Clinical Encounters (SOAP) | ✅ | ✅ | ✅ |
| All 12 Specialties | ✅ | ✅ | ✅ |
| Inventory | ✅ | ✅ | ✅ |
| Pharmacy | ✅ | ✅ | ✅ |
| Laboratory | ✅ | ✅ | ✅ |
| Imaging / Radiology | ✅ | ✅ | ✅ |
| Offline operation | ✅ | ❌ | ✅ |
| Local SQLite database | ✅ | ❌ | ✅ |
| Cloud sync | Optional | ✅ | ✅ |
| Online payments (Stripe) | ❌ | ✅ | ✅ |
| Email notifications | ❌ | ✅ | ✅ |
| SMS notifications | ❌ | ✅ | ✅ |
| WhatsApp notifications | ❌ | ✅ | ✅ |
| Online patient booking | ❌ | ✅ | ✅ |
| Patient portal | ❌ | ✅ | ✅ |
| Multi-tenant | ❌ | ✅ | ✅ |
| White-label / Custom domain | ❌ | ✅ | ✅ |
| AI features | ❌ | Phase 2 | Phase 2 |
| Mobile apps | ❌ | Phase 2 | Phase 2 |

---

## Sprint Summary

| Sprint | Focus | Duration | Deliverable |
|--------|-------|----------|-------------|
| 0 | *What exists today* | — | Backend 80%, Frontend 30%, Desktop 10% |
| 1 | Git, Data, Frontend Foundation | 2 weeks | Repo initialized, migrations correct, CI green |
| 2 | Patients Frontend | 2 weeks | Full patient lifecycle in browser |
| 3 | Appointments Frontend | 2 weeks | Calendar, queue board, status machine |
| 4 | Billing Frontend | 2 weeks | Quote → invoice → payment end-to-end |
| 5 | Electron + Local Database | 3 weeks | Offline CRUD for core entities |
| 6 | Sync Engine | 3 weeks | Background sync, conflict resolution |
| 7 | Desktop Polish | 2 weeks | Printing, shortcuts, auto-update, code signing |
| **8** | **Desktop Offline Launch** | **2 weeks** | **🛒 Edition #1 sellable** |
| 9 | Online Payments | 2 weeks | Stripe integration |
| 10 | Notifications | 2 weeks | Email, SMS, WhatsApp live |
| 11 | Online Booking & Portal | 2 weeks | Patient self-service |
| 12 | Multi-tenant & White-Label | 2 weeks | Tenant onboarding, custom domains |
| 13 | Security & Compliance | 3 weeks | HIPAA-ready, pen-test clean |
| 14 | Testing & Monitoring | 3 weeks | E2E tests, load tests, dashboards, alerting |
| **15** | **Cloud Edition Launch** | **2 weeks** | **🛒 Edition #2 sellable** |
| | **Total** | **~34 weeks** | |

---

## What You Need to Know Before Starting

### Team size assumption
This plan assumes **1-2 full-stack developers**. If you're solo, expect ~50-60 weeks instead of 34. If you have 3+ developers, you can parallelize Phase 1 (frontend) with Phase 2 (Electron).

### Biggest risks
1. **Sync complexity** — Conflict resolution when two devices edit the same record offline is genuinely hard. Sprint 6 has a full 3 weeks for this. Don't cut it short.
2. **Electron packaging** — Code signing, auto-updaters, and platform-specific bugs (Windows vs macOS vs Linux) always take longer than expected.
3. **Stripe integration** — Payment webhooks, idempotency, and edge cases (partial refunds, failed payments) need careful testing.
4. **Frontend scope** — The frontend looks smaller than it is. Every table needs sort/filter/search. Every form needs validation/error states/loading. Every page needs empty/error/loading states. This adds up.

### What you should NOT build yet
- AI features (SOAP generation, ICD coding, voice-to-text)
- Mobile apps (React Native)
- Plugin marketplace
- FHIR SMART on FHIR third-party apps
- Insurance EDI (X12)
- Multi-language / RTL
- Elasticsearch

These are Phase 2. First, ship the product.

### Immediate next step
Initialize the git repo and make the first commit. Everything else depends on having a baseline you can roll back to.

```bash
git init
git add -A
git commit -m "Initial commit: Healthcare OS — backend core, frontend scaffold, desktop scaffold"
git remote add origin https://github.com/DzKriMo/HealthCare-OS
git push -u origin main
```
