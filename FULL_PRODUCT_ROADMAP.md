# Healthcare OS — Full Blueprint Realization Plan

> **Current**: MVP — Identity, Patients, Appointments, Billing, Files, Notifications, Audit, Reports, Dental, Sync, API Keys, Webhooks. 83 tests, 110+ endpoints.
> **Target**: The complete blueprint — all specialties, pharmacy, lab, imaging, mobile apps, AI, FHIR, marketplace, product editions.

---

## Gap Analysis: What the Blueprint Describes vs. What's Built

| Blueprint Section | Built? | Gap |
|-------------------|--------|-----|
| Core Engine (Auth, Tenants, Patients, Scheduling, Billing, Files, Notifications, Reports, Audit) | ✅ Yes | — |
| Dental Module | ✅ Yes | — |
| Laboratory Module | ❌ No | Full module needed |
| Pharmacy Module | ❌ No | Full module needed |
| Imaging / Radiology Module | ❌ No | Full module + DICOM viewer |
| General Medicine Module | ❌ No | Consultation templates, diagnoses, referrals |
| Dermatology Module | ❌ No | Body mapping, photo timeline, lesion tracking |
| Ophthalmology Module | ❌ No | Eye exams, vision tests, retina imaging |
| Cardiology Module | ❌ No | ECG, echo reports, BP history, risk scoring |
| Pediatrics Module | ❌ No | Growth tracking, vaccination schedules |
| Gynecology, ENT, Orthopedics, Physiotherapy, Dialysis, Oncology, Emergency | ❌ No | Full modules needed |
| Veterinary Module | ❌ No | Specialty customizations |
| Inventory System | ❌ No | Medicines, supplies, equipment, stock, suppliers, POs |
| Plugin Marketplace | ❌ No | Third-party connector system, monetization |
| Patient Mobile App | ❌ No | Booking, records, payments, chat |
| Doctor Mobile App | ❌ No | Today's patients, encounters, prescriptions, voice notes |
| AI Module | ❌ No | SOAP generation, ICD/CPT coding, speech-to-text, image analysis |
| FHIR Interoperability | ❌ No | FHIR resource exposure, SMART on FHIR |
| Integrations | Partial | WhatsApp, Stripe/PayPal, Google/Outlook Calendar, Insurance EDI, Accounting |
| White-label / Domain Mapping | Partial | Theming engine built, domain mapping not |
| Product Editions | ❌ No | Solo Clinic, Specialist Pro, Diagnostic Center, Polyclinic, Hospital Network |
| Multi-language / RTL | ❌ No | Full i18n with translation files, RTL layout |
| Compliance Policy Engine | ❌ No | Record retention, signature rules, consent display, prescription restrictions |
| Advanced Search (Elasticsearch) | ❌ No | Fuzzy matching, phonetic search across all entities |
| EHR Interoperability (HL7, DICOM) | ❌ No | HL7 v2 messages, DICOM imaging standard |

---

## Phase 2 — Core Expansion (Sprints B1–B5)

### Sprint B1 — Inventory System

The inventory engine is a dependency for Pharmacy, Dental, and General Medicine. Build it first as standalone, then modules consume it.

| # | Task |
|---|------|
| B1.1 | `InventoryItem` model — medicines, supplies, equipment, with category, unit, cost/price |
| B1.2 | `StockMovement` model — in/out/adjust/transfer, with batch/lot tracking |
| B1.3 | `Supplier` model — contact info, lead times, pricing history |
| B1.4 | `PurchaseOrder` model — create, send, receive, status workflow |
| B1.5 | `Batch` model — lot numbers, manufacturing date, expiration date |
| B1.6 | Low-stock alert engine — threshold per item, auto-event `StockBelowThreshold` |
| B1.7 | Barcode/QR generation — labels for items, batches, shelves |
| B1.8 | Inventory API — CRUD, stock adjustments, batch queries, expiration report |
| B1.9 | Inventory frontend — stock grid, batch tracker, PO board, low-stock alerts |
| B1.10 | Inventory reports — valuation, turnover rate, expiration forecast |
| B1.11 | Module registration — permissions, menus, dashboard widgets, billing codes |
| B1.12 | Tests — stock movement math, batch expiration, tenant isolation |

### Sprint B2 — Pharmacy Module

