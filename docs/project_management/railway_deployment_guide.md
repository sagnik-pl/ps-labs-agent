# Railway Deployment Guide - Execution Plan
## Deploy ps-labs-agent WebSocket Backend to Production

**Status**: Ready to Execute
**Estimated Time**: 2-3 hours
**Target**: Production deployment at api.photospherelabs.com

---

## Pre-Flight Checklist

### ⚠️ CRITICAL SECURITY FIXES (Do First!)

Before deploying, we **MUST** fix exposed credentials:

- [ ] **Step 0.1**: Rotate OpenAI API Key
- [ ] **Step 0.2**: Create new AWS IAM user with minimal permissions
- [ ] **Step 0.3**: Update Firebase secret if needed
- [ ] **Step 0.4**: Verify `.env` is in `.gitignore` (it is, but double-check)

### Prerequisites

- [ ] Railway account (sign up at https://railway.app)
- [ ] GitHub account with repo access
- [ ] Domain access (to configure api.photospherelabs.com)
- [ ] New credentials ready (OpenAI, AWS)
- [ ] Node.js installed (for Railway CLI)

---

## Phase 0: Security Fixes (REQUIRED - Do First!)

### Step 0.1: Rotate OpenAI API Key

```bash
# 1. Go to https://platform.openai.com/api-keys
# 2. Click "Create new secret key"
# 3. Name it: "photosphere-production-2025"
# 4. Copy the key (starts with sk-proj-...)
# 5. Save to password manager

# 6. Test new key works
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-YOUR_NEW_KEY" \
  | jq '.data[0].id'

# Expected: "gpt-3.5-turbo" or similar

# 7. IMPORTANT: Revoke old key in OpenAI dashboard
```

**Save this value - you'll need it for Railway:**
```
OPENAI_API_KEY=sk-proj-[YOUR_NEW_KEY_HERE]
```

### Step 0.2: Create New AWS IAM User

```bash
# 1. Create IAM user
aws iam create-user --user-name photosphere-backend-prod

# 2. Create restrictive policy
cat > athena-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StartQueryExecution",
        "athena:StopQueryExecution"
      ],
      "Resource": "arn:aws:athena:*:*:workgroup/primary"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetTables"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::photosphere-athena-results",
        "arn:aws:s3:::photosphere-athena-results/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:photosphere/firebase/*"
    }
  ]
}
EOF

# 3. Create policy
aws iam create-policy \
  --policy-name PhotosphereBackendPolicy \
  --policy-document file://athena-policy.json

# 4. Attach policy to user
aws iam attach-user-policy \
  --user-name photosphere-backend-prod \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/PhotosphereBackendPolicy

# 5. Create access keys
aws iam create-access-key --user-name photosphere-backend-prod

# Output will show:
# {
#     "AccessKey": {
#         "AccessKeyId": "AKIA...",
#         "SecretAccessKey": "...",
#         ...
#     }
# }
```

**Save these values:**
```
AWS_ACCESS_KEY_ID=AKIA[YOUR_NEW_KEY]
AWS_SECRET_ACCESS_KEY=[YOUR_NEW_SECRET]
```

### Step 0.3: Verify Old Credentials Revoked

```bash
# List all access keys for old user
aws iam list-access-keys --user-name [OLD_USER_NAME]

# Delete old access keys
aws iam delete-access-key \
  --user-name [OLD_USER_NAME] \
  --access-key-id AKIAW36XHETWJYNIISWS

# Revoke old OpenAI key in dashboard
# https://platform.openai.com/api-keys
```

---

## Phase 1: Prepare Repository

### Step 1.1: Create Dockerfile

```bash
cd /Users/sagnik/Development/ps-labs-agent

cat > Dockerfile << 'EOF'
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["uvicorn", "api_websocket:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
EOF
```

### Step 1.2: Create .dockerignore

```bash
cat > .dockerignore << 'EOF'
# Environment files
.env
.env.*
!.env.example

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
agent_venv/
venv/
env/
ENV/

# Git
.git/
.gitignore
.gitattributes

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Documentation
*.md
!README.md
docs/

# Tests
tests/
test_*.py
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db
EOF
```

### Step 1.3: Create railway.json

```bash
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
    "restartPolicyMaxRetries": 10,
    "healthcheckPath": "/",
    "healthcheckTimeout": 100
  }
}
EOF
```

### Step 1.4: Update .gitignore

```bash
# Verify .env is ignored
grep -q "^.env$" .gitignore || echo ".env" >> .gitignore
grep -q "^.env.*$" .gitignore || echo ".env.*" >> .gitignore

# Add Railway-specific ignores
cat >> .gitignore << 'EOF'

# Railway
.railway/
EOF
```

### Step 1.5: Test Docker Build Locally

```bash
# Build the Docker image
docker build -t ps-labs-agent:test .

# Expected output: Successfully built...

# Test run (won't work fully without env vars, but should start)
docker run -p 8000:8000 ps-labs-agent:test

# Press Ctrl+C to stop
```

---

## Phase 2: Setup Railway

### Step 2.1: Install Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Verify installation
railway --version
```

### Step 2.2: Login to Railway

```bash
# Login (opens browser)
railway login

# Verify login
railway whoami
```

### Step 2.3: Create Railway Project

```bash
# Initialize project
railway init

# You'll be prompted:
# ? Enter project name: ps-labs-agent-backend
# ? Select a team: [Select your team or personal account]

# Link to current directory
railway link
```

### Step 2.4: Configure Environment Variables

**Create a file with your new credentials:**

```bash
# Create env vars file (DO NOT COMMIT THIS)
cat > .env.railway << 'EOF'
ENVIRONMENT=production
DEBUG=false

# OpenAI (NEW KEY from Step 0.1)
OPENAI_API_KEY=sk-proj-[YOUR_NEW_KEY_HERE]

# AWS (NEW KEYS from Step 0.2)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIA[YOUR_NEW_KEY]
AWS_SECRET_ACCESS_KEY=[YOUR_NEW_SECRET]

# AWS Resources (verify these values)
GLUE_DATABASE=photosphere_production
ATHENA_S3_OUTPUT_LOCATION=s3://photosphere-athena-results/production/
FIREBASE_SECRET_NAME=photosphere/firebase/production

# API Configuration
CORS_ORIGINS=https://www.photospherelabs.com,https://photospherelabs.com

# Logging (optional)
LOG_LEVEL=INFO
EOF

# Add to gitignore
echo ".env.railway" >> .gitignore
```

**Set variables in Railway:**

```bash
# Set each variable
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false
railway variables set OPENAI_API_KEY="sk-proj-YOUR_NEW_KEY"
railway variables set AWS_REGION=us-east-1
railway variables set AWS_ACCESS_KEY_ID="AKIA_YOUR_KEY"
railway variables set AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
railway variables set GLUE_DATABASE="photosphere_production"
railway variables set ATHENA_S3_OUTPUT_LOCATION="s3://photosphere-athena-results/production/"
railway variables set FIREBASE_SECRET_NAME="photosphere/firebase/production"
railway variables set CORS_ORIGINS="https://www.photospherelabs.com,https://photospherelabs.com"
railway variables set LOG_LEVEL="INFO"

# Verify all variables set
railway variables
```

---

## Phase 3: Deploy to Railway

### Step 3.1: Commit Changes

```bash
# Stage new files
git add Dockerfile .dockerignore railway.json .gitignore

# Commit
git commit -m "feat: Add Railway deployment configuration

- Add Dockerfile with Python 3.12 and health checks
- Add .dockerignore for optimal build
- Add railway.json for deployment config
- Update .gitignore for Railway files

Deployment ready for production Railway instance.
"
```

### Step 3.2: Deploy

```bash
# Deploy to Railway
railway up

# This will:
# 1. Upload your code
# 2. Build Docker image
# 3. Deploy container
# 4. Assign a URL

# Watch deployment logs
railway logs --follow
```

**Expected output:**
```
✓ Build successful
✓ Deployment live
✓ https://ps-labs-agent-production-xxxx.up.railway.app
```

### Step 3.3: Test Deployment

```bash
# Get your Railway URL
RAILWAY_URL=$(railway status --json | jq -r '.environment.deployments[0].url')

# Test health endpoint
curl https://$RAILWAY_URL/

# Expected: {"status":"ok","service":"Photosphere Labs Agent API","version":"1.0.0"}

# Test WebSocket (install wscat if needed)
npm install -g wscat

# Connect to WebSocket
wscat -c wss://$RAILWAY_URL/ws/test-user/test-session

# Send a test message
{"type":"query","query":"test","conversation_id":"test"}

# You should see progress events streaming back
```

---

## Phase 4: Configure Custom Domain

### Step 4.1: Add Domain in Railway

```bash
# Via CLI (or use Railway dashboard)
railway domain

# This opens browser to domain settings
```

**In Railway Dashboard:**
1. Go to your project
2. Click on "Settings" tab
3. Scroll to "Domains"
4. Click "Add Domain"
5. Enter: `api.photospherelabs.com`
6. Click "Add"

**Railway will provide a CNAME target like:**
```
ps-labs-agent-production.up.railway.app
```

### Step 4.2: Update DNS

**In your DNS provider (Vercel, Cloudflare, etc.):**

```
Type: CNAME
Name: api
Value: ps-labs-agent-production.up.railway.app
TTL: 300 (or Auto)
```

**Example for Cloudflare:**
```bash
# Using Cloudflare API
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer YOUR_CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type":"CNAME",
    "name":"api",
    "content":"ps-labs-agent-production.up.railway.app",
    "ttl":300,
    "proxied":false
  }'
