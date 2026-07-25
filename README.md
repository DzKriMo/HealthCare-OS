# Healthcare OS

Modular, offline-first, multi-tenant healthcare platform built with Django + Next.js + Electron.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Next.js  │  │ Electron  │  │ Patient  │  │  Doctor  │   │
│  │   Web    │  │  Desktop  │  │  Mobile  │  │  Mobile  │   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Core Engine (Django)                     │
│  Auth │ Tenants │ Patients │ Scheduling │ Billing │ Docs    │
├─────────────────────────────────────────────────────────────┤
│                   Specialty Modules                          │
│  Dental │ Lab │ Imaging │ Pharmacy │ Derm │ Cardio │ ...    │
├─────────────────────────────────────────────────────────────┤
│                   Integrations Layer                         │
│  SMS │ WhatsApp │ Email │ Payments │ Insurance │ FHIR       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and start all services
docker compose up -d

# 2. Run database migrations
docker compose exec backend python manage.py migrate

# 3. Create a superuser
docker compose exec backend python manage.py createsuperuser

# 4. Seed initial data (roles, permissions, demo tenant)
docker compose exec backend python manage.py seed_demo

# 5. Open the app
open http://localhost:3000        # Frontend
open http://localhost:8000/admin  # Django admin
open http://localhost:8000/api/docs  # API docs
open http://localhost:9001        # MinIO console
```

## Project Structure

```
Healthcare OS/
├── backend/              # Django 5.1 + DRF
│   ├── healthcare_os/   # Project settings (base/dev/prod)
│   ├── identity/        # Auth, users, roles, permissions
│   ├── tenancy/         # Tenant management, branding
│   ├── patients/        # Patient master data
│   ├── scheduling/      # Appointments, calendar
│   ├── billing/         # Invoices, payments, POS
│   ├── documents/       # File storage, signatures
│   ├── notifications/   # Email, SMS, WhatsApp orchestration
│   ├── reporting/       # Reports, dashboards
│   ├── audit/           # Immutable audit trails
│   ├── modules/         # Module registry
│   └── sync/            # Offline sync engine
├── frontend/            # Next.js 14 + shadcn/ui
│   └── src/
│       ├── app/         # App Router pages
│       ├── components/  # Shared UI components
│       ├── features/    # Feature modules
│       ├── hooks/       # Shared React hooks
│       └── lib/         # Utilities
├── desktop/             # Electron app (Sprint 9)
├── packages/
│   ├── types/           # Shared TypeScript interfaces
│   └── validators/      # Shared Zod validation schemas
├── infra/
│   ├── docker/          # Dockerfiles
│   └── nginx/           # Reverse proxy config
├── docs/                # Documentation
├── docker-compose.yml   # Dev environment
└── DEVELOPMENT_PLAN.md  # Sprint-based dev plan
```

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
npm install
npm run dev:frontend
```

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run all checks
pre-commit run --all-files
```

## Sprint Progress

| Sprint | Status | Focus |
|--------|--------|-------|
| 0 | 🚧 In Progress | Project Foundation & Infrastructure |
| 1 | ⬜ Pending | Identity, Tenancy & RBAC |
| 2 | ⬜ Pending | Patient Master Data |
| 3 | ⬜ Pending | Appointments & Scheduling |
| 4 | ⬜ Pending | Billing & Payments |
| 5 | ⬜ Pending | Files, Documents & Notifications |
| 6 | ⬜ Pending | Audit, Reports & Dashboards |
| 7 | ⬜ Pending | Dental Module (First Specialty) |
| 8 | ⬜ Pending | Online Booking & API Foundation |
| 9 | ⬜ Pending | Electron Desktop & Offline Sync |
| 10 | ⬜ Pending | Integration, Polish & Launch |

See [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for detailed sprint breakdowns.
