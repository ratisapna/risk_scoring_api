#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y docker.io docker-compose git curl

# Start Docker
systemctl start docker
systemctl enable docker

# Clone the repository
cd /opt
git clone ${github_repo}
cd risk_scoring_api

# Set environment variables for the app
cat > .env << EOF
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:${db_port}/${db_name}
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Build and start the Docker container
docker build -t risk-scoring-api .
docker run -d \
  --name risk-scoring-api \
  -p 8000:8000 \
  --restart unless-stopped \
  --env-file .env \
  risk-scoring-api

# Verify the app is running
sleep 5
if curl -f http://localhost:8000/health; then
  echo "✓ App is running and healthy"
else
  echo "✗ Health check failed"
  docker logs risk-scoring-api
  exit 1
fi