```

### Step 4.3: Wait for SSL Provisioning

```bash
# Railway auto-provisions SSL (Let's Encrypt)
# Usually takes 5-10 minutes

# Check status
railway logs --follow | grep -i ssl

# Test HTTPS
curl https://api.photospherelabs.com/

# Expected: {"status":"ok"...}
```

---

## Phase 5: Update Frontend

### Step 5.1: Update Frontend Environment Variables

**In your ps-labs-app repository:**

```typescript
// Update .env.production or wherever WebSocket URL is configured
VITE_WEBSOCKET_URL=wss://api.photospherelabs.com
VITE_API_URL=https://api.photospherelabs.com
```

### Step 5.2: Update Frontend Code (if hardcoded)

```typescript
// In ps-labs-app/src/config.ts or similar
export const WEBSOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL ||
  (import.meta.env.PROD
    ? 'wss://api.photospherelabs.com'
    : 'ws://localhost:8000');
```

### Step 5.3: Deploy Frontend

```bash
# In ps-labs-app repo
git add .
git commit -m "chore: Update API URL to production Railway deployment"
git push origin main

# Vercel will auto-deploy
```

---

## Phase 6: Verify End-to-End

### Step 6.1: Test from Frontend

1. Visit https://www.photospherelabs.com
2. Open browser DevTools (Console + Network tabs)
3. Go to chat interface
4. Send a test query

**Expected behavior:**
- WebSocket connects to `wss://api.photospherelabs.com`
- See progress events streaming
- Final response appears in chat
- No errors in console

