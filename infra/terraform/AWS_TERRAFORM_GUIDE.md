# AWS Terraform Deployment Guide

This guide walks you through deploying your Transaction Risk Scoring API to AWS using Terraform.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS Account                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  VPC (10.0.0.0/16)                                  │   │
│  │  ├─ Public Subnet (10.0.1.0/24)                     │   │
│  │  │  └─ EC2 Instance (t3.micro, Ubuntu)             │   │
│  │  │     └─ Elastic IP: 3.x.x.x                      │   │
│  │  │        └─ Docker Container: FastAPI on :8000    │   │
│  │  │                                                  │   │
│  │  ├─ Private Subnet 1 (10.0.2.0/24)                │   │
│  │  │  └─ RDS Postgres (db.t3.micro)                  │   │
│  │  └─ Private Subnet 2 (10.0.3.0/24)                │   │
│  │     └─ RDS Replica (for HA)                        │   │
│  │                                                    │   │
│  │  Security Groups:                                 │   │
│  │  ├─ EC2-SG: Allow 80, 443, 8000, 22              │   │
│  │  └─ RDS-SG: Allow 5432 only from EC2-SG          │   │
│  │                                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  CloudWatch Logs (PostgreSQL)                             │
│  IAM Roles (least privilege)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

✓ AWS Account created
✓ IAM user `terraform-deploy` with credentials
✓ Terraform installed locally
✓ AWS CLI configured with credentials

If missing any of these, see main AWS setup section above.

---

## Step 1: Prepare SSH Key

You need an SSH key to access the EC2 instance.

### Generate SSH Key (if you don't have one)

**On Windows PowerShell**:
```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\risk-scoring-key" -N ""
```

This creates:
- **Private key**: `C:\Users\ratis\.ssh\risk-scoring-key` (keep secret!)
- **Public key**: `C:\Users\ratis\.ssh\risk-scoring-key.pub` (goes in Terraform)

View the public key:
```powershell
Get-Content $env:USERPROFILE\.ssh\risk-scoring-key.pub
# Output: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
```

---

## Step 2: Create terraform.tfvars

In `infra/terraform/aws/`:

```powershell
cd C:\Users\ratis\Desktop\risk\infra\terraform\aws
Copy-Item terraform.tfvars.example terraform.tfvars
```

Now edit `terraform.tfvars`:

```hcl
aws_region = "us-east-1"

db_name     = "risk_scoring_db"
db_username = "risk_admin"
db_password = "YourSecurePassword123!!"  # Change this to something strong

ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... (your key from Step 1)"

# IMPORTANT: Change this to your IP for security!
# Find your IP: curl https://ifconfig.me
allowed_ssh_cidr = ["203.0.113.45/32"]  # Example: your IP

github_repo = "https://github.com/ratisapna/risk_scoring_api.git"
```

**⚠️ IMPORTANT**: Add `terraform.tfvars` to `.gitignore` (it already is by default)

---

## Step 3: Initialize Terraform

```powershell
cd C:\Users\ratis\Desktop\risk\infra\terraform\aws

# Download Terraform providers
terraform init
```

Expected output:
```
Terraform has been successfully configured!
```

---

## Step 4: Plan the Deployment

```powershell
terraform plan -out=tfplan
```

This shows what Terraform will create:
- 1 VPC
- 3 Subnets
- 2 Security Groups
- 1 RDS Instance
- 1 EC2 Instance
- 1 Elastic IP
- 1 IAM Key Pair

**Review the output carefully**. It should show ~15 resources being created.

If you see any errors, fix them before proceeding.

---

## Step 5: Apply Terraform

```powershell
terraform apply tfplan
```

**Wait 5-10 minutes** for AWS to provision everything.

You'll see output like:
```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

app_url = "http://3.x.x.x:8000"
ec2_instance_id = "i-0123456789abcdef0"
health_check_url = "http://3.x.x.x:8000/health"
rds_address = "risk-scoring-db.xxxxx.us-east-1.rds.amazonaws.com"
```

**Save these outputs!** You'll need them.

---

## Step 6: Test the Deployment

### Wait for EC2 to be ready
The EC2 instance runs `user_data.sh` on startup, which:
- Installs Docker
- Clones your GitHub repo
- Builds and starts the app

This takes ~3-5 minutes. Check progress in AWS Console:

1. Go to **EC2** → **Instances**
2. Click your instance
3. Go to **Status checks** tab
4. Wait for both checks to show ✓ Green

### Test the Health Endpoint

Once EC2 is healthy:

```powershell
# Replace with your actual public IP from terraform output
curl http://3.x.x.x:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "transaction-risk-scoring-api",
  "version": "0.1.0"
}
```