| # | Task |
|---|------|
| B2.1 | `Prescription` model — drug, dose, frequency, duration, refills, DAW |
| B2.2 | `DispenseRecord` model — prescription fulfillment, quantity dispensed, pharmacist |
| B2.3 | `ControlledSubstanceLog` — mandatory tracking, witness signature |
| B2.4 | Prescription workflow — draft → issued → partially filled → filled → cancelled |
| B2.5 | Drug-drug interaction checker — basic severity: contraindicated/caution/ok |
| B2.6 | Refill management — auto-decrement, refill request from patient |
| B2.7 | Retail POS for pharmacy — OTC items, prescriptions, combined checkout |
| B2.8 | Pharmacy API — prescriptions, dispense, controlled substance queries |
| B2.9 | Pharmacy frontend — prescription queue, dispense screen, controlled log |
| B2.10 | Pharmacy reports — dispensing volume, controlled substance audit, stock vs dispense |
| B2.11 | Module registration — permissions, appointment types, patient tabs, menus, widgets |
| B2.12 | Tests — dispense math, controlled logging, refill count, interaction checks |

### Sprint B3 — Laboratory Module

| # | Task |
|---|------|
| B3.1 | `TestCatalog` model — test name, department, specimen type, reference ranges, turnaround time |
| B3.2 | `Specimen` model — type, collection date/time, collector, barcode |
| B3.3 | `LabOrder` model — doctor orders tests, linked to encounter |
| B3.4 | `LabResult` model — test → result value, reference range, flag (normal/high/low/critical) |
| B3.5 | Specimen lifecycle — collected → received → processing → completed |
| B3.6 | Result approval workflow — draft → reviewed → approved → amended |
| B3.7 | Barcode system — generate specimen labels, scan at each stage |
| B3.8 | Critical result alert — flag and notify ordering doctor immediately |
| B3.9 | PDF report generation — lab report with branding, reference ranges, abnormal flags |
| B3.10 | Lab API — orders, specimens, results, panel queries |
| B3.11 | Lab frontend — specimen tracking board, result entry screen, approval queue |
| B3.12 | Lab reports — turnaround time, test volume, abnormal rate, pending queue |
| B3.13 | Module registration |
| B3.14 | Tests — specimen lifecycle, result flag logic, approval workflow |

### Sprint B4 — Imaging / Radiology Module

| # | Task |
|---|------|
| B4.1 | `ImagingStudy` model — modality (X-ray, CT, MRI, ultrasound), body part, protocol |
| B4.2 | `ImagingSeries` model — series within study, DICOM metadata |
| B4.3 | `ImagingImage` model — individual image/slice, DICOM instance UID |
| B4.4 | DICOM viewer integration — embed Orthanc or OHIF viewer for DICOM images |
| B4.5 | `RadiologyReport` model — findings, impression, recommendations, radiologist |
| B4.6 | Comparison view — side-by-side display of prior studies |
| B4.7 | Annotation tools — draw, measure, arrow, text on images |
| B4.8 | Report workflow — draft → dictated → transcribed → reviewed → signed |
| B4.9 | Imaging API — studies, series, images, report CRUD, DICOM web viewer |
| B4.10 | Imaging frontend — study browser, viewer, report editor |
| B4.11 | Imaging reports — volume by modality, report turnaround, peer review stats |
| B4.12 | Module registration |
| B4.13 | Tests — study organization, report workflow, DICOM metadata |

### Sprint B5 — General Medicine + Advanced Clinical

| # | Task |
|---|------|
| B5.1 | `Encounter` model (replaces current stub) — full SOAP notes with templates |
| B5.2 | `Diagnosis` model — ICD-10 codes, primary/secondary, acute/chronic, onset date |
| B5.3 | `Referral` model — referring doctor, specialist, reason, urgency, status tracking |
| B5.4 | `VitalSigns` model — BP, HR, temp, RR, O2 sat, BMI, pain score — trendable |
| B5.5 | `Vaccination` model — vaccine, dose, lot, site, date, next due |
| B5.6 | `FamilyHistory` model — relation, condition, age of onset, status |
| B5.7 | `SocialHistory` model — smoking, alcohol, occupation, exercise, diet |
| B5.8 | Clinical templates — SOAP templates by specialty, chief-complaint-driven |
| B5.9 | General Medicine API — encounters, diagnoses, referrals, vitals, vaccines |
| B5.10 | Clinical frontend — encounter note editor with templates, diagnosis search |
| B5.11 | Clinical reports — diagnosis distribution, referral patterns, vaccination compliance |
| B5.12 | Module registration for General Medicine |
| B5.13 | Tests — vitals trending, template rendering, ICD code validation |


