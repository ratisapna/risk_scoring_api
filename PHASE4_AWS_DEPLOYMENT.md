# Phase 4: AWS Deployment Guide

Complete guide for deploying Risk Scoring API to AWS with Terraform.

## Architecture

```
                     Internet
                        ↓
                   Route 53 (DNS)
                        ↓
            Application Load Balancer (ALB)
                        ↓
                    VPC (10.0.0.0/16)
                   ┌────────────┐
        ┌──────────┤ EC2 Public │
        │          └────────────┘
        │          (t3.micro)
        │          - Ubuntu 22.04
        │          - Docker
        │          - App runs on :8000
        │
        │          Private Subnets
        │          ┌────────────┐
        └──────────┤ RDS Private│
                   └────────────┘
                   PostgreSQL 14
                   db.t3.micro
                   Multi-AZ ready
```

## Prerequisites

✅ AWS Account with free tier eligibility
✅ AWS CLI configured (`aws configure`)
✅ Terraform installed (v1.0+)
✅ SSH key pair generated
✅ GitHub repo cloned locally

## Step 1: Generate SSH Key Pair

```bash
# On your machine (not EC2)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/risk-scoring-key -N ""

# Get the public key (you'll need this)
cat ~/.ssh/risk-scoring-key.pub
```

## Step 2: Configure Terraform Variables

Edit `infra/terraform/aws/terraform.tfvars`:

```hcl
aws_region         = "us-east-1"          # Match your AWS region
db_name            = "risk_scoring_db"
db_username        = "postgres_admin"
db_password        = "YourSecurePassword123!"  # Use strong password
ssh_public_key     = "ssh-rsa AAAA..."   # Paste output from Step 1
allowed_ssh_cidr   = ["YOUR_IP/32"]      # Your IP: find via `curl ifconfig.me`
github_repo        = "https://github.com/ratisapna/risk_scoring_api.git"
```

## Step 3: Initialize Terraform

```bash
cd infra/terraform/aws

# Initialize Terraform (downloads providers)
terraform init

# Review the plan (see what will be created)
terraform plan -out=tfplan

# Shows ~15 resources:
# - 1 VPC
# - 3 Subnets (1 public, 2 private)
# - 2 Security Groups
# - 1 RDS PostgreSQL instance
# - 1 EC2 instance
# - Internet Gateway, Route Tables, etc.
```

## Step 4: Deploy Infrastructure

```bash
# Apply the plan (creates all AWS resources)
terraform apply tfplan

# ⏱️  Wait 3-5 minutes for:
#  - RDS to initialize
#  - EC2 instance to boot
#  - Docker to build and start

# Show outputs (connection details)
terraform output
```

**Outputs will display:**
```
rds_endpoint = "risk-scoring-db.xxxxx.us-east-1.rds.amazonaws.com:5432"
ec2_public_ip = "54.xxx.xxx.xxx"
app_url = "http://54.xxx.xxx.xxx:8000"
database_url = "postgresql://postgres_admin:password@..."
```

## Step 5: Connect to EC2 and Verify

```bash
# SSH into the instance
ssh -i ~/.ssh/risk-scoring-key ubuntu@54.xxx.xxx.xxx

# On EC2, check app status
docker ps                           # See running containers
docker logs risk-scoring-api -f     # Stream app logs
curl http://localhost:8000/health   # Test health endpoint
```

## Step 6: Test API Endpoints

### Create API Key (via EC2 psql)

```bash
ssh -i ~/.ssh/risk-scoring-key ubuntu@54.xxx.xxx.xxx

# Connect to PostgreSQL
psql -h risk-scoring-db.xxxxx.rds.amazonaws.com \
     -U postgres_admin \
     -d risk_scoring_db

# In psql shell:
INSERT INTO api_keys (key, name, is_active)
VALUES ('test_key_abc123xyz', 'test_key', true);
```

### Test Score Endpoint