✓ **Congratulations! Your app is live on AWS!**

---

## Step 7: SSH into EC2 (Optional)

To debug or check logs:

```powershell
ssh -i "$env:USERPROFILE\.ssh\risk-scoring-key" ubuntu@3.x.x.x
```

Inside the instance:
```bash
# View Docker logs
docker logs risk-scoring-api -f

# Check if app is running
docker ps

# View environment variables
cat .env

# Restart the app
docker restart risk-scoring-api
```

---

## Step 8: Monitor in AWS Console

### Check RDS Database
1. Go to **RDS** → **Databases**
2. Click `risk-scoring-db`
3. Verify **Status**: `available`
4. Note the **Endpoint**: This is your database host

### Check EC2 Instance
1. Go to **EC2** → **Instances**
2. Click your instance
3. Verify **Status**: `running`
4. Note **Public IPv4 address**: This is your app URL

### View CloudWatch Logs
1. Go to **CloudWatch** → **Log groups**
2. Find `/aws/rds/instance/risk-scoring-db/postgresql`
3. View database logs

---

## Step 9: Update GitHub Actions (Optional)

To automate deployment on push to `main`:

Edit `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: pip install -e ".[dev]" && pytest tests/
      
      - name: SSH and deploy
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.AWS_EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.AWS_SSH_KEY }}
          script: |
            cd /opt/risk_scoring_api
            git pull origin main
            docker build -t risk-scoring-api .
            docker stop risk-scoring-api || true
            docker rm risk-scoring-api || true
            docker run -d \
              --name risk-scoring-api \
              -p 8000:8000 \
              --restart unless-stopped \
              --env-file .env \
              risk-scoring-api
```

Add to GitHub Secrets:
- `AWS_EC2_HOST`: Your Elastic IP (from terraform output)
- `AWS_SSH_KEY`: Contents of your private key file

---

## Troubleshooting

### "terraform apply" fails with "Access Denied"
- Check AWS credentials: `aws sts get-caller-identity`
- Verify IAM user has required permissions
- Ensure `terraform.tfvars` has correct credentials

### EC2 Status checks failing
1. Go to **EC2** → Click instance
2. Click **Status checks** tab
3. Wait 5 more minutes (still initializing)
4. If still failing, check **System log** for errors

### App not responding at health endpoint
1. SSH into EC2: `ssh -i your-key ubuntu@3.x.x.x`
2. Check Docker: `docker ps`
3. View logs: `docker logs risk-scoring-api`
4. Common issues:
   - Database connection failed → Check DB password in `.env`
   - Port in use → Kill process on port 8000
   - Out of memory → Restart instance

### Can't SSH into EC2
- Verify Security Group allows port 22 from your IP
- Check key pair name: `aws ec2 describe-key-pairs`
- Ensure private key has correct permissions: `chmod 400 risk-scoring-key`

---

## Costs

**Free Tier (12 months)**:
- ✓ EC2 t3.micro: 750 hours/month (free tier)
- ✓ RDS db.t3.micro: Free tier eligible
- ✓ Data transfer: ~1GB/month (free)
- **Total**: $0/month

**After Free Tier**:
- EC2 t3.micro: ~$7/month
- RDS db.t3.micro: ~$25/month
- Data transfer: ~$0.09/GB
- **Total**: ~$32/month (rough estimate)

**To reduce costs after free tier**:
- Downgrade to t2.micro if available
- Use RDS MariaDB instead of Postgres (~$10/month cheaper)
- Set up auto-shutdown during off-hours

---

## Cleanup (Delete Resources)

**⚠️ WARNING**: This deletes everything (RDS data, EC2, VPC)

```powershell
terraform destroy
```

Type `yes` to confirm. This takes ~5 minutes.

---

## Next Steps

1. **Phase 2**: Implement `/score` endpoint + database models
2. **Phase 3**: Add API key auth + rate limiting
3. **Set up monitoring**: CloudWatch alarms, health checks
4. **Set up backups**: RDS automated backups (already enabled)
5. **Automate deployments**: Update GitHub Actions

---

## Interview Talking Points

*"I used Terraform to provision a production-grade AWS infrastructure for my API. The configuration creates a VPC with public and private subnets, an EC2 instance with Docker, and a managed RDS Postgres database with encryption and automated backups. The security groups follow the principle of least privilege—the app communicates with the database through a security group, SSH is restricted to my IP, and the database is in a private subnet. The whole infrastructure is version-controlled and reproducible: I can destroy and recreate it with a single `terraform apply` command."*

---

See `STRATEGY.md` for overall project roadmap.
