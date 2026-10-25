# Company-OS | Deployment Foundation

A minimal deployable foundation for **Next.js (frontend)** and **Python FastAPI (backend)**.

> **Important:** This is a fresh foundation, not the complete Company-OS application. The original repository contained only LICENSE before this setup. Add the actual application code, authentication, database, AI agents, MCP gateway, and workflows in subsequent changes.

## Repository layout

- `frontend/`: Next.js App Router app and backend connectivity panel
- `backend/`: FastAPI ASGI app, health endpoint
- `.gitignore`: ignores secrets, build output, virtual environments

## Local development

**Backend (Python 3.12+):**

```bash
cd backend
python -m venv .venv
# Activate your virtual environment for your operating system.
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend (Node.js 22+):**

```bash
cd frontend
npm install
cp .env.example .env.local
# Set BACKEND_ORIGIN=http://127.0.0.1:8000 in .env.local
npm run dev
```

Visit the frontend's `/`, and check `/api/backend-health`. Backend health: `GET /api/health`. The frontend makes a server-side request to the API, so no browser CORS setup is needed for this check.

## Vercel deployment

Use **two Vercel projects connected to this GitHub repository**:

| Vercel project | Root directory | Framework |
| --- | --- | --- |
| company-os-api | backend | FastAPI |
| company-os-web | frontend | Next.js |

Deploy backend first. Configure `BACKEND_ORIGIN=https://<deployed-api-domain>` in the frontend project for Production and Preview, then redeploy frontend. Do not include a trailing slash. Never commit secrets.

Each push to `main` triggers a production deployment for both projects. Pull requests can receive Preview deployments.

## Security / next steps

This initial API exposes *only a public health check* (and FastAPI documentation), no privileged actions. Production credentials, OAuth, permissions, database connections, rate-limiting, and agents are **not yet configured**. Do not expose real agents or tools until authentication and authorization are implemented. Long-running n8n workflows/workers should be separately hosted and authenticated.

## Status

- Next.js + FastAPI bootstrap: provided
- Actual Company-OS features and original code migration: **not included**
- Persistent database: **not configured**
- Authentication: **not configured**
