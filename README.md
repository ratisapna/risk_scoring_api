# Transaction Risk Scoring API

A portfolio project demonstrating backend engineering, CI/CD, and infrastructure-as-code (IaC) skills for fraud/risk engineering roles. This is a rule-based transaction risk-scoring API that evaluates financial transactions against a set of explainable fraud heuristics.

## Project Goals

- **Core logic**: Implement a modular, testable rules engine for transaction risk assessment
- **Data layer**: PostgreSQL persistence with SQLAlchemy ORM and Alembic migrations
- **API**: FastAPI endpoints for scoring, storage, and retrieval of transactions
- **Testing**: High-coverage unit and integration tests with pytest
- **CI/CD**: GitHub Actions workflows for automated testing, linting, and deployment
- **Infrastructure**: Terraform configuration to provision production database

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Request                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   FastAPI Application   │
        │   ├─ POST /score       │
        │   ├─ GET /transactions │
        │   ├─ GET /transactions/{id} │
        │   └─ GET /health       │
        └────────┬───────────────┘
                 │
        ┌────────┴──────────┬──────────────┐
        │                   │              │
        ▼                   ▼              ▼
   ┌────────────┐  ┌────────────────┐ ┌──────────┐
   │Rules Engine│  │SQLAlchemy ORM  │ │PostgreSQL│
   ├─ Velocity  │  ├─ Models        │ │Database  │
   ├─ Amount    │  ├─ Session       │ │          │
   ├─ Travel    │  └─ Migrations    │ └──────────┘
   ├─ Category  │
   └─ New Account │
        ▲
        └─ Pure functions, fully testable
```

## Scoring Rules

Each transaction is evaluated against five independent rules. A triggered rule contributes its weight to the overall risk score (capped at 100).

### 1. **Velocity Check** (weight: 30)
- Flags if user has >5 transactions within 10 minutes
- Detects card testing, fraud bursts

### 2. **Amount Anomaly Check** (weight: 35)
- Flags if transaction is ≥3x user's average, or
- ≥2 standard deviations above mean (z-score ≥ 2.0)
- Detects sudden large purchases

### 3. **Impossible Travel Check** (weight: 40)
- Flags if transaction location is geographically implausible
- Compares: distance / time > 900 km/h (commercial flight max)
- Example: NYC → London in 1 hour = ❌ fraud signal

### 4. **High-Risk Category Check** (weight: 25)
- Flags merchant categories known for fraud risk:
  - Cryptocurrency exchanges
  - Wire transfers
  - Gift card sellers
  - Money remittance
  - Gambling, prepaid cards, high-value goods

### 5. **New Account + High Value Check** (weight: 20)
- Flags if account is <30 days old AND transaction > $1,000
- Detects account takeover on recently created accounts

## Severity Labels

- **Low** (0–33): Safe, routine transaction
- **Medium** (34–66): Worth monitoring or manual review
- **High** (67–100): Block or challenge, investigate

## Project Structure

```
risk-scoring-api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app (to be built)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # Route handlers (to be built)
│   │   └── schemas.py             # Pydantic models (to be built)
│   ├── rules/                     # ✅ Complete
│   │   ├── __init__.py
│   │   ├── models.py              # RuleResult, ScoringResult
│   │   ├── engine.py              # Scoring aggregator
│   │   ├── velocity.py
│   │   ├── amount_anomaly.py
│   │   ├── impossible_travel.py
│   │   ├── high_risk_category.py
│   │   └── new_account.py
│   └── db/                        # Database layer (to be built)
│       ├── __init__.py
│       ├── models.py              # SQLAlchemy ORM models
│       ├── session.py             # DB session management
│       └── migrations/            # Alembic migrations
│
├── tests/                         # ✅ Complete
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures
│   ├── test_rules/               # 54 tests, 98.8% coverage
│   ├── test_api/                 # Integration tests (to be built)
│   └── fixtures/                 # Test data
│
├── scripts/
│   ├── seed_data.py              # Generate synthetic test data (to be built)
│
├── infra/
│   └── terraform/                # IaC for production DB (to be built)
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── .github/workflows/            # CI/CD (to be built)
│   ├── ci.yml                    # PR checks: lint, test, coverage
│   └── deploy.yml                # Main merge: test, build, push, deploy
│
├── Dockerfile                    # Container image (to be built)
├── docker-compose.yml            # Local dev stack (to be built)
├── pyproject.toml               # ✅ Project config, dependencies
└── README.md                     # This file
```

## Getting Started

### Local Development (Phase 1: Skeleton)

**Prerequisites**:
- Python 3.11+
- Docker & Docker Compose (optional, for containerized dev)

**Setup**:
```bash
git clone https://github.com/ratisapna/risk_scoring_api.git
cd risk_scoring_api
pip install -e ".[dev]"
```

**Run tests locally**:
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Run the app locally**:
```bash
# Option 1: Direct Python
uvicorn app.main:app --reload

