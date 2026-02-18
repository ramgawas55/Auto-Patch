# AUTO PATCH — Centralized Linux Patch Management System
Project made by Ram Gawas
GitHub: https://github.com/ramgawas55

AUTO PATCH is a centralized way to see patch status across Linux servers and safely trigger patch jobs through an agent polling model. The backend stores inventories, jobs, approvals, and audit logs. The frontend gives you a clean dashboard. The agent runs on each Linux server and checks in every 60 seconds.

## What You Get
- FastAPI backend with JWT auth, approvals workflow, audit logs, and scheduling
- Next.js App Router dashboard with clean tables and filters
- PostgreSQL for inventory, updates, jobs, and results
- Agent that supports apt and yum/dnf without SSH
- Render-ready deployment via render.yaml

## Architecture
- Backend: FastAPI + Uvicorn
- Frontend: Next.js App Router + Tailwind
- Database: PostgreSQL
- Agent: Python script + systemd service/timer
- Deployment: Render Blueprint

## Repo Structure
```
backend/
frontend/
agent/
infra/
  docker-compose.yml
docs/
render.yaml
README.md
```

## Local Development (Docker Compose)
1) Start services
```
cd infra
docker compose up -d
```
2) Open frontend
```
http://localhost:3000
```
3) Login
```
Email: admin@example.com
Password: admin123
```
4) Install agent on a Linux VM and set BACKEND_URL to http://localhost:8000
5) Server appears within 5 minutes
6) Create a job, approve it, and watch logs

## Deploy to Render (Blueprint)
1) Create a new Render Blueprint and connect this repo
2) Render reads render.yaml and creates:
   - PostgreSQL database
   - Backend web service
   - Frontend web service
3) Set required backend environment variables:
   - JWT_SECRET
   - ADMIN_EMAIL
   - ADMIN_PASSWORD
4) Deploy all services
5) Open the frontend URL and login with ADMIN_EMAIL and ADMIN_PASSWORD
6) Configure agent BACKEND_URL to the backend Render URL
7) If you rename services, update FRONTEND_ORIGIN, API_BASE_URL, and NEXT_PUBLIC_API_BASE in Render

Render runs migrations automatically using:
```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables
Backend:
- DATABASE_URL
- JWT_SECRET
- ADMIN_EMAIL
- ADMIN_PASSWORD
- FRONTEND_ORIGIN
- API_BASE_URL
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- AGENT_BOOTSTRAP_TOKEN

Frontend:
- NEXT_PUBLIC_API_BASE
- NEXT_PUBLIC_APP_NAME

## Agent Install (Linux)
1) Copy agent to /opt/autopatch/agent.py
2) Create /etc/autopatch/agent.env
```
BACKEND_URL=https://autopatch-backend.onrender.com
AGENT_TOKEN=your_agent_token
BOOTSTRAP_TOKEN=optional_bootstrap_token
```
3) Install systemd unit and timer
```
sudo cp agent/systemd/autopatch-agent.service /etc/systemd/system/autopatch-agent.service
sudo cp agent/systemd/autopatch-agent.timer /etc/systemd/system/autopatch-agent.timer
sudo systemctl daemon-reload
sudo systemctl enable --now autopatch-agent.timer
```
4) Verify
```
systemctl status autopatch-agent.timer
```

Agent should run as root or with sudo permissions for package updates.

## API Examples (curl)
Login:
```
curl -X POST "$API_BASE/api/auth/login" -d "username=admin@example.com" -d "password=admin123"
```

List servers:
```
curl -H "Authorization: Bearer $TOKEN" "$API_BASE/api/servers"
```

Create job:
```
curl -X POST "$API_BASE/api/jobs" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"server_id":1,"job_type":"SCAN_NOW","requires_approval":true}'
```

Approve job:
```
curl -X POST "$API_BASE/api/approvals/1/approve" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"reason":"approved"}'
```

## Common Render Errors and Fixes
- CORS errors
  - Set FRONTEND_ORIGIN to the frontend Render URL
  - Ensure NEXT_PUBLIC_API_BASE points to backend Render URL
- DATABASE_URL sslmode issues
  - Use Render managed DATABASE_URL with sslmode=require
- Build failures on frontend
  - Use Node 18+ and run npm ci && npm run build
  - Check that NEXT_PUBLIC_API_BASE is set

## Screenshots
See docs/SCREENSHOTS.md for placeholders.
