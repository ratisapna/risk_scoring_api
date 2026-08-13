# Project Strategy: Build → Deploy → Iterate with AWS Integration

This document answers your key questions:
1. **Where does AWS fit and when?**
2. **How do we manage security across phases?**
3. **What's the full timeline?**
4. **How does CI/CD work end-to-end?**

---

## Overall Architecture & Timeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: SKELETON (Week 1)                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ /health endpoint                                                       │
│ ✓ Docker containerization                                               │
│ ✓ GitHub Actions CI/CD pipeline                                        │
│ ✓ Render deployment (free tier)                                        │
│ ✗ Database: Not yet needed (no data endpoints)                         │
│ ✗ AWS: Not needed                                                       │
│ ✗ Security: Basic (HTTPS only, via Render)                            │
│                                                                         │
│ Result: Live API at https://risk-scoring-api.onrender.com/health       │
│ Time: 1-2 hours build + 30 min setup Render                            │
│ Cost: $0/month                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: CORE API + DATABASE (Week 2-3)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ POST /score endpoint (rules engine integration)                      │
│ ✓ GET /transactions with filtering                                     │
│ ✓ GET /transactions/{id}                                               │
│ ✓ SQLAlchemy ORM models                                                │
│ ✓ Alembic migrations (schema versioning)                               │
│ ✓ SQLite database (local file, Render filesystem)                      │
│ ✓ Request validation & error handling                                  │
│ ✗ AWS: Still not needed                                                │
│ ✗ Security: API keys (basic, in Phase 3)                               │
│                                                                         │
│ Result: Live scoring API with data persistence                         │
│ Deploy: Automatic (GitHub Actions → Render)                            │
│ Time: 4-6 hours build                                                  │
│ Cost: $0/month (or $7/month for always-on)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: SECURITY & HARDENING (Week 4)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ API key authentication                                               │
│ ✓ Rate limiting (per-key)                                              │
│ ✓ Request validation & sanitization                                    │
│ ✓ CORS configuration                                                   │
│ ✓ Request/response logging                                             │
│ ✓ Error handling (no stack traces in responses)                        │
│ ✓ Secrets management (GitHub Secrets for deploy keys)                  │
│ ✗ AWS: Still not needed for deployed app                              │
│ ✗ AWS: BUT start AWS account & familiarize yourself                   │
│                                                                         │
│ Result: Hardened API, production-ready                                 │
│ Deploy: Automatic                                                      │
│ Time: 3-4 hours                                                        │
│ Cost: $0-7/month (Render)                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: INFRASTRUCTURE-AS-CODE & AWS MIGRATION (Week 5)              │
├─────────────────────────────────────────────────────────────────────────┤
│ ✓ AWS Account setup                                                     │
│ ✓ Terraform configuration for RDS Postgres                            │
│ ✓ Terraform configuration for EC2 (or ECS)                            │
│ ✓ GitHub Actions secrets for AWS credentials                          │
│ ✓ Migrate from Render to AWS deployment                               │
│ ✓ AWS Secrets Manager for sensitive data                              │
│ ✓ Security groups & network configuration                             │
│ ✓ IAM roles & least-privilege access                                  │
│                                                                         │
│ Result: Production-grade infrastructure via code                       │
│ Deploy: terraform apply → GitHub Actions → ECR → ECS/EC2             │
│ Time: 4-6 hours build + 1 hour AWS setup                              │
│ Cost: Free tier (12 months) then ~$15-20/month                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AWS: Why, When, and How

### Why AWS?

1. **Portfolio value**: Shows you can use production infrastructure, Terraform, IaC
2. **Scalability**: Unlike Render, you can grow to auto-scaling, load balancing
3. **Security**: AWS IAM, VPCs, security groups (real enterprise patterns)
4. **Interview talking points**: "I managed infrastructure as code, deployed to AWS RDS and ECS..."

### When to Create AWS Account?

**Phase 3 (Security phase)**: Start familiarizing yourself, but don't migrate yet.

**Phase 4**: Build infrastructure in AWS, then migrate.

**Don't do it in Phase 1** — adds complexity, no benefit yet (SQLite works fine).

### AWS Setup Timeline