---

## Phase 3 — Specialty Modules (Sprints B6–B9)

Each follows the Dental module pattern: models + API + frontend + module registration + tests.

### Sprint B6 — Dermatology + Ophthalmology

| # | Task |
|---|------|
| B6.1 | **Dermatology**: `BodyMap` model — body region mapping with photo attachment points |
| B6.2 | **Dermatology**: `Lesion` model — location, size, color, morphology, dermoscopy findings |
| B6.3 | **Dermatology**: `PhotoTimeline` — dated photos of same lesion/region for progression |
| B6.4 | **Dermatology**: Body map interactive UI — click region → lesions → photo timeline |
| B6.5 | **Dermatology**: Module registration |
| B6.6 | **Ophthalmology**: `EyeExam` model — visual acuity (OD/OS/OU), refraction, IOP |
| B6.7 | **Ophthalmology**: `VisionTest` model — color vision, visual field, Amsler grid |
| B6.8 | **Ophthalmology**: `LensPrescription` — sphere, cylinder, axis, add, PD, prism |
| B6.9 | **Ophthalmology**: Retina image attachment with before/after comparison |
| B6.10 | **Ophthalmology**: Module registration |
| B6.11 | Tests for both modules |

### Sprint B7 — Cardiology + Pediatrics

| # | Task |
|---|------|
| B7.1 | **Cardiology**: `ECGRecord` model — upload, waveform data, interpretation |
| B7.2 | **Cardiology**: `EchoReport` model — LVEF, chamber sizes, valve function, findings |
| B7.3 | **Cardiology**: `BPHistory` — systolic/diastolic/pulse over time with trend chart |
| B7.4 | **Cardiology**: Cardiovascular risk calculator (Framingham/ASCVD) |
| B7.5 | **Cardiology**: Module registration |
| B7.6 | **Pediatrics**: `GrowthChart` model — height, weight, head circumference, BMI percentiles (WHO/CDC) |
| B7.7 | **Pediatrics**: `VaccinationSchedule` — age-based schedule with due/overdue alerts |
| B7.8 | **Pediatrics**: `DevelopmentalMilestone` — tracking by age, flagging delays |
| B7.9 | **Pediatrics**: Growth chart visualization — percentile curves |
| B7.10 | **Pediatrics**: Module registration |
| B7.11 | Tests for both modules |

### Sprint B8 — Gynecology + Orthopedics + ENT

| # | Task |
|---|------|
| B8.1 | **Gynecology**: `OBHistory` model — gravida/para/abortus, LMP, EDD, pregnancies |
| B8.2 | **Gynecology**: `PapSmear` model — result, follow-up, HPV co-testing |
| B8.3 | **Gynecology**: `AntenatalVisit` — gestational age, fundal height, fetal HR, ultrasound |
| B8.4 | **Gynecology**: Module registration |
| B8.5 | **Orthopedics**: `JointAssessment` — range of motion, stability, strength grading |
| B8.6 | **Orthopedics**: `FractureRecord` — bone, type, classification, treatment, healing progress |
| B8.7 | **Orthopedics**: `PhysiotherapyPlan` — exercises, sets/reps, frequency, progress |
| B8.8 | **Orthopedics**: Module registration |
| B8.9 | **ENT**: `AudiologyExam` — audiogram, tympanometry, speech discrimination |
| B8.10 | **ENT**: `EndoscopyRecord` — nasal, laryngeal, otoscopic findings with images |
| B8.11 | **ENT**: Module registration |
| B8.12 | Tests for all three modules |

### Sprint B9 — Remaining Specialties