### Step 6.2: Test API Endpoints

```bash
# Test conversations endpoint (should fail without auth for now)
curl https://api.photospherelabs.com/conversations/test-user

# Test health
curl https://api.photospherelabs.com/
```

### Step 6.3: Monitor Logs

```bash
# Watch Railway logs in real-time
railway logs --follow

# Filter for errors
railway logs --follow | grep -i error

# Filter for specific user
railway logs --follow | grep "user_id"
```

---

## Phase 7: Monitoring Setup

### Step 7.1: Configure Railway Alerts

**In Railway Dashboard:**
1. Go to Settings → Notifications
2. Add your email/Slack webhook
3. Enable alerts for:
   - Deployment failures
   - High memory usage (>80%)
   - High CPU usage (>80%)
   - Crashes/restarts

### Step 7.2: Set Up Uptime Monitoring

**Using UptimeRobot (free tier):**

1. Go to https://uptimerobot.com
2. Add New Monitor:
   - Type: HTTP(S)
   - URL: `https://api.photospherelabs.com/`
   - Interval: 5 minutes
   - Alert Contacts: Your email

### Step 7.3: Set Up Error Tracking (Optional but Recommended)

```bash
# Install Sentry
pip install sentry-sdk

# Add to requirements.txt
echo "sentry-sdk==1.40.0" >> requirements.txt
```

**Update api_websocket.py:**
```python
import sentry_sdk

# Add at the top of file
if settings.environment == "production":
    sentry_sdk.init(
        dsn="https://your-sentry-dsn@sentry.io/project",
        environment="production",
        traces_sample_rate=0.1,
    )
```

---

## Troubleshooting

### Issue: Build Fails

```bash
# Check build logs
railway logs --deployment

# Common issues:
# - Missing requirements.txt dependencies
# - Python version mismatch
# - Invalid Dockerfile syntax

# Solution: Fix issue, commit, and redeploy
git add .
git commit -m "fix: Update Docker configuration"
railway up
```

### Issue: Deployment Succeeds but Health Check Fails

```bash
# Check application logs
railway logs --follow

# Check if port 8000 is correct
# Verify HEALTHCHECK in Dockerfile
# Test locally:
docker build -t test .
docker run -p 8000:8000 test
curl http://localhost:8000/
```

### Issue: WebSocket Connection Fails

```bash
# Check CORS configuration
# Verify in api_websocket.py:
# allow_origins=["https://www.photospherelabs.com"]

# Check Railway logs for connection attempts
railway logs --follow | grep WebSocket

# Test WebSocket directly
wscat -c wss://api.photospherelabs.com/ws/test/test
```