| Task | Time | Complexity |
|---|---|---|
| Create AWS account | 5 min | Easy |
| Create IAM user for Terraform | 10 min | Easy |
| Write RDS Terraform | 30 min | Medium |
| Write EC2/ECS Terraform | 1 hour | Medium |
| First `terraform apply` | 5 min | Easy |
| Debug networking issues | 30-60 min | Hard (if needed) |

### AWS Phase 4 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      AWS Account                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐        ┌──────────────────────────┐     │
│  │   GitHub Actions │        │   VPC (Private)          │     │
│  │                 │────────▶│   ├─ EC2 Instance       │     │
│  │ 1. Test         │        │   │   (Docker FastAPI)  │     │
│  │ 2. Build Docker │        │   │                      │     │
│  │ 3. Push to ECR  │        │   └─ RDS Postgres      │     │
│  │ 4. Deploy to ECS│        │      (encrypted)        │     │
│  └─────────────────┘        │                         │     │
│                             │  Security Groups        │     │
│  ┌─────────────────┐        │  ├─ EC2: Allow 22, 8000 │     │
│  │  Terraform State│        │  └─ RDS: Allow 5432     │     │
│  │  (S3 + DynamoDB)│        │  IAM Roles (least priv) │     │
│  └─────────────────┘        │  CloudWatch Logs        │     │
│                             └──────────────────────────┘     │
│                                                               │
│  Secrets (AWS Secrets Manager):                            │
│  ├─ DB password                                            │
│  ├─ API keys                                               │
│  └─ Third-party service creds                              │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Security by Phase

### Phase 1: Skeleton
**What's secure**:
- ✓ HTTPS enforced (Render handles)
- ✓ Code on GitHub (public is fine, no secrets)

**What's not yet**:
- ⚠️ No authentication (anyone can call `/health`)
- ⚠️ No rate limiting (DDoS possible, but trivial endpoint)
- ⚠️ No input validation (not applicable yet)

**Action**: None needed. `/health` is meant to be public.

---

### Phase 2: Core API
**What to add**:
- ✓ Input validation on `/score` (user_id, amount must be valid)
- ✓ Catch and log errors (don't expose stack traces)
- ⚠️ Still no authentication (anyone can score transactions)

**Security checklist**:
- Validate: `amount > 0`, `timestamp` is ISO8601, `location` is lat,lon
- Validate: `user_id` is alphanumeric (prevent SQL injection via URL)
- Catch exceptions: Return 400/500 not 500 with traceback
- Add request logging: Log all API calls for audit trail

**Example**:
```python
@app.post("/score")
async def score_transaction(request: ScoringRequest):
    try:
        # Validate input
        if request.amount <= 0:
            raise ValueError("amount must be positive")
        
        # Call rules engine
        result = score_transaction(request.dict())
        return result.to_dict()
    except ValueError as e:
        raise HTTPException(400, f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        raise HTTPException(500, "Internal server error")
```

**Cost**: $0 (no additional infrastructure)

---

### Phase 3: Hardening
**What to add**:
- ✓ API key authentication
- ✓ Rate limiting
- ✓ CORS restrictions
- ✓ Request signing (optional)

**Implementation**:
```python
# In app/api/auth.py
def verify_api_key(api_key: str = Header(...)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(401, "Invalid API key")
    return api_key

# In routes
@app.post("/score")
async def score_transaction(
    request: ScoringRequest,
    api_key: str = Depends(verify_api_key),
):
    # API key verified, proceed with scoring
    pass
```

**Rate limiting** (using `slowapi`):
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_api_key)

@app.post("/score")
@limiter.limit("100/minute")
async def score_transaction(...):
    pass
```

**Cost**: $0 (libraries are free)

---

### Phase 4: AWS Security
**What to add**:
- ✓ AWS IAM: Least-privilege roles for EC2, RDS
- ✓ VPC: Private subnet for RDS, restrict inbound
- ✓ Security groups: Only allow necessary ports
- ✓ Secrets Manager: Rotate DB password, API keys
- ✓ Encryption: RDS encryption at rest
- ✓ Audit logs: CloudWatch, CloudTrail

**Example Terraform**:
```hcl
# EC2 security group: allow web traffic + SSH
resource "aws_security_group" "api" {
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Web traffic
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]  # SSH from your IP only
  }
}