| # | Task |
|---|------|
| B9.1 | **Physiotherapy**: Treatment plans, exercise library with video/gif, session notes, progress tracking |
| B9.2 | **Dialysis**: Treatment sessions, pre/post vitals, fluid removal, access site monitoring |
| B9.3 | **Oncology**: Staging (TNM), chemotherapy protocols, radiation therapy tracking, tumor markers |
| B9.4 | **Emergency / Urgent Care**: Triage levels (ESI 1-5), chief complaint, disposition tracking |
| B9.5 | **Veterinary**: Species/breed/weight, microchip tracking, rabies certificates, species-specific anatomy |
| B9.6 | All module registrations |
| B9.7 | Tests for all modules |


---

## Phase 4 — Integrations & Ecosystem (Sprints B10–B13)

### Sprint B10 — Payment + Calendar + Communication Integrations

| # | Task |
|---|------|
| B10.1 | **Stripe integration** — payment gateway, card processing, webhook handling for charge events |
| B10.2 | **PayPal integration** — alternative payment method, refund synchronization |
| B10.3 | **Google Calendar sync** — two-way sync: appointments in Healthcare OS ↔ Google Calendar |
| B10.4 | **Outlook Calendar sync** — Microsoft Graph API, same two-way sync |
| B10.5 | **WhatsApp Business API** — real implementation (not stub), template approval, delivery receipts |
| B10.6 | **SMS integration** — Twilio + generic HTTP gateway, delivery status webhooks |
| B10.7 | **Email provider integration** — SendGrid/Mailgun with open/click tracking |
| B10.8 | Integration settings UI — per-tenant configuration, test buttons, status indicators |
| B10.9 | Tests |

### Sprint B11 — Insurance + Accounting + Government

| # | Task |
|---|------|
| B11.1 | **Insurance EDI connector** — X12 837 (claims), 835 (remittance), 270/271 (eligibility) |
| B11.2 | **Insurance verification** — real-time eligibility check via clearinghouse API |
| B11.3 | **Insurance claim tracking** — claim status dashboard, denial reasons, appeal workflow |
| B11.4 | **Accounting integration** — QuickBooks/Xero connector, chart of accounts mapping |
| B11.5 | **Government API connectors** — prescription monitoring programs (PDMP), notifiable disease reporting |
| B11.6 | Tests |

### Sprint B12 — Plugin Marketplace

| # | Task |
|---|------|
| B12.1 | `Plugin` model — name, version, author, description, pricing (free/paid/subscription) |
| B12.2 | Plugin installation flow — browse marketplace → install → configure credentials → enable |
| B12.3 | Plugin SDK — documented interface: what a plugin can register (webhooks, settings, menu items, jobs, event listeners, billing hooks, notification channels) |
| B12.4 | Plugin certification process — review queue, security scan, approval badge |
| B12.5 | Marketplace frontend — catalog with search, categories, ratings, install button |
| B12.6 | Monetization — billing integration for paid plugins, revenue share |
| B12.7 | Example plugins — Telegram, Discord, Slack, custom SMS provider |
| B12.8 | Tests |

### Sprint B13 — Interoperability (FHIR + HL7 + DICOM)

| # | Task |
|---|------|
| B13.1 | **FHIR resource layer** — map internal models to FHIR R4 resources: Patient, Observation, Encounter, MedicationRequest, CarePlan, Appointment, Invoice (as Claim) |
| B13.2 | **FHIR API endpoints** — `GET /fhir/Patient/{id}`, `GET /fhir/Observation`, etc. with `_include`, `_revinclude` |
| B13.3 | **FHIR search** — `Patient?name=Smith`, `Observation?patient=123&code=LOINC` |
| B13.4 | **FHIR Bundle** — transaction bundles for bulk operations |
| B13.5 | **SMART on FHIR** — OAuth2 authorization code flow, launch context (patient, encounter), scoped access tokens |
| B13.6 | **SMART app registry** — third-party app registration, scopes, redirect URIs |
| B13.7 | **HL7 v2** — inbound/outbound ADT (admit/discharge/transfer), ORM (order), ORU (result) messages |
| B13.8 | **DICOM** — DICOMweb (WADO-RS, QIDO-RS, STOW-RS) for imaging interoperability |
| B13.9 | Tests |


---

## Phase 5 — Mobile, AI & Advanced Features (Sprints B14–B17)

### Sprint B14 — Patient Mobile App

