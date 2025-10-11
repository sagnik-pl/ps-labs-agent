# Deployment Plan
## ps-labs-agent Multi-Agent Analytics System

**Last Updated**: 2025-10-06
**Status**: Draft
**Target Environment**: Production (www.photospherelabs.com)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Deployment Requirements](#deployment-requirements)
3. [Platform Options](#platform-options)
4. [Recommended Architecture](#recommended-architecture)
5. [Pre-Deployment Checklist](#pre-deployment-checklist)
6. [Deployment Steps](#deployment-steps)
7. [Environment Configuration](#environment-configuration)
8. [Security Hardening](#security-hardening)
9. [Monitoring & Logging](#monitoring--logging)
10. [CI/CD Pipeline](#cicd-pipeline)
11. [Scaling Strategy](#scaling-strategy)
12. [Disaster Recovery](#disaster-recovery)
13. [Cost Estimates](#cost-estimates)

---

## Architecture Overview

### Current System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vercel)                        │
│                  ps-labs-app (React/Vite)                    │
│                 www.photospherelabs.com                      │
└────────────────────────┬─────────────────────────────────────┘
                         │ WebSocket (wss://)
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (Needs Deployment)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  FastAPI + WebSocket Server (api_websocket.py)     │    │
│  │  - Port 8000                                       │    │
│  │  - Persistent connections (10s-60s+)               │    │
│  │  - Real-time streaming responses                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Multi-Agent Workflow (LangGraph)                  │    │
│  │  - Planner → Router → Agents → Validators          │    │
│  │  - SQL Generator → Athena → Data Interpreter       │    │
│  └────────────────────────────────────────────────────┘    │
└────────────────┬──────────────┬─────────────┬───────────────┘
                 │              │             │
                 ▼              ▼             ▼
        ┌─────────────┐  ┌──────────┐  ┌────────────┐
        │   Firebase  │  │   AWS    │  │  OpenAI    │
        │  Firestore  │  │  Athena  │  │    API     │
        │             │  │  Secrets │  │            │
        │ (Convos)    │  │  Manager │  │  (LLM)     │
        └─────────────┘  └──────────┘  └────────────┘
```

### What Needs to Be Deployed

1. **WebSocket API Server** (`api_websocket.py`)
   - Handles real-time chat connections
   - Routes to multi-agent workflow
   - Streams progress updates
   - Manages conversation metadata

2. **Agent Workflow System**
   - LangGraph orchestration
   - SQL generation & validation
   - Data interpretation
   - Context management

3. **Dependencies**
   - Python 3.12 runtime
   - 25+ Python packages (see requirements.txt)
   - Environment variables
   - Secret management

---

## Deployment Requirements

### Runtime Requirements

| Requirement | Specification | Reason |
|------------|---------------|---------|
| **Runtime** | Python 3.12+ | LangChain/LangGraph compatibility |
| **Memory** | 1GB minimum, 2GB recommended | LLM processing, concurrent users |
| **CPU** | 1 vCPU minimum, 2+ recommended | Agent workflow execution |
| **Storage** | 10GB minimum | Dependencies, logs, cache |
| **Network** | Persistent connections required | WebSocket support (NOT serverless) |
| **Uptime** | 99.9% SLA | Production chat application |

### External Dependencies

| Service | Purpose | Required Credentials |
|---------|---------|---------------------|
| **Firebase** | Conversation storage | Service account JSON (via AWS Secrets) |
| **AWS Athena** | Data queries | IAM role or access keys |
| **AWS Secrets Manager** | Firebase credentials | IAM permissions |
| **OpenAI API** | LLM inference | API key |

### Network Requirements

| Direction | Protocol | Port | Purpose |
|-----------|----------|------|---------|
| Inbound | HTTPS | 443 | REST API |
| Inbound | WSS | 443 | WebSocket connections |
| Outbound | HTTPS | 443 | Firebase, AWS, OpenAI |

---

## Platform Options

### Option 1: Railway ⭐ RECOMMENDED

**Pros:**
- ✅ WebSocket support out-of-the-box
- ✅ Simple deployment (Git push to deploy)
- ✅ Built-in environment variable management
- ✅ Auto-scaling support
- ✅ Free SSL certificates
- ✅ Good monitoring dashboard
- ✅ Competitive pricing (~$5-20/month)

**Cons:**
- ❌ Smaller company (stability concerns)
- ❌ Limited advanced features vs AWS

**Best For:** Quick production deployment, small-medium scale

### Option 2: Render

**Pros:**
- ✅ WebSocket support
- ✅ Free tier available
- ✅ Simple deployment
- ✅ Auto-scaling
- ✅ Good documentation

**Cons:**
- ❌ Free tier has cold starts
- ❌ Paid tier similar cost to Railway

**Best For:** Testing, small scale deployments

### Option 3: AWS ECS/Fargate

**Pros:**
- ✅ Enterprise-grade reliability
- ✅ Already using AWS (Athena, Secrets Manager)
- ✅ Fine-grained control
- ✅ Advanced networking options
- ✅ Excellent monitoring (CloudWatch)

**Cons:**
- ❌ Complex setup and configuration
- ❌ Higher operational overhead
- ❌ More expensive (~$30-50/month minimum)

**Best For:** Enterprise deployments, high scale, complex requirements

### Option 4: Google Cloud Run

**Pros:**
- ✅ Serverless with WebSocket support (newer feature)
- ✅ Pay per use
- ✅ Auto-scaling

**Cons:**
- ❌ WebSocket support still maturing
- ❌ Complexity in setup
- ❌ Not already using GCP services

**Best For:** Google Cloud ecosystem users

### ❌ NOT RECOMMENDED

| Platform | Reason |
|----------|--------|
| **Vercel** | WebSocket timeout (10s max), serverless limitations |
| **Netlify** | No WebSocket support for serverless |
| **AWS Lambda** | 15-minute timeout, WebSocket complexity |
| **Heroku** | Expensive, company stability concerns |

---

## Recommended Architecture

### Phase 1: Railway Deployment (Immediate)

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Vercel)                                   │
│  https://www.photospherelabs.com                    │
└────────────────────────┬─────────────────────────────┘
                         │
                         │ wss://api.photospherelabs.com
                         ▼
┌─────────────────────────────────────────────────────┐
│  Railway Service                                     │
│  ┌────────────────────────────────────────────┐    │
│  │  Docker Container                           │    │
│  │  - Python 3.12                             │    │
│  │  - FastAPI + Uvicorn                       │    │
│  │  - Auto-scaling (1-3 instances)            │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  Environment Variables (Railway Secrets)             │
│  - OPENAI_API_KEY                                   │
│  - AWS_ACCESS_KEY_ID                                │
│  - AWS_SECRET_ACCESS_KEY                            │
│  - FIREBASE_SECRET_NAME                             │
└─────────────────────────────────────────────────────┘
```

**Benefits:**
- Quick deployment (1-2 hours)
- Low operational overhead
- Cost-effective
- Production-ready

### Phase 2: AWS ECS (Future Scale)

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│  Route 53 + CloudFront                              │
│  api.photospherelabs.com                            │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Application Load Balancer (ALB)                    │
│  - SSL Termination                                  │
│  - WebSocket support                                │
│  - Health checks                                    │
└────────────────────────┬─────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  ECS Fargate Service                                │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   Task 1     │  │   Task 2     │                │
│  │  Container   │  │  Container   │  Auto-scaling  │
│  └──────────────┘  └──────────────┘                │
│                                                      │
│  - IAM Role for AWS access                          │
│  - Secrets from Secrets Manager                     │
│  - CloudWatch Logs                                  │
└─────────────────────────────────────────────────────┘
```

**Benefits:**
- Enterprise-grade reliability
- Advanced monitoring
- VPC isolation
- IAM-based security

**When to Migrate:**
- >1000 concurrent users
- Need advanced networking
- Compliance requirements
- Budget allows (~$50-100/month)

---

## Pre-Deployment Checklist

### ✅ Security (CRITICAL - Must Complete First)

**All security tasks tracked in Jira**: https://photospherelabs.atlassian.net/browse/PSAG

**Priority P0 Tasks** (see Jira for full details):
- PSAG-8: [SEC-001] Rotate all exposed API keys and AWS credentials
- PSAG-9: [SEC-002] Implement JWT authentication on WebSocket
- PSAG-10: [SEC-003] Add authentication to REST endpoints
- PSAG-11: [SEC-013] Secure Railway production deployment

**Priority P1 Tasks**:
- PSAG-12: [SEC-004] Fix CORS configuration
- PSAG-16: [SEC-008] Remove hardcoded AWS credentials

**View all security tasks**: `project = PSAG AND labels = security`

### ✅ Code Quality

**Code quality tasks tracked in Jira**: https://photospherelabs.atlassian.net/browse/PSAG

**Key Tasks**:
- PSAG-20: [QUAL-002] Replace print statements with proper logging
- PSAG-19: [QUAL-001] Refactor error handling

**View all quality tasks**: `project = PSAG AND labels = quality`

### ✅ Configuration

- [ ] Create `.env.production` template
- [ ] Document all required environment variables
- [ ] Set up secrets management strategy
- [ ] Configure different settings for dev/staging/prod

### ✅ Testing

- [ ] Test WebSocket connection locally
- [ ] Test all API endpoints
- [ ] Verify Firebase connectivity
- [ ] Verify AWS Athena queries work
- [ ] Test with real OpenAI API calls
- [ ] Load test (at least 10 concurrent users)

### ✅ Infrastructure

- [ ] Choose deployment platform (Railway recommended)
- [ ] Set up custom domain (api.photospherelabs.com)
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Configure CDN if needed

### ✅ Monitoring

- [ ] Set up error tracking (Sentry recommended)
- [ ] Configure logging aggregation
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Create alerts for critical failures
- [ ] Set up cost alerts for AWS/OpenAI

---

## Deployment Steps

### Railway Deployment (Recommended)

#### Step 1: Prepare Repository

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/')"

# Run application
CMD ["uvicorn", "api_websocket:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create .dockerignore
cat > .dockerignore << 'EOF'
.env
.env.*
__pycache__
*.pyc
*.pyo
*.pyd
.Python
agent_venv/
venv/
.git
.gitignore
*.md
tests/
test_*.py
.pytest_cache
.coverage
*.log
EOF

# Create railway.json for configuration
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
```

#### Step 2: Create Railway Project

1. **Sign up for Railway**
   - Go to https://railway.app
   - Sign in with GitHub
   - Connect your repository

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # Initialize project
   railway init

   # Link to repository
   railway link
   ```

3. **Configure Environment Variables**
   ```bash
   # Set environment variables via CLI
   railway variables set ENVIRONMENT=production
   railway variables set OPENAI_API_KEY=<new-key>
   railway variables set AWS_ACCESS_KEY_ID=<new-key>
   railway variables set AWS_SECRET_ACCESS_KEY=<new-secret>
   railway variables set AWS_REGION=us-east-1
   railway variables set FIREBASE_SECRET_NAME=<secret-name>
   railway variables set GLUE_DATABASE=<db-name>
   railway variables set ATHENA_S3_OUTPUT_LOCATION=<s3-path>

   # Or set via Railway dashboard
   # https://railway.app/project/<project-id>/settings
   ```

#### Step 3: Deploy

```bash
# Deploy from CLI
railway up

# Or push to GitHub (auto-deploys if connected)
git push origin main

# Monitor deployment
railway logs
```

#### Step 4: Configure Custom Domain

1. **Add Domain in Railway Dashboard**
   - Go to Settings → Domains
   - Add `api.photospherelabs.com`
   - Copy CNAME record

2. **Update DNS**
   ```
   Type: CNAME
   Name: api
   Value: <railway-provided-domain>.railway.app
   TTL: 300
   ```

3. **Wait for SSL**
   - Railway auto-provisions SSL (Let's Encrypt)
   - Usually takes 5-10 minutes

#### Step 5: Update Frontend

Update frontend to point to new API:

```typescript
// In ps-labs-app repo
const WEBSOCKET_URL = import.meta.env.PROD
  ? 'wss://api.photospherelabs.com'
  : 'ws://localhost:8000';
```

#### Step 6: Test Production

```bash
# Test health endpoint
curl https://api.photospherelabs.com/

# Test WebSocket (use tool like wscat)
npm install -g wscat
wscat -c wss://api.photospherelabs.com/ws/test-user/test-session

# Test from frontend
# Visit www.photospherelabs.com and try chat
```

### AWS ECS Deployment (Advanced)

See [AWS ECS Deployment Guide](#aws-ecs-deployment-guide) section below for detailed steps.

---

## Environment Configuration

### Environment Variables

Create environment-specific configuration:

#### Production (.env.production)

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# OpenAI
OPENAI_API_KEY=<production-key>

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<iam-user-key>
AWS_SECRET_ACCESS_KEY=<iam-secret>

# AWS Resources
GLUE_DATABASE=photosphere_production
ATHENA_S3_OUTPUT_LOCATION=s3://photosphere-athena-results/production/
FIREBASE_SECRET_NAME=photosphere/firebase/production

# API Configuration
CORS_ORIGINS=https://www.photospherelabs.com,https://photospherelabs.com
API_RATE_LIMIT=100/minute

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=<sentry-dsn>
```

#### Staging (.env.staging)

```bash
ENVIRONMENT=staging
DEBUG=false
OPENAI_API_KEY=<staging-key>
AWS_REGION=us-east-1
GLUE_DATABASE=photosphere_staging
ATHENA_S3_OUTPUT_LOCATION=s3://photosphere-athena-results/staging/
FIREBASE_SECRET_NAME=photosphere/firebase/staging
CORS_ORIGINS=https://staging.photospherelabs.com
LOG_LEVEL=DEBUG
```

### Secrets Management

#### Railway Secrets (Recommended for Railway)

```bash
# Set via CLI
railway variables set OPENAI_API_KEY=<key> --environment production

# Or via Dashboard
# Project → Environment Variables → Add Variable
```

#### AWS Secrets Manager (For ECS)

```bash
# Create secret
aws secretsmanager create-secret \
  --name photosphere/backend/production \
  --secret-string '{
    "OPENAI_API_KEY": "<key>",
    "AWS_ACCESS_KEY_ID": "<key>",
    "AWS_SECRET_ACCESS_KEY": "<secret>"
  }'

# Reference in ECS task definition
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:photosphere/backend/production:OPENAI_API_KEY::"
    }
  ]
}
```

---

## Security Hardening

### Pre-Deployment Security Checklist

Based on [vulns_and_issues.md](vulns_and_issues.md):

#### 1. Credential Rotation (CRITICAL)

```bash
# Generate new OpenAI API key
# https://platform.openai.com/api-keys

# Create new AWS IAM user with minimal permissions
aws iam create-user --user-name photosphere-backend-prod

# Attach minimal policy (see athena-policy.json)
aws iam attach-user-policy \
  --user-name photosphere-backend-prod \
  --policy-arn arn:aws:iam::123456789:policy/PhotosphereAthenaAccess

# Generate new access keys
aws iam create-access-key --user-name photosphere-backend-prod

# Revoke old credentials
aws iam delete-access-key --user-name old-user --access-key-id <old-key>
```

#### 2. Authentication Implementation

```python
# Add to api_websocket.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and extract user_id."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Update WebSocket endpoint
@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    token: str = Query(...)  # Get token from query param
):
    # Verify token
    authenticated_user_id = verify_jwt_token(token)

    # Ensure authenticated user matches path user_id
    if authenticated_user_id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Continue with connection...
```

#### 3. CORS Configuration

```python
# Update api_websocket.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.photospherelabs.com",
        "https://photospherelabs.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### 4. Rate Limiting

```python
# Install slowapi
# pip install slowapi

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/conversations/{user_id}")
@limiter.limit("100/minute")
async def get_conversations(request: Request, user_id: str):
    # ... existing code
```

#### 5. Input Validation

```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=2000)
    conversation_id: str = Field(..., regex="^[a-zA-Z0-9-]+$")

    @validator('query')
    def validate_query(cls, v):
        # Remove potential injection attempts
        dangerous_patterns = ['<script', 'javascript:', 'DROP TABLE', '--']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Query contains dangerous pattern: {pattern}")
        return v
```

### Network Security

#### Firewall Rules

```bash
# Railway (automatic)
# - Only ports 80, 443 exposed
# - Automatic DDoS protection

# AWS Security Groups (if using ECS)
# Inbound rules:
# - Port 443 (HTTPS/WSS) from 0.0.0.0/0
# - Port 80 (HTTP redirect) from 0.0.0.0/0

# Outbound rules:
# - Port 443 to OpenAI, Firebase, AWS APIs
```

#### SSL/TLS

```bash
# Railway: Automatic Let's Encrypt SSL

# AWS ALB: Configure SSL certificate
aws acm request-certificate \
  --domain-name api.photospherelabs.com \
  --validation-method DNS
```

---

## Monitoring & Logging

### Application Monitoring

#### 1. Error Tracking (Sentry)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Configure in api_websocket.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    traces_sample_rate=0.1,  # 10% of transactions
)
```

#### 2. Logging Strategy

```python
# Structured logging configuration
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "line": record.lineno,
        }
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        return json.dumps(log_data)

# Configure handlers
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

#### 3. Metrics (Prometheus)

```python
# Install prometheus client
# pip install prometheus-client

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
llm_api_calls = Counter('llm_api_calls_total', 'Total LLM API calls', ['provider', 'model'])
query_execution_time = Histogram('query_execution_seconds', 'Query execution time', ['query_type'])

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Infrastructure Monitoring

#### Railway Dashboard
- Built-in metrics (CPU, Memory, Network)
- Deployment history
- Log aggregation
- Cost tracking

#### AWS CloudWatch (if using ECS)
```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/photosphere-backend

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name photosphere-backend \
  --dashboard-body file://cloudwatch-dashboard.json
```

### Uptime Monitoring

#### UptimeRobot Configuration

```yaml
Monitors:
  - name: API Health Check
    type: HTTP(S)
    url: https://api.photospherelabs.com/
    interval: 5 minutes
    alert_contacts: [email, slack]

  - name: WebSocket Check
    type: Keyword
    url: https://api.photospherelabs.com/
    keyword: "ok"
    interval: 5 minutes
```

### Alerting Rules

```yaml
Alerts:
  Critical:
    - API down for >5 minutes → Page on-call engineer
    - Error rate >5% → Slack alert
    - AWS cost >$100/day → Email alert

  Warning:
    - Response time >5s (p95) → Slack alert
    - Memory usage >80% → Email alert
    - OpenAI API errors >10/hour → Slack alert

  Info:
    - New deployment → Slack notification
    - Daily summary report → Email
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: '3.12'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov black flake8

      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Format check with black
        run: black . --check

      - name: Run tests
        run: pytest tests/ --cov=. --cov-report=xml

      - name: Security scan
        run: |
          pip install safety bandit
          safety check
          bandit -r . -f json -o bandit-report.json

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy-staging:
    needs: [test, security-scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway (Staging)
        run: |
          npm install -g @railway/cli
          railway link ${{ secrets.RAILWAY_STAGING_PROJECT }}
          railway up --environment staging
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

      - name: Run smoke tests
        run: |
          sleep 30  # Wait for deployment
          curl -f https://staging-api.photospherelabs.com/ || exit 1

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway (Production)
        run: |
          npm install -g @railway/cli
          railway link ${{ secrets.RAILWAY_PRODUCTION_PROJECT }}
          railway up --environment production
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

      - name: Run smoke tests
        run: |
          sleep 30
          curl -f https://api.photospherelabs.com/ || exit 1

      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment completed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
```

### Deployment Environments

```yaml
Environments:
  development:
    url: http://localhost:8000
    auto_deploy: on commit

  staging:
    url: https://staging-api.photospherelabs.com
    auto_deploy: on merge to main
    requires_approval: false

  production:
    url: https://api.photospherelabs.com
    auto_deploy: on merge to main
    requires_approval: true
    approvers: [team-lead, cto]
```

---

## Scaling Strategy

### Horizontal Scaling

#### Railway Auto-Scaling

```json
// railway.json
{
  "deploy": {
    "numReplicas": {
      "min": 1,
      "max": 5
    },
    "autoscaling": {
      "enabled": true,
      "cpuThreshold": 70,
      "memoryThreshold": 80
    }
  }
}
```

#### AWS ECS Auto-Scaling

```bash
# Create scaling policy
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/photosphere-cluster/backend-service \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/photosphere-cluster/backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

### Vertical Scaling

| Users | CPU | Memory | Instances | Cost (Railway) |
|-------|-----|--------|-----------|----------------|
| 1-100 | 1 vCPU | 1GB | 1 | $5/month |
| 100-500 | 2 vCPU | 2GB | 1-2 | $10-20/month |
| 500-1000 | 2 vCPU | 4GB | 2-3 | $30-40/month |
| 1000-5000 | 4 vCPU | 8GB | 3-5 | $80-120/month |

### Performance Optimization

#### 1. Connection Pooling

```python
# Database connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    connection_string,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

#### 2. Caching Layer

```python
# Redis caching
import redis
from functools import lru_cache

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@lru_cache(maxsize=100)
def get_table_schema(table_name: str):
    # Cache table schemas
    cached = redis_client.get(f"schema:{table_name}")
    if cached:
        return json.loads(cached)

    # Fetch and cache
    schema = fetch_schema(table_name)
    redis_client.setex(f"schema:{table_name}", 3600, json.dumps(schema))
    return schema
```

#### 3. Async Processing

```python
# Use async for I/O operations
async def process_query_async(query: str):
    async with aiohttp.ClientSession() as session:
        # Parallel API calls
        firebase_task = asyncio.create_task(fetch_context(session, user_id))
        athena_task = asyncio.create_task(execute_query(session, sql))

        context, data = await asyncio.gather(firebase_task, athena_task)
        return interpret_data(data, context)
```

---

## Disaster Recovery

### Backup Strategy

#### 1. Firestore Backups (Automatic)

```bash
# Firestore automatically backs up data
# Configure backup retention in Firebase Console
# Settings → Backups → Configure

# Manual export (for critical data)
gcloud firestore export gs://photosphere-backups/$(date +%Y%m%d)
```

#### 2. Configuration Backups

```bash
# Backup environment variables
railway variables list --json > backup/railway-vars-$(date +%Y%m%d).json

# Backup AWS Secrets
aws secretsmanager get-secret-value \
  --secret-id photosphere/backend/production \
  --query SecretString \
  --output text > backup/aws-secrets-$(date +%Y%m%d).json
```

#### 3. Code Backups

```bash
# Git is primary backup
# Maintain mirrors:
git remote add gitlab git@gitlab.com:photosphere/ps-labs-agent.git
git push gitlab main
```

### Recovery Procedures

#### Scenario 1: API Server Down

```bash
# 1. Check Railway status
railway status

# 2. View logs
railway logs --tail 100

# 3. Restart service
railway restart

# 4. If restart fails, rollback
railway rollback

# 5. If all fails, redeploy from last known good commit
git checkout <last-good-commit>
railway up
```

#### Scenario 2: Database Connection Lost

```bash
# 1. Verify Firebase status
curl https://status.firebase.google.com/

# 2. Check credentials
railway variables get FIREBASE_SECRET_NAME

# 3. Rotate credentials if needed
aws secretsmanager update-secret \
  --secret-id <secret-name> \
  --secret-string file://new-firebase-creds.json

# 4. Restart service
railway restart
```

#### Scenario 3: AWS Access Issues

```bash
# 1. Verify IAM credentials
aws sts get-caller-identity

# 2. Check policy permissions
aws iam get-user-policy \
  --user-name photosphere-backend-prod \
  --policy-name AthenaAccess

# 3. Rotate keys if compromised
aws iam create-access-key --user-name photosphere-backend-prod
railway variables set AWS_ACCESS_KEY_ID=<new-key>
railway variables set AWS_SECRET_ACCESS_KEY=<new-secret>
```

### Rollback Strategy

```yaml
Rollback Triggers:
  Automatic:
    - Error rate >10% for 5 minutes
    - Health check failures >3
    - Critical exceptions

  Manual:
    - Customer-reported issues
    - Data integrity concerns
    - Security incidents

Rollback Process:
  1. Identify last known good deployment
  2. Railway: railway rollback
  3. Verify health checks pass
  4. Monitor error rates
  5. Notify stakeholders
  6. Post-mortem analysis
```

---

## Cost Estimates

### Monthly Operating Costs

#### Railway (Recommended Initial)

| Component | Usage | Cost |
|-----------|-------|------|
| **Compute** | 1 instance, 1 vCPU, 1GB RAM | $5 |
| **Bandwidth** | 100GB outbound | Included |
| **SSL Certificate** | Auto-provisioned | Included |
| **Custom Domain** | 1 domain | Included |
| **Total (Railway)** | | **$5/month** |

#### External Services

| Service | Usage | Cost |
|---------|-------|------|
| **OpenAI API** | 10M tokens/month (~$30/1M) | $300 |
| **AWS Athena** | 100 queries/day, 1GB scanned | $5 |
| **AWS Secrets Manager** | 1 secret | $0.40 |
| **Firebase Firestore** | 100K reads, 50K writes | $0.60 |
| **Sentry** | Free tier | $0 |
| **Total (External)** | | **$306/month** |

#### Total Initial Cost: ~$311/month

### Scaling Costs

| Users | Railway | External Services | Total/Month |
|-------|---------|-------------------|-------------|
| 100 | $5 | $306 | **$311** |
| 500 | $15 | $450 | **$465** |
| 1,000 | $30 | $800 | **$830** |
| 5,000 | $80 | $2,500 | **$2,580** |

### AWS ECS Costs (Alternative)

| Component | Configuration | Cost/Month |
|-----------|--------------|------------|
| **Fargate Tasks** | 2 tasks, 1 vCPU, 2GB RAM | $50 |
| **Application Load Balancer** | Standard | $22 |
| **Data Transfer** | 100GB outbound | $9 |
| **CloudWatch Logs** | 10GB | $5 |
| **Total (AWS Infrastructure)** | | **$86/month** |

---

## AWS ECS Deployment Guide

For teams ready for enterprise-grade deployment:

### Prerequisites

```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# Install ECS CLI
brew install amazon-ecs-cli
```

### Step-by-Step Deployment

#### 1. Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name photosphere-backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Build and Push Docker Image

```bash
# Build image
docker build -t photosphere-backend .

# Tag image
docker tag photosphere-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/photosphere-backend:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/photosphere-backend:latest
```

#### 3. Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name photosphere-cluster

# Create task execution role
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

#### 4. Create Task Definition

```json
// task-definition.json
{
  "family": "photosphere-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/photosphereBackendTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/photosphere-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "AWS_REGION", "value": "us-east-1"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:photosphere/backend/production:OPENAI_API_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/photosphere-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/ || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### 5. Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name photosphere-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345 \
  --scheme internet-facing

# Create target group
aws elbv2 create-target-group \
  --name photosphere-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-12345 \
  --target-type ip \
  --health-check-path / \
  --health-check-interval-seconds 30

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<acm-cert-arn> \
  --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

#### 6. Create ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster photosphere-cluster \
  --service-name backend-service \
  --task-definition photosphere-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=<tg-arn>,containerName=backend,containerPort=8000"
```

#### 7. Configure Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/photosphere-cluster/backend-service \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/photosphere-cluster/backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

---

## Post-Deployment Checklist

### Day 1

- [ ] Verify all endpoints return 200 OK
- [ ] Test WebSocket connections from frontend
- [ ] Send test queries and verify responses
- [ ] Check logs for errors
- [ ] Verify Firebase connectivity
- [ ] Verify AWS Athena queries work
- [ ] Test authentication flow
- [ ] Monitor error rates (<1%)
- [ ] Verify SSL certificate valid

### Week 1

- [ ] Monitor uptime (>99.9%)
- [ ] Review error logs daily
- [ ] Check cost metrics
- [ ] Optimize slow queries
- [ ] Review security alerts
- [ ] Test load handling (simulate 10x traffic)
- [ ] Verify backups working
- [ ] Update documentation

### Month 1

- [ ] Performance review
- [ ] Cost optimization
- [ ] Security audit
- [ ] Scale testing
- [ ] User feedback review
- [ ] Disaster recovery drill
- [ ] Documentation update

---

## Support & Escalation

### Runbook

| Issue | Severity | Response Time | Contact |
|-------|----------|---------------|---------|
| API Down | P0 | Immediate | On-call engineer, CTO |
| High Error Rate | P1 | 15 minutes | Backend team lead |
| Slow Performance | P2 | 1 hour | Backend team |
| Minor Bug | P3 | Next business day | Support team |

### Contact Information

| Role | Contact | Backup |
|------|---------|--------|
| On-Call Engineer | [TBD] | [TBD] |
| DevOps Lead | [TBD] | [TBD] |
| CTO | [TBD] | - |

### Incident Response

1. **Detection**: Monitoring alert or user report
2. **Assessment**: Determine severity (P0-P3)
3. **Notification**: Alert appropriate team members
4. **Mitigation**: Immediate fix or rollback
5. **Communication**: Update status page, notify users
6. **Resolution**: Deploy permanent fix
7. **Post-Mortem**: Document learnings, prevent recurrence

---

## Next Steps

### Immediate (This Week)

1. ⬜ Complete P0 security fixes (PSAG-8 to PSAG-11) - See Jira
2. ✅ Set up Railway account
3. ✅ Create Dockerfile
4. ✅ Deploy to staging
5. ✅ Run smoke tests

### Short Term (Next 2 Weeks)

1. ✅ Deploy to production
2. ✅ Configure monitoring
3. ✅ Set up CI/CD
4. ✅ Load testing
5. ✅ Documentation finalization

### Long Term (Next 3 Months)

1. ⬜ Implement remaining P1 security fixes
2. ⬜ Achieve 80% test coverage
3. ⬜ Optimize performance
4. ⬜ Plan AWS ECS migration
5. ⬜ Cost optimization

---

**Document Status**: Draft → Review → Approved → Implemented
**Owner**: DevOps Team
**Last Updated**: 2025-10-06
**Next Review**: After first production deployment