# RDS security group: only allow from EC2
resource "aws_security_group" "db" {
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]  # Only from API
  }
}

# Secrets Manager for DB password
resource "aws_secretsmanager_secret" "db_password" {
  name = "risk-scoring-db-password"
}

# RDS with encryption
resource "aws_db_instance" "postgres" {
  identifier            = "risk-scoring-db"
  engine                = "postgres"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.db.arn
  db_subnet_group_name  = aws_db_subnet_group.private.name
  vpc_security_group_ids = [aws_security_group.db.id]
}
```

**Cost**: Free tier (12 months), then ~$15-20/month

---

## CI/CD Workflow Summary

### Phase 1-2: GitHub Actions + Render
```
GitHub (master branch)
    ↓
Trigger GitHub Actions
    ├─ Lint & Test (ruff, black, pytest)
    ├─ Build Docker image
    └─ Call Render deploy hook
        ↓
    Render detects new push
        ├─ Pull latest code
        ├─ Build Docker image
        ├─ Start container
        └─ Health check
            ↓
        Live at https://risk-scoring-api.onrender.com
```

**Time**: ~3-5 minutes

---

### Phase 4: GitHub Actions + AWS ECR/ECS
```
GitHub (master branch)
    ↓
Trigger GitHub Actions
    ├─ Lint & Test
    ├─ Build Docker image
    ├─ Push to AWS ECR (Elastic Container Registry)
    └─ Trigger ECS deployment
        ↓
    AWS ECS detects new image
        ├─ Pull image from ECR
        ├─ Kill old container
        ├─ Start new container
        ├─ Update load balancer
        └─ Health check
            ↓
        Live at https://api.example.com (via Route53)
```

**Time**: ~5-7 minutes (slightly slower due to ECR push)

---

## Decision: Render vs AWS

| Factor | Render (Phase 1-3) | AWS (Phase 4) |
|---|---|---|
| **Cost** | $0-7/month | Free tier, then $15-20/month |
| **Setup time** | 30 min | 2-3 hours |
| **Infrastructure as Code** | No | Yes (Terraform) |
| **Portfolio value** | Good | Excellent |
| **Scalability** | Limited | Unlimited |
| **Security** | Good | Enterprise-grade |

**Recommendation**: 
1. **Use Render for Phase 1-3** (fast, free, keeps focused on code)
2. **Migrate to AWS Phase 4** (shows IaC mastery, interview impact)

---

## Your Full Interview Narrative

**"I built a transaction risk-scoring API using a build-deploy-iterate approach:**

**Phase 1**: Containerized the app with Docker and set up automated CI/CD. Every push to `main` triggers GitHub Actions to lint, test, and deploy to Render. The `/health` endpoint is live within minutes.

**Phase 2**: Implemented the core scoring endpoints backed by SQLAlchemy and SQLite. The rules engine (velocity, amount anomaly, impossible travel, high-risk category, new account) is tested at 98% coverage.

**Phase 3**: Hardened the API with authentication (API keys), rate limiting, input validation, and error handling. All deployment secrets are managed via GitHub Secrets.

**Phase 4**: Migrated to AWS using Terraform. I provisioned RDS Postgres (with encryption and private subnet), EC2 for the app, and security groups for least-privilege access. Infrastructure is versioned alongside code, with state managed in S3.

The whole pipeline is automated: commit → tests → build → deploy. Each phase took 1-2 weeks, deployed live from day one."**

---

## Next Steps

1. **Phase 1 (THIS WEEK)**:
   - ✓ Push code to GitHub
   - ✓ Create Render account
   - ✓ Deploy `/health` skeleton
   - ✓ Verify CI/CD pipeline works

2. **Phase 2 (NEXT WEEK)**:
   - Build POST /score endpoint
   - Add SQLAlchemy models
   - Deploy automatically via GitHub Actions

3. **Phase 3 (WEEK AFTER)**:
   - Add API key auth + rate limiting
   - Hardening review

4. **Phase 4 (WEEK 4)**:
   - Create AWS account
   - Write Terraform
   - Migrate to AWS
   - Update deploy workflow

---

See `DEPLOY.md` for step-by-step Render deployment instructions.