```bash
API_KEY="test_key_abc123xyz"
API_URL="http://54.xxx.xxx.xxx:8000"

curl -X POST $API_URL/api/v1/score \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "amount": 150.00,
    "timestamp": "2024-08-13T10:00:00",
    "merchant_category": "grocery",
    "location": "40.7128,-74.0060"
  }'
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "risk_score": 0,
  "severity": "low",
  "rules_triggered": [...],
  "user_id": "user_123",
  "amount": 150.0,
  "timestamp": "2024-08-13T10:00:00",
  "merchant_category": "grocery"
}
```

## Step 7: Monitor & Maintain

### CloudWatch Logs
```bash
# View EC2 application logs
aws logs tail /risk-scoring-api/app --follow

# View RDS activity
aws rds describe-db-instances --db-instance-identifier risk-scoring-db
```

### RDS Backups
- Automated daily backups (retention: 1 day for free tier)
- Encrypted at rest
- Manual snapshots available anytime

### Cost Monitoring
```bash
# Check free tier usage
aws ce get-cost-and-usage \
  --time-period Start=2024-08-01,End=2024-08-31 \
  --granularity DAILY \
  --metrics "UnblendedCost"
```

## Step 8: Cleanup (When Done)

⚠️ **This will DELETE all AWS resources**

```bash
cd infra/terraform/aws

# Review what will be destroyed
terraform plan -destroy

# Delete all resources
terraform destroy

# Or via AWS CLI
aws ec2 terminate-instances --instance-ids i-xxxxx
aws rds delete-db-instance --db-instance-identifier risk-scoring-db
```

## Troubleshooting

### EC2 Instance Stuck Starting
```bash
# Check instance status
aws ec2 describe-instance-status --instance-ids i-xxxxx

# View system log
aws ec2 get-console-output --instance-id i-xxxxx

# Restart if needed
aws ec2 reboot-instances --instance-ids i-xxxxx
```

### RDS Connection Failed
```bash
# Check security group
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Verify RDS is accepting connections
aws rds describe-db-instances \
  --db-instance-identifier risk-scoring-db \
  --query 'DBInstances[0].[DBInstanceStatus,MultiAZ]'
```

### Database Initialization Error
```bash
# Check EC2 logs
ssh -i ~/.ssh/risk-scoring-key ubuntu@IP
docker logs risk-scoring-api | tail -50

# Reinit database (on EC2)
docker exec risk-scoring-api \
  python -c "from app.db import Base, engine; Base.metadata.create_all(engine)"
```

## Performance Optimization (Phase 5+)

- **Add CloudFront CDN** for static assets
- **Use RDS Read Replicas** for read scaling
- **Add ElastiCache (Redis)** for caching API responses
- **Enable WAF** on ALB for DDoS protection
- **Use Route 53 Health Checks** for failover

## Cost Summary (Free Tier)

| Resource | Cost | Notes |
|----------|------|-------|
| t3.micro EC2 | $0 | 750 hours/month included |
| db.t3.micro RDS | $0 | 750 hours/month included |
| 20GB Storage | $0 | Included |
| Data Transfer | $0 | First 1GB/month out |
| **Total** | **$0** | Stay within free tier |

## Security Checklist

- [x] Security groups restrict SSH to your IP only
- [x] RDS password is strong (16+ chars, mix of types)
- [x] Database backups enabled
- [x] Encryption at rest enabled
- [x] Monitoring via CloudWatch
- [ ] Add WAF rules (Phase 5)
- [ ] Enable VPC Flow Logs (Phase 5)
- [ ] Use AWS Secrets Manager for secrets (Phase 5)

## Next: CI/CD Pipeline for AWS

To auto-deploy to AWS on git push:

1. Create IAM user with Terraform permissions
2. Add AWS credentials to GitHub Secrets
3. Create `.github/workflows/deploy-aws.yml`:
   - Run `terraform init`
   - Run `terraform apply`
   - Smoke test the live API

This makes Phase 4 fully automated! 🚀