### Issue: Environment Variables Not Working

```bash
# List all variables
railway variables

# Check for typos
railway variables get OPENAI_API_KEY

# Update if needed
railway variables set OPENAI_API_KEY="new-value"

# Restart service
railway restart
```

### Issue: "Module not found" errors

```bash
# Check requirements.txt is complete
cat requirements.txt

# Add missing dependencies
echo "missing-package==1.0.0" >> requirements.txt
git add requirements.txt
git commit -m "fix: Add missing dependency"
railway up
```

---

## Rollback Procedure

If something goes wrong:

```bash
# View deployment history
railway status

# Rollback to previous deployment
railway rollback

# Or rollback to specific deployment
railway rollback <deployment-id>

# Monitor rollback
railway logs --follow
```

---

## Post-Deployment Checklist

### Immediate (Next 30 minutes)

- [ ] Health check returns 200 OK
- [ ] WebSocket connects successfully
- [ ] Test query works end-to-end
- [ ] Logs show no errors
- [ ] SSL certificate valid
- [ ] Custom domain resolves correctly
- [ ] Frontend connects to production backend

### First 24 Hours

- [ ] Monitor error rates (<1%)
- [ ] Monitor response times (<2s p95)
- [ ] Check Railway metrics (CPU, Memory)
- [ ] Verify Firebase connectivity
- [ ] Verify AWS Athena queries work
- [ ] Test with real user queries
- [ ] Monitor costs (Railway + OpenAI)

### First Week

- [ ] Review all logs for errors
- [ ] Optimize slow queries
- [ ] Add additional monitoring
- [ ] Document any issues
- [ ] Update runbooks
- [ ] Plan security improvements (SEC-002, SEC-003)

---

## Next Steps After Deployment

### Priority 1: Complete Security Fixes

From [vulns_and_issues.md](vulns_and_issues.md):

1. **SEC-002**: Implement JWT authentication on WebSocket
2. **SEC-003**: Add authentication to REST endpoints
3. **SEC-004**: Already done (CORS fix)
4. **SEC-010**: Add rate limiting

### Priority 2: Monitoring & Observability

1. Set up comprehensive logging
2. Add Prometheus metrics
3. Create dashboards
4. Configure alerting

### Priority 3: CI/CD Pipeline

1. Set up GitHub Actions
2. Automate testing
3. Automate deployments
4. Add security scanning

---

## Cost Monitoring

### Railway Costs

**Current Plan:**
- Starter: $5/month base
- Usage: ~$0-15/month (depends on traffic)

**Monitor costs:**
```bash
# Check usage in Railway dashboard
# Settings → Usage
```

### OpenAI API Costs

```bash
# Monitor at: https://platform.openai.com/usage

# Set up billing alerts:
# 1. Go to Settings → Billing
# 2. Set up usage limit ($300/month recommended)
# 3. Add email notifications
```

### AWS Costs

```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

---

## Success Criteria

Deployment is successful when:

✅ Health endpoint returns 200 OK
✅ WebSocket connections work from frontend
✅ Queries execute successfully end-to-end
✅ Logs show INFO level only (no errors)
✅ SSL certificate valid on custom domain
✅ Response times <2s p95
✅ Error rate <1%
✅ Firebase, AWS, OpenAI integrations working
✅ Frontend deploys successfully with new API URL

---

## Support & Escalation

### If Something Goes Wrong

**Immediate Actions:**
1. Check Railway logs: `railway logs --follow`
2. Check health endpoint: `curl https://api.photospherelabs.com/`
3. Rollback if needed: `railway rollback`
4. Check status page: https://railway.app/status

**Contact:**
- Railway Support: https://railway.app/help
- GitHub Issues: https://github.com/sagnik-pl/ps-labs-agent/issues

---

## Appendix: Quick Reference

### Railway CLI Commands

```bash
# Deploy
railway up

# View logs
railway logs --follow

# Check status
railway status

# Restart service
railway restart

# Rollback
railway rollback

# View variables
railway variables

# Set variable
railway variables set KEY=value

# Delete variable
railway variables delete KEY

# Open dashboard
railway open
```

### Useful URLs

- Railway Dashboard: https://railway.app/project/YOUR_PROJECT
- Railway Docs: https://docs.railway.app
- Production API: https://api.photospherelabs.com
- Frontend: https://www.photospherelabs.com
- OpenAI Dashboard: https://platform.openai.com
- AWS Console: https://console.aws.amazon.com

---

**Document Status**: Ready to Execute
**Estimated Execution Time**: 2-3 hours
**Last Updated**: 2025-10-06
**Next Review**: After successful deployment
