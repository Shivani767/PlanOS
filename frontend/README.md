# PlanOS Frontend

Production-quality React frontend for the PlanOS enterprise planning system.

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- TanStack Query (server state)
- React Router (routing)
- Recharts (charts)
- React Hook Form + Zod (forms/validation)
- Lucide React (icons)
- Sonner (toast notifications)

## Prerequisites

- Node.js 20+
- Running PlanOS backend at http://localhost:8000

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend: http://localhost:5173
Backend: http://localhost:8000

## Login

Use seeded credentials:
- Email: `admin@acme.com`
- Password: `password123`

## Pages

| Route | Description |
|-------|-------------|
| `/login` | Authentication |
| `/dashboard` | Main overview with metrics |
| `/plans` | Plan list and management |
| `/plans/:id` | Plan detail with metrics |
| `/scenarios` | Scenario management |
| `/scenarios/:id` | Scenario detail and impact |
| `/scenarios/compare` | Scenario comparison |
| `/agent` | Planning copilot chat |
| `/agent-runs` | Agent execution history |
| `/agent-runs/:id` | Agent run trace |
| `/approvals` | Approval center |
| `/evaluations` | Evaluation metrics dashboard |
| `/imports` | Data import management |
| `/audit-logs` | Audit trail |
| `/settings` | Settings |

## Architecture

```
frontend/src/
├── components/
│   ├── ui/          # Reusable UI primitives
│   ├── layout/      # App shell, sidebar
├── pages/           # Route-level pages
├── hooks/           # TanStack Query hooks
├── lib/             # API client, utilities
├── types/           # TypeScript types
├── context/         # Auth context
└── App.tsx          # Routing
```

## API Integration

The frontend communicates with the PlanOS backend via REST API. See `FRONTEND_INTEGRATION.md` in the project root for endpoint documentation.

## Build

```bash
npm run build      # Production build
npm run preview    # Preview production build
npm run lint       # ESLint
```