| # | Task |
|---|------|
| B14.1 | React Native scaffold — shared types package from monorepo |
| B14.2 | Login / registration — phone number + OTP, biometric unlock |
| B14.3 | Appointment booking — browse slots, book, cancel, reschedule |
| B14.4 | Medical records viewer — encounters, lab results, prescriptions, documents |
| B14.5 | Invoices & payments — view invoices, pay via Stripe/PayPal |
| B14.6 | Notifications — push notifications for reminders, results, messages |
| B14.7 | Secure messaging — chat with clinic (async, not real-time for MVP) |
| B14.8 | Health wallet — store insurance cards, allergy info, emergency contacts offline |
| B14.9 | Offline support — cache recent records, queue appointment bookings |
| B14.10 | Tests |

### Sprint B15 — Doctor Mobile App

| # | Task |
|---|------|
| B15.1 | React Native scaffold (shared components with patient app) |
| B15.2 | Today's patient list — schedule view, patient cards with status |
| B15.3 | Quick encounter review — SOAP notes, vitals, past history |
| B15.4 | Voice notes — dictate note, auto-attach to encounter |
| B15.5 | e-Prescribing — search drugs, prescribe, send to pharmacy |
| B15.6 | Image review — view lab reports, imaging studies, DICOM on mobile |
| B15.7 | Secure messaging — communicate with patients, refer to specialists |
| B15.8 | Clinical decision support — drug interaction check, allergy alert at point of care |
| B15.9 | Offline support — cache today's schedule, queue notes and prescriptions |
| B15.10 | Tests |

### Sprint B16 — AI Module

| # | Task |
|---|------|
| B16.1 | **AI governance framework** — tenant-level enable/disable, audit logging, human-review requirement |
| B16.2 | **SOAP note generation** — draft from chief complaint + vitals + history, clinician reviews and signs |
| B16.3 | **ICD-10 code suggestion** — suggest codes from diagnosis text, ranked by confidence |
| B16.4 | **CPT / billing code suggestion** — suggest billing codes from procedure notes |
| B16.5 | **Speech-to-text** — dictate clinical notes, Whisper or cloud STT, real-time transcription |
| B16.6 | **Medical chat assistant** — RAG over medical knowledge base, cite sources, disclaimers |
| B16.7 | **Image analysis (future)** — dermatology lesion classification, radiology anomaly detection |
| B16.8 | **Prescription drafting** — suggest medication, dose, frequency based on diagnosis + guidelines |
| B16.9 | **Treatment plan suggestion** — evidence-based treatment pathways per diagnosis |
| B16.10 | **AI audit trail** — log every AI suggestion, whether accepted/rejected, by whom |
| B16.11 | Tests |

### Sprint B17 — Advanced Platform Features

| # | Task |
|---|------|
| B17.1 | **Multi-language UI** — `react-i18next` with namespaced keys, translation files for EN/ES/FR/AR |
| B17.2 | **RTL layout** — Arabic/Hebrew support, bidirectional layout engine |
| B17.3 | **Advanced search** — Elasticsearch for fuzzy matching, phonetic search, cross-entity search |
| B17.4 | **White-label domain mapping** — custom domain per tenant, SSL cert automation |
| B17.5 | **Compliance policy engine** — configurable record retention, signature requirements, consent display rules |
| B17.6 | **Data anonymization pipeline** — for analytics, ML training, staging environments |
| B17.7 | **Product editions** — feature flags per edition (Solo, Pro, Diagnostic, Polyclinic, Hospital Network) |
| B17.8 | **Tenant onboarding wizard** — step-by-step: clinic info → branding → modules → roles → staff → go-live |
| B17.9 | **In-app training tours** — role-specific guided tours for first-time users |
| B17.10 | **Printing system** — thermal receipt, prescription, lab result, invoice — all tenant-branded |
| B17.11 | Tests |


---

## Phase 6 — Hardening & Launch (Sprints B18–B20)

### Sprint B18 — Cross-Cutting Concerns

| # | Task |
|---|------|
| B18.1 | Performance audit — identify N+1 queries across all modules, add `select_related`/`prefetch_related` |
| B18.2 | Database index review — verify every query pattern has covering indexes |
| B18.3 | Redis caching layer — cache tenant settings, role permissions, module registry (invalidate on change) |
| B18.4 | API response pagination consistency — audit all list endpoints for consistent pagination |
| B18.5 | Error message standardization — consistent error format across all 150+ endpoints |
| B18.6 | Idempotency — add idempotency keys to all mutation endpoints (payment, prescription, procedure) |
| B18.7 | Soft-delete consistency — audit all DELETE operations, ensure soft-delete where required |

