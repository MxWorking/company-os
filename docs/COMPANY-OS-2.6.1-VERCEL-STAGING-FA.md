# Company OS v2.6.1 | Vercel compatibility and safe staging (FA)

> Base: exact user-provided Company OS 2.6 ZIP (SHA-256 `e838072370c10aad7a23ec066d944722c9713e00d19e3f38ccb86fc7f733ed98`).
> This is a staging/review version, not approved production ERP/HR/accounting software.

## Unchanged

All original Next.js pages, layouts, Neon/Glassmorphism theme, Light/Dark, FA/EN, RTL/LTR, frontend assets, FastAPI business logic, database models, role permissions, accounting and HR functionality remain intact.

## Targeted code compatibility fixes

1. `frontend/next.config.ts`: keep original same-origin `/api/:path*` proxy working for split Vercel projects using the server-only `BACKEND_ORIGIN` environment variable, with local `BACKEND_URL` fallback.
2. `frontend/lib/demo.ts`: type only changed to `Partial<Record<ModuleKey, ModuleItem[]>>` because it intentionally lists only demo modules.
3. `frontend/components/CompanyOS.tsx`: remove redundant `section !== 'settings'` type guard inside the branch that already excludes settings. Rendered UI behavior remains unchanged.
4. Restore the source `.github/workflows/qa.yml`. No user-facing screens or existing backend APIs were redesigned.

## Verification

- Local original ZIP integrity: 119 entries, no CRC errors, source SHA-256 verified.
- Local Python backend: `python -m pytest -q` passed all **54** tests.
- GitHub Actions for PR #1: Python tests and compileall passed; frontend `npm run typecheck` and `npm run build` passed.
- Vercel preview: Next.js build READY and GET / returned HTTP 200.
- FastAPI preview: Build READY but runtime GET /health returned HTTP 500, because `DATABASE_URL` is missing. This is an intentional production safety guard.
- Persistent PostgreSQL, ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_SECRET, HR_ENCRYPTION_KEY, full data migration and security QA: not configured/verified.

## Vercel projects

- company-os-web: root directory `frontend` (Next.js).
- company-os-api: root directory `backend` (FastAPI).
- Set frontend `BACKEND_ORIGIN` to the correct backend origin in each environment; do not place API secrets in `NEXT_PUBLIC_` variables.
- Keep production protected/unmodified until a dedicated durable PostgreSQL database, strong secrets and secure migrations are configured.
- Do not reuse an unrelated Supabase database or destroy any existing Docker volume.
- The root `vercel.json` in v2.6 is for the alternative **single Vercel Services** layout, not the active two-project setup; split project root settings are managed independently.

## GitHub release state

- Staging branch: `company-os-v2.6`
- Draft pull request: https://github.com/MxWorking/company-os/pull/1
- Production branch `main` is NOT merged; currently deployed production placeholders are left untouched.

When PostgreSQL provisioning and environment configuration are ready, run a full protected preview of login, session cookies, CSRF, tenant/RBAC restrictions and accounting smoke tests. Only after passing those should the staging branch replace production.
