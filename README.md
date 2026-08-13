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

## Getting Started (Scaffolding Phase)

### Prerequisites
- Python 3.11+
- pip / poetry

### Install Dependencies
```bash
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/test_rules/ -v --cov=app --cov-report=term-missing
```

Expected output:
```
54 passed in ~2s, coverage: 98.8% (rules engine fully covered)
```

### Run Linting
```bash
black --check app/
ruff check app/
```

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
