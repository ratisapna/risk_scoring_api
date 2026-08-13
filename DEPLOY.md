# Deployment Guide: Phase 1 Skeleton

This guide walks you through deploying the `/health` skeleton to **Render** with automated CI/CD.

## Prerequisites

- GitHub account with repo `ratisapna/risk_scoring_api` (✓ done)
- Render account (free)
- No AWS account needed yet (Phase 4)

---

## Step 1: Create Render Account & Web Service (5 minutes)

### 1a. Sign up on Render
1. Go to https://render.com
2. Click "Sign up"
3. Sign up with GitHub (or email)
4. Authorize Render to access your GitHub repos

### 1b. Create a new Web Service
1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Select **"ratisapna/risk_scoring_api"** from your GitHub repos
   - (You may need to "Configure account" first to connect GitHub)
3. Configure the service:

   **Name**: `risk-scoring-api`
   
   **Environment**: `Docker`
   
   **Region**: Choose closest to you (e.g., us-east-1)
   
   **Build Command**: (leave empty)
   
   **Start Command**: (leave empty)
   
   **Plan**: Free (or Starter $7/month if you want always-on)

4. Click **"Create Web Service"**

Render will now:
- Clone your repo
- Build Docker image from `Dockerfile`
- Deploy to `https://risk-scoring-api.onrender.com` (or similar)
- Take ~3-5 minutes for first deploy

**Watch the deploy logs** in the Render dashboard. It should end with:
```
2024-01-15 10:00:00 | ✓ Service started
2024-01-15 10:00:01 | Uvicorn running on http://0.0.0.0:8000
```

### 1c. Test the deployment
```bash
curl https://risk-scoring-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "transaction-risk-scoring-api",
  "version": "0.1.0"
}
```

✓ **Skeleton deployed!**

---

## Step 2: Set Up GitHub Secrets (for Auto-Deploy)

The deploy workflow needs these secrets to trigger automatic deployments when you push to `main`.

### 2a. Get Render Deploy Key
1. In Render dashboard, go to your **"risk-scoring-api"** service
2. Click **"Settings"** (gear icon, top right)
3. Scroll down to **"Deploy"** section
4. Copy the **"Deploy Hook"** URL

   Example: `https://api.render.com/deploy/srv-xxxxx?key=rnd_xxxxx`

### 2b. Extract Service ID and Deploy Key
From the Deploy Hook URL:
- **Service ID** (after `srv-`): `xxxxx`
- **Deploy Key** (after `key=`): `rnd_xxxxx`

### 2c. Add GitHub Secrets
1. Go to your GitHub repo: https://github.com/ratisapna/risk_scoring_api
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and add:

   | Secret Name | Value |
   |---|---|
   | `RENDER_SERVICE_ID` | `srv-xxxxx` (without `https://api.render.com/deploy/`) |
   | `RENDER_DEPLOY_KEY` | `rnd_xxxxx` (the key part only) |
   | `RENDER_URL` | `https://risk-scoring-api.onrender.com` |

   (Render URL will be shown in your service dashboard)

---

## Step 3: Test the CI/CD Pipeline

### 3a. Make a test commit
```bash
cd /path/to/risk_scoring_api
echo "# Test deployment" >> README.md
git add README.md
git commit -m "Test: CI/CD pipeline"
git push origin main
```

### 3b. Watch GitHub Actions
1. Go to your repo → **"Actions"** tab
2. Click the latest workflow run
3. You should see two jobs:
   - **ci.yml**: Runs on pull request → lint, test, coverage
   - **deploy.yml**: Runs on push to main → build, deploy, smoke test

### 3c. Watch Render Deploy
1. Go to Render dashboard
2. Click your service
3. Scroll down to "Events" to see the deployment trigger
4. Watch the build and deploy logs

---

## Step 4: Understand the Auto-Deploy Flow

```
You push to main
        ↓
GitHub Actions triggered
        ↓
CI workflow runs:
  ├─ Python 3.11 setup
  ├─ pip install -e ".[dev]"
  ├─ ruff check & black --check
  └─ pytest (54 tests pass ✓, coverage 98.99%)
        ↓
Deploy workflow runs:
  ├─ Docker build
  ├─ curl Render deploy hook
  ├─ Wait for deployment (polling /health)
  └─ Smoke test passed ✓
        ↓
Service live at: https://risk-scoring-api.onrender.com/health
```

**Total time**: ~2-3 minutes

---

## Troubleshooting

### Deploy fails: "Render deployment not ready"
- Check Render dashboard → Service → Logs
- Common issues:
  - Port mismatch: Ensure `PORT=8000` in environment
  - Database connection: Phase 1 uses SQLite, should work out of box
  - Missing `HEALTHCHECK` in Dockerfile: Already included ✓

### CI workflow fails
- Check GitHub Actions → latest run → logs
- Common issues:
  - Coverage below 85%: Run `pytest --cov=app` locally to debug
  - Lint errors: Run `black app/` and `ruff check app/ --fix` locally
  - Import errors: Check `pyproject.toml` for missing dependencies

### Smoke test timeout
- Render free tier goes to sleep after 15 min inactivity
- Solution: Keep it warm or upgrade to Starter ($7/month)
- Or: Visit https://risk-scoring-api.onrender.com/health manually to wake it up

---

## What's Deployed

**Current State (Phase 1)**:
- ✓ `/health` endpoint: Live, returns 200 OK
- ⏳ `/score`: Placeholder, returns 501
- ⏳ `/transactions`: Placeholder, returns 501
- ⏳ Database: SQLite (local file)
- ✓ CI/CD: Automated test + deploy on push to main

**Next Steps (Phase 2)**:
1. Implement `/score` endpoint with rules engine
2. Add SQLAlchemy models for transactions
3. Deploy updated version (automatic via GitHub Actions)

---

## Costs

| Service | Phase 1 | Phase 2+ |
|---|---|---|
| **Render Web** | Free (sleeps after 15 min) | $7/month (always-on) |
| **Storage** | Free (SQLite) | Free (SQLite) or $7/month (Postgres) |
| **GitHub Actions** | Free (2000 min/month) | Free |
| **Total/month** | $0 | $7–14 |

---

## FAQ

**Q: Why no AWS yet?**
A: SQLite works for the skeleton. AWS Postgres + Terraform come in Phase 4 when you showcase infrastructure-as-code.

**Q: Can I scale this later?**
A: Yes. Phase 4 migrates to AWS RDS Postgres. SQLite→Postgres migration is straightforward.

**Q: Is the /health endpoint enough for a portfolio?**
A: For Phase 1, yes. Shows you can deploy. Phase 2–4 add the business logic and infrastructure.

**Q: How do I see real-time logs?**
A: 
- Render: Service → Logs (top right)
- GitHub Actions: Repo → Actions → Click workflow run

**Q: Can I test locally before pushing?**
A: Yes!
```bash
docker-compose up
curl http://localhost:8000/health
```

---

## What to Tell Interviewers

**"I built a transaction risk-scoring API with automated CI/CD. Phase 1 is a containerized skeleton deployed to Render, with GitHub Actions triggering tests on every push to main. When tests pass, the workflow automatically builds a Docker image and deploys it—the whole pipeline takes about 2 minutes. In Phase 2, I'll add the core scoring endpoints backed by SQLite, then migrate to AWS RDS and Terraform in Phase 4 to showcase infrastructure-as-code."**

---

Next steps: See `README.md` for how to proceed to Phase 2.
