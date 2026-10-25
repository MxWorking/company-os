# Company OS 2.0 | Implementation and acceptance report

Date: 2026-10-12. Source baseline: `Company-OS-NextJS-FastAPI-Review-v1.3.0.zip`.

**Release type: Functional integration MVP / developer review**. NOT a production-ready implementation of the entire architecture blueprint. No GitHub push or Vercel deploy.

## Delivered and backed by code

- Existing v1.3 landing page with light/dark FA/EN, dashboard, HR directory and AI assistant remains in source (no destructive migration).
- FastAPI `/api/v2` with **organization-scoped** accounts, password hashing (scrypt), organization membership, role checks, organization selection, member creation and role editing, and signed-session CSRF checks for v2 mutations outside demo mode.
- Dedicated v2 business entities in additive SQLAlchemy tables: organization, user, membership, record, notes, checklist, links and audit events. v1 tables retained.
- Eight distinct *catalog modules*: organization, work, HR, collaboration, documents, CRM, finance and intelligence; each has specialized editable field definitions, per-kind validation, CRUD, soft archive and scoped queries.
- **Work**: advanced projects, boards, tasks, three task views (table/kanban/timeline-style progress overview), member assignments, assigned-to-me API, optimistic record-version updates, checklists, comments, simple dependencies with cycle detection.
- **HR**: existing employee directory and management structure retained; new contract, leave and equipment record screens.
- **Collaboration**: channels, message and meeting records, comments; currently REST-refresh, not realtime.
- **Documents**: document *metadata*, internal/incoming/outgoing letters, referral records. No secure binary upload or legally valid e-signing in this version.
- **CRM**: customers, contacts, leads, opportunities, linked through record references.
- **Finance**: invoice/payment/cost/worklog metadata with validated non-negative integer values (in smallest units), per-currency fields, simple IRR aggregation.
- **Intelligence**: organization-scoped aggregate counters and read-only statistical assistant; `automation` records are **disabled drafts, never executed**.
- **Tenant isolation**: v2 queries scope to active membership organization. v1 legacy endpoints blocked for restricted v2 members, preventing bypass via old APIs.
- **UI**: custom themed OperationsWorkspace embedded into main existing menu, dynamic forms, view toggle, modal/drawer, customer/HR/finance screens, bilingual labels, organization switcher, organization-member creation and search.
- `.github/workflows/qa.yml` sample CI for backend tests + actual Next.js build on an internet-connected runner.

## Important incomplete blueprint milestones

These are **not** claimed to be finished:

1. **Migration**: v2 uses additive SQLAlchemy tables created at startup. There is NO Alembic production baseline/backfill or account-to-employee automatic migration; old data stays on v1 APIs. Explicit organization-scoped data migration and verified backup are prerequisites before real deployment.
2. **Full tenant security hardening**: multi-user v2 role checks and CSRF are an MVP. v1 demo mode and old login, login brute-force limits, granular object ACLs, field-level permissions, audit retention, MFA, password recovery, session invalidation, privacy/PII handling and penetration tests are outstanding. Do NOT place real HR/financial data on public infrastructure.
3. **Advanced planning**: timeline is a progress overview, **not** a date-accurate Gantt implementation; no scheduling engine, drag-and-drop to reorder within a board, conflict UI, offline operation, persistent saved filters or true project-page-list hierarchy with relational keys.
4. **HR**: contracts/leave/assets are typed metadata records, not a legally complete HR or payroll system; sensitive employee records remain in legacy model without v2 tenant isolation.
5. **Chat**: no websocket/pub-sub/notifications/typing/reconnect/offline synchronization; no permissioned private chat memberships.
6. **Documents**: no binary storage, malware scanning, versioned blobs, tamper-proof signatures or multi-level approval engine.
7. **CRM and finance**: no formal quote/order engine, atomic opportunity-to-project conversion, certified accounting, ledger, payment processors, FX conversion, reconciliation or project rate costing.
8. **AI and automation**: no model provider/API/LLM, retrieval index, tool execution, approval inbox, scheduler, background queue or external side effects. Rule-based, read-only counts are fully disclosed in UI.
9. **Release validation**: npm registry DNS is unavailable in this environment, so **Next.js dependency installation, typecheck, production build and end-to-end visual QA have NOT passed**. Source was syntactically parsed with local global TypeScript. Backend tests pass.
10. **Vercel**: root `vercel.json` from the baseline remains an unverified configuration depending on experimental multi-service availability; do not deploy without verifying account support or choosing a separate Python backend.

## Running locally

**Docker Compose** (requires Docker and npm internet access for container image build):

```sh
docker compose up --build
```

App: http://localhost:3000 — API: http://localhost:8000/docs

Manual backend:

```sh
cd backend
python -m venv .venv
# Activate your venv on your OS (e.g. .venv\\Scripts\\activate on Windows)
pip install -r requirements.txt -r requirements-dev.txt
# Development-only demo mode; contains fake sample data.
python -m uvicorn main:app --reload --port 8000
python -m pytest -q
```

Manual frontend in second terminal:

```sh
cd frontend
npm install
npm run dev
npm run typecheck
npm run build
```

Set `BACKEND_URL=http://127.0.0.1:8000` in `frontend/.env.local` for local Next.js rewrite. Production environment must have strong `SESSION_SECRET`, `ADMIN_PASSWORD`, HTTPS, and persistent PostgreSQL. Demo is **for local exploration only**.

## API quickstart in development demo

- `GET /api/v2/me` → user, active organization, CSRF token and role.
- `GET /api/v2/catalog` → eight modules and typed resource fields.
- `GET /api/v2/records/task` → scoped tasks; `POST /api/v2/records/task` → validated write.
- `GET /api/v2/my-work` → signed-in account tasks.
- `GET /api/v2/record/{id}/notes`, `/checklist`, `/links` → supporting workflows.
- `GET /api/v2/analytics/summary` → scoped aggregate counts.
- `POST /api/v2/assistant/query` → read-only statistical summary (no LLM).

**Testing status on 2026-10-12:** 25 Python tests passed; frontend source parsed without syntax errors, but compiling Next.js and browser testing require running the CI checks on an internet-connected machine.

## Publishing policy

No push, deploy, secret insertion or external account modification before the user inspects this ZIP and explicitly authorizes the next steps.