### Sprint B19 — E2E Testing & Documentation

| # | Task |
|---|------|
| B19.1 | E2E test suite — Playwright: login → patient → appointment → encounter → prescription → billing → payment for all specialties |
| B19.2 | Cross-tenant isolation test suite — automated verification for all 11+ modules |
| B19.3 | API contract tests — verify frontend ↔ backend contracts for every endpoint |
| B19.4 | OpenAPI documentation — complete `@extend_schema` decorators on all views, examples for every endpoint |
| B19.5 | Developer documentation — local setup, architecture overview, module development guide, API guide |
| B19.6 | User documentation — role-specific guides (Receptionist, Doctor, Lab Tech, Pharmacist, Admin) |
| B19.7 | Video walkthroughs — 5-minute overviews for each role |

### Sprint B20 — Launch

| # | Task |
|---|------|
| B20.1 | Production infrastructure — ECS/k8s, RDS Multi-AZ, ElastiCache, S3, CloudFront |
| B20.2 | CI/CD pipeline — automated deploy to staging → smoke tests → promote to production |
| B20.3 | Monitoring + alerting — Prometheus, Grafana, Sentry, PagerDuty integration |
| B20.4 | Backup + disaster recovery — automated daily backups, PITR, quarterly DR drills |
| B20.5 | SLA framework — uptime monitoring, latency SLOs, incident response process |
| B20.6 | Go-live — production launch with one pilot clinic, then staged rollout |

---

## Complete Timeline

| Phase | Sprints | Content | Est. Weeks |
|-------|---------|---------|------------|
| **MVP** | S0-S10 | Identity, Patients, Appointments, Billing, Files, Notifications, Audit, Reports, Dental, Sync, API, Webhooks | ✅ Done |
| **Phase 2** | B1-B5 | Inventory, Pharmacy, Laboratory, Imaging/Radiology, General Medicine + Clinical | 10 |
| **Phase 3** | B6-B9 | Derm, Ophth, Cardio, Peds, Gyn, Ortho, ENT, Physio, Dialysis, Oncology, ER, Vet | 8 |
| **Phase 4** | B10-B13 | Stripe, PayPal, Google/Outlook Calendar, WhatsApp, SMS, Insurance EDI, Accounting, Plugin Marketplace, FHIR, HL7, DICOM, SMART | 10 |
| **Phase 5** | B14-B17 | Patient App, Doctor App, AI Module, i18n/RTL, Elasticsearch, White-label, Compliance Engine, Product Editions, Onboarding Wizard | 10 |
| **Phase 6** | B18-B20 | Performance, E2E Testing, Documentation, Production Launch | 6 |
| **Total** | **30 sprints** | **From MVP to complete blueprint** | **~60 weeks** |

---

## Dependency Graph

```
MVP (Done)
  │
  ├─ B1: Inventory ────── B2: Pharmacy
  │                           │
  ├─ B3: Laboratory ─────────┤
  │                           │
  ├─ B4: Imaging/Radiology ──┤
  │                           │
  ├─ B5: General Medicine ───┤
  │                           │
  ├─ B6-B9: All Specialties ─┘
  │
  ├─ B10: Payment/Calendar/Comms ── B11: Insurance/Accounting
  │
  ├─ B12: Plugin Marketplace
  │
  ├─ B13: FHIR/HL7/DICOM
  │
  ├─ B14: Patient App ──┐
  ├─ B15: Doctor App ───┤── B16: AI ── B17: Advanced Features
  │                     │
  └─────────────────────┘
                          │
                          └── B18: Cross-cutting ── B19: Testing/Docs ── B20: Launch
```

---

## First Action (This Week)

Start **Sprint B1 — Inventory System**. This is the highest-value next module because:
1. Pharmacy, Dental, and General Medicine all depend on it
2. It's a standalone domain that doesn't touch the existing 11 apps
3. It follows the exact same module registry pattern proven by Dental

Ready to start B1 when you are.