# Option 2: Docker Compose
docker-compose up
```

Then visit `http://localhost:8000/health` — should return:
```json
{
  "status": "healthy",
  "service": "transaction-risk-scoring-api",
  "version": "0.1.0"
}
```

**Run linting**:
```bash
black app/ tests/
ruff check app/ tests/
```

## Deployment (Phase 1: Live Skeleton)

### Setup Render Account & Service

1. **Create Render account**: https://render.com (sign up with GitHub)

2. **Create new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `ratisapna/risk_scoring_api`
   - Configure:
     - **Name**: `risk-scoring-api`
     - **Region**: Your closest (e.g., us-east-1)
     - **Runtime**: Docker
     - **Build command**: `(leave empty, Dockerfile handles it)`
     - **Start command**: `(leave empty, Dockerfile handles it)`
   - Click "Create Web Service"
   
   Render will automatically:
   - Pull your code
   - Build the Docker image
   - Deploy to `https://risk-scoring-api.onrender.com`
   - Deploy takes ~2 minutes

3. **Add GitHub Secrets** (for automated deploy.yml):
   In your GitHub repo, go to **Settings → Secrets and variables → Actions**:
   - `RENDER_SERVICE_ID`: Found in Render service URL (srv-xxxxx)
   - `RENDER_DEPLOY_KEY`: From Render **Settings → Deploy Hook** (copy the key portion)
   - `RENDER_URL`: Your service URL (https://risk-scoring-api.onrender.com)

4. **Test the deployment**:
   ```bash
   curl https://risk-scoring-api.onrender.com/health
   ```
   Should return `{"status": "healthy", ...}`

### CI/CD Pipeline

Every time you push to `main`:
1. **CI workflow** runs: lint, tests, coverage checks
2. **Deploy workflow** runs if CI passes:
   - Builds Docker image
   - Triggers Render to pull latest code
   - Waits for deployment (~2 min)
   - Runs smoke test (`/health` check)
   - Notifies if deployment fails

**View workflow status**: GitHub repo → **Actions** tab

**View logs**:
- GitHub Actions: Repo → Actions → Click workflow run
- Render: Service dashboard → **Logs** tab

### Costs (Phase 1)
- **Render Web Service**: Free tier (but goes to sleep after 15 min inactivity)
- **Render Paid**: $7/month for always-on service

For portfolio: free tier is fine (you'll keep it active during interviews).

---

## Next Steps (in order)

1. **Database layer**: SQLAlchemy models, Alembic migrations, seed script
2. **API layer**: FastAPI routes, Pydantic schemas, integration tests
3. **CI/CD workflows**: GitHub Actions for PR checks and deployment
4. **Infrastructure**: Terraform for production Postgres
5. **Deployment**: Docker image, deploy to Render/Railway/Fly.io

## CI/CD Strategy

### `.github/workflows/ci.yml` (Runs on every PR)
- Checkout, Python setup, dependency cache
- Lint: `ruff check`, `black --check`
- Test: `pytest --cov` (fail if coverage < 85%)
- Data quality checks (seed data validation)
- Branch protection: PR cannot merge without passing

### `.github/workflows/deploy.yml` (Runs on merge to `main`)
- Re-run test suite
- Build Docker image
- Push to GitHub Container Registry (ghcr.io)
- Deploy to hosting platform (Render/Railway/Fly.io)
- Smoke test: curl `/health` endpoint, fail if timeout or non-200

**Why separate workflows?**
- `ci.yml` is lightweight, provides fast feedback on PRs
- `deploy.yml` is expensive (build, push, deploy), only runs on merge
- Keeps pipeline stages visible and independent
- Easier to debug and re-run individual workflows

## Test Coverage

**Rules engine**: 98.8% coverage
- Velocity check: 100% (pure function, no external dependencies)
- Amount anomaly: 94% (statistical edge cases)
- Impossible travel: 100%
- High-risk category: 100%
- New account: 100%
- Aggregator/scoring: 100%

Each rule is tested in isolation with boundary conditions, edge cases, and both triggered/non-triggered scenarios.

## Key Design Decisions

1. **Rule isolation**: Each rule is a pure function taking a transaction dict and returning a RuleResult. This makes them:
   - Testable without database or HTTP
   - Cacheable/memoizable
   - Easy to add/modify rules
   - Explainable (no hidden state or ML models)

2. **Weight-based aggregation**: Rather than threshold-based (if X rules trigger, block), we sum weights. This allows:
   - Fine-tuned risk scoring
   - Flexibility in policy (can adjust weights without retraining)
   - Clear tracing of which rules contributed to the score

3. **No ML**: Deliberately rule-based for explainability and demonstrating strong backend fundamentals.

## License

MIT (portfolio project)
