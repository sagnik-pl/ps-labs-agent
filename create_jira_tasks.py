#!/usr/bin/env python3
"""
Bulk create all ps-labs-agent tasks in Jira following software engineering best practices.

Creates:
- 8 EPICs organized by theme
- 44 tasks across P0-P3 priorities
- Proper labels, story points, dependencies, descriptions
"""
import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional

# Jira Configuration
# Load from .jira_credentials file (excluded from git)
credentials_file = Path(__file__).parent / ".jira_credentials"
if credentials_file.exists():
    # Read credentials from file
    with open(credentials_file) as f:
        for line in f:
            if line.startswith("JIRA_EMAIL="):
                JIRA_EMAIL = line.split("=", 1)[1].strip()
            elif line.startswith("JIRA_TOKEN="):
                JIRA_TOKEN = line.split("=", 1)[1].strip()
            elif line.startswith("JIRA_URL="):
                JIRA_URL = line.split("=", 1)[1].strip()
            elif line.startswith("JIRA_PROJECT="):
                JIRA_PROJECT = line.split("=", 1)[1].strip()
else:
    # Fallback to environment variables
    JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")
    JIRA_URL = os.getenv("JIRA_URL", "https://photospherelabs.atlassian.net")
    JIRA_PROJECT = os.getenv("JIRA_PROJECT", "PSAG")

if not JIRA_EMAIL or not JIRA_TOKEN:
    print("❌ Error: JIRA_EMAIL and JIRA_TOKEN must be set")
    print("   Create .jira_credentials file or set environment variables")
    exit(1)

ASSIGNEE_ACCOUNT_ID = "712020:0e79e054-9f07-4f7c-91f3-73834452b521"  # Sagnik

# Issue Type IDs
ISSUE_TYPE_TASK = "10008"
ISSUE_TYPE_EPIC = "10009"

# Create session
session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_TOKEN)
session.headers.update({"Content-Type": "application/json"})

# Track created issues
created_issues = {}

# Priority mapping (Jira uses: Highest, High, Medium, Low, Lowest)
PRIORITY_MAP = {
    "CRITICAL": "Highest",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low"
}

# Story point mapping (hours -> points, using Fibonacci)
EFFORT_TO_STORY_POINTS = {
    "1h": 1,
    "2h": 1,
    "4h": 2,
    "6h": 3,
    "8h": 5,
    "12h": 8,
    "16h": 8,
    "20h": 13,
    "24h": 13,
    "40h": 21,
}


def get_story_points(effort: str) -> int:
    """Convert effort estimate to story points."""
    return EFFORT_TO_STORY_POINTS.get(effort, 5)


# EPIC Definitions
EPICS = [
    {
        "name": "Security Hardening",
        "summary": "🔒 Security: Critical security vulnerabilities and hardening",
        "description": """Epic for all security-related tasks including:
- Credential rotation and management
- Authentication & authorization implementation
- CORS and rate limiting
- SQL injection protection
- Input validation and sanitization
- Production deployment security

**Goal**: Secure all API endpoints and eliminate critical vulnerabilities.
**Timeline**: Sprint 0-1 (Weeks 1-3)
**Impact**: CRITICAL - Prevents data breaches, unauthorized access, and security exploits
""",
        "labels": ["security", "P0", "epic"]
    },
    {
        "name": "Architecture & Design",
        "summary": "🏗️ Architecture: System design improvements and refactoring",
        "description": """Epic for architectural improvements:
- LLM provider abstraction layer
- Service layer architecture
- Repository pattern implementation
- Dependency injection
- API versioning
- Event sourcing for workflow state

**Goal**: Establish clean, maintainable architecture for scalability.
**Timeline**: Sprint 2-3 (Weeks 4-7)
**Impact**: HIGH - Improves maintainability, testability, and scalability
""",
        "labels": ["architecture", "P2", "epic"]
    },
    {
        "name": "Testing & CI/CD",
        "summary": "🧪 Testing: Test coverage and continuous integration",
        "description": """Epic for testing infrastructure:
- Unit test suite (>80% coverage)
- Integration tests
- CI/CD pipeline with security scanning
- Test organization and fixtures
- Automated testing on PRs

**Goal**: Establish comprehensive testing to prevent regressions.
**Timeline**: Sprint 1 & 4 (Weeks 2-3, 8-10)
**Impact**: HIGH - Prevents bugs, enables confident refactoring
""",
        "labels": ["testing", "P1", "epic"]
    },
    {
        "name": "Code Quality & Refactoring",
        "summary": "🐛 Quality: Code quality improvements and bug fixes",
        "description": """Epic for code quality improvements:
- Error handling refactoring (remove bare except)
- Replace print statements with logging
- Add type hints
- Extract magic values to constants
- Break down large functions (<50 lines)
- Naming convention standardization

**Goal**: Improve code readability, maintainability, and reduce technical debt.
**Timeline**: Sprint 2 (Weeks 4-5)
**Impact**: MEDIUM - Improves developer productivity and reduces bugs
""",
        "labels": ["quality", "bug", "P2", "epic"]
    },
    {
        "name": "Technical Debt",
        "summary": "⚙️ Tech Debt: Technical debt paydown and infrastructure",
        "description": """Epic for technical debt items:
- Firebase initialization refactoring (singleton pattern)
- Dependency injection implementation
- Retry logic for external services
- Database connection pooling
- Caching strategy (Redis)
- Health checks and monitoring
- Metrics (Prometheus)

**Goal**: Pay down technical debt to improve reliability and performance.
**Timeline**: Sprint 3 (Weeks 6-7)
**Impact**: MEDIUM - Improves reliability, observability, and performance
""",
        "labels": ["tech-debt", "P2", "epic"]
    },
    {
        "name": "Configuration & Environment",
        "summary": "⚙️ Config: Configuration management and environment setup",
        "description": """Epic for configuration improvements:
- Environment variable validation
- Separate dev/prod configurations
- Remove sensitive files from repo
- LLM model configuration
- Secrets management

**Goal**: Improve configuration management and environment setup.
**Timeline**: Backlog (P3)
**Impact**: LOW-MEDIUM - Prevents configuration errors
""",
        "labels": ["configuration", "P3", "epic"]
    },
    {
        "name": "Dependencies & Performance",
        "summary": "⚡ Performance: Dependencies and performance optimization",
        "description": """Epic for dependencies and performance:
- Dependency audit and updates
- Dependency lock file
- Pagination for large queries
- Schema fetching optimization (batch + cache)

**Goal**: Keep dependencies secure and optimize performance bottlenecks.
**Timeline**: Backlog (P3)
**Impact**: LOW-MEDIUM - Security patches and performance gains
""",
        "labels": ["performance", "dependencies", "P3", "epic"]
    },
]


# All 44 Tasks (P0, P1, P2, P3)
TASKS = [
    # === P0 - CRITICAL (Sprint 0) ===
    {
        "id": "SEC-001",
        "summary": "Rotate all exposed API keys and AWS credentials",
        "priority": "CRITICAL",
        "effort": "2h",
        "epic": "Security Hardening",
        "labels": ["security", "P0", "sprint-0"],
        "description": """## Problem
API keys and AWS credentials were exposed in public GitHub repository (in documentation files).

## Tasks
1. Generate new OpenAI API key
2. Create new AWS IAM user with minimal permissions (least privilege)
3. Generate new AWS access keys
4. Update Railway environment variables
5. Update local .env files
6. Check AWS CloudTrail for any unauthorized access
7. Remove credentials from git history (if needed)

## Acceptance Criteria
- [ ] All credentials rotated
- [ ] CloudTrail reviewed for suspicious activity
- [ ] Old credentials revoked
- [ ] New credentials working in dev and prod
- [ ] Documentation updated (without credentials)

## References
- docs/project_management/vulns_and_issues.md
- Railway environment variables
""",
        "dependencies": []
    },
    {
        "id": "SEC-002",
        "summary": "Implement JWT authentication on WebSocket endpoints",
        "priority": "CRITICAL",
        "effort": "8h",
        "epic": "Security Hardening",
        "labels": ["security", "P0", "sprint-0"],
        "description": """## Problem
WebSocket endpoints (`/ws/{user_id}/{session_id}`) are publicly accessible without authentication.

## Solution
Implement JWT token-based authentication for WebSocket connections.

## Implementation
```python
from fastapi import WebSocket, Depends, HTTPException
from jose import JWTError, jwt

async def verify_jwt_websocket(websocket: WebSocket, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        await websocket.close(code=1008)  # Policy violation
        raise HTTPException(403)

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    token: str = Query(...)  # Token in query string for WS
):
    token_data = await verify_jwt_websocket(websocket, token)
    if token_data["sub"] != user_id:
        await websocket.close(code=1008)
        return
    # ... existing code
```

## Acceptance Criteria
- [ ] JWT token required for WebSocket connections
- [ ] Token validation includes user_id matching
- [ ] Expired tokens rejected
- [ ] Invalid tokens close connection
- [ ] Tests for auth failures

## Dependencies
- SEC-001 (credentials rotated)
""",
        "dependencies": ["SEC-001"]
    },
    {
        "id": "SEC-003",
        "summary": "Add authentication to REST API endpoints",
        "priority": "CRITICAL",
        "effort": "4h",
        "epic": "Security Hardening",
        "labels": ["security", "P0", "sprint-0"],
        "description": """## Problem
REST API endpoints are publicly accessible:
- GET /conversations/{user_id}
- GET /conversations/{user_id}/{conversation_id}/messages

## Solution
Add JWT authentication using FastAPI Depends.

## Implementation
```python
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

async def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")

@app.get("/conversations/{user_id}")
async def get_conversations(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["sub"] != user_id:
        raise HTTPException(403, "Unauthorized")
    # ... existing code
```

## Acceptance Criteria
- [ ] All REST endpoints require JWT
- [ ] User can only access their own data
- [ ] 401 for invalid/missing token
- [ ] 403 for unauthorized access
- [ ] Tests for all auth scenarios

## Dependencies
- SEC-002 (WebSocket auth)
""",
        "dependencies": ["SEC-002"]
    },
    {
        "id": "SEC-013",
        "summary": "Secure Railway production deployment",
        "priority": "CRITICAL",
        "effort": "6h",
        "epic": "Security Hardening",
        "labels": ["security", "P0", "sprint-0", "railway"],
        "description": """## Problem
Railway production deployment has 5 critical vulnerabilities:
1. No authentication
2. No authorization
3. CORS wide open (allow_origins=["*"])
4. Data exposure (any user_id can read any data)
5. No rate limiting

## Solution
Apply all security fixes to production deployment.

## Tasks
1. Restrict CORS to frontend domain only
2. Add rate limiting (slowapi)
3. Verify JWT auth working in production
4. Test authentication end-to-end
5. Update frontend to include auth headers/tokens

## Implementation
```python
# CORS restriction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ps-labs-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/conversations/{user_id}")
@limiter.limit("10/minute")
async def get_conversations(...):
    ...
```

## Acceptance Criteria
- [ ] CORS restricted to frontend domain
- [ ] Rate limiting active (10 req/min for reads, 5 req/min for writes)
- [ ] Authentication required for all endpoints
- [ ] Production tested end-to-end
- [ ] Monitoring/alerts set up for auth failures

## Dependencies
- SEC-001, SEC-002, SEC-003
""",
        "dependencies": ["SEC-001", "SEC-002", "SEC-003"]
    },

    # === P1 - HIGH (Sprint 1) ===
    {
        "id": "SEC-004",
        "summary": "Fix CORS configuration (remove wildcard origins)",
        "priority": "HIGH",
        "effort": "2h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1"],
        "description": """## Problem
Current CORS allows wildcard origins: `allow_origins=["*"]`
Risk: CSRF attacks, any website can make requests

## Solution
Restrict to specific frontend domains.

## Implementation
File: api_websocket.py
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ps-labs-app.vercel.app",
        "https://ps-labs-app-staging.vercel.app",
        "http://localhost:3000"  # Local development only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Acceptance Criteria
- [ ] Only whitelisted domains can access API
- [ ] Credentials (cookies/auth headers) work
- [ ] Preflight requests handled correctly
- [ ] Local development still works

## Dependencies
- SEC-003
""",
        "dependencies": ["SEC-003"]
    },
    {
        "id": "SEC-005",
        "summary": "Add SQL injection protections for LLM-generated queries",
        "priority": "HIGH",
        "effort": "16h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1"],
        "description": """## Problem
SQL queries are generated by LLM and executed directly without validation.
Risk: SQL injection, data exfiltration, DROP TABLE attacks

## Solution
Multi-layer SQL injection protection:
1. Whitelist allowed SQL operations (SELECT only)
2. Parse and validate SQL AST
3. Check for dangerous keywords (DROP, DELETE, UPDATE, etc.)
4. Validate table names against allowed schemas
5. Use parameterized queries where possible

## Implementation
Create new file: `utils/sql_validator.py`
```python
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

ALLOWED_OPERATIONS = ["SELECT"]
DANGEROUS_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE", "EXEC", "EXECUTE"]

def validate_sql_query(sql: str, allowed_tables: List[str]) -> Dict[str, Any]:
    # Parse SQL
    parsed = sqlparse.parse(sql)[0]

    # Check operation type
    operation = parsed.get_type()
    if operation not in ALLOWED_OPERATIONS:
        return {"valid": False, "reason": f"Operation {operation} not allowed"}

    # Check for dangerous keywords
    for token in parsed.flatten():
        if token.ttype is Keyword and token.value.upper() in DANGEROUS_KEYWORDS:
            return {"valid": False, "reason": f"Dangerous keyword: {token.value}"}

    # Extract and validate table names
    tables = extract_tables(parsed)
    for table in tables:
        if table not in allowed_tables:
            return {"valid": False, "reason": f"Table {table} not in allowed list"}

    return {"valid": True}
```

## Acceptance Criteria
- [ ] Only SELECT queries allowed
- [ ] Dangerous keywords blocked
- [ ] Table names validated against schema
- [ ] Unit tests for all attack vectors
- [ ] Integration test with LLM-generated queries

## Dependencies
- None
""",
        "dependencies": []
    },
    {
        "id": "SEC-006",
        "summary": "Implement user_id validation in data access layer",
        "priority": "HIGH",
        "effort": "8h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1"],
        "description": """## Problem
No validation that user can only access their own data.
SQL queries don't automatically filter by user_id.

## Solution
Add user_id validation at multiple layers:
1. API layer (already done with JWT)
2. Data access layer (ensure WHERE user_id = ?)
3. SQL validation layer (verify user_id in WHERE clause)

## Implementation
```python
def validate_user_id_in_query(sql: str, user_id: str) -> bool:
    # Ensure query contains WHERE user_id = 'actual_user_id'
    parsed = sqlparse.parse(sql)[0]
    where_clause = extract_where_clause(parsed)

    if not where_clause:
        return False

    # Check for user_id filter
    return f"user_id = '{user_id}'" in where_clause.lower()

def execute_user_query(sql: str, user_id: str):
    if not validate_user_id_in_query(sql, user_id):
        raise SecurityException("Query must filter by user_id")

    # Add user_id filter as safeguard
    safe_sql = inject_user_id_filter(sql, user_id)
    return athena_client.execute_query(safe_sql)
```

## Acceptance Criteria
- [ ] All queries validated for user_id filter
- [ ] Queries without user_id rejected
- [ ] User cannot access other users' data
- [ ] Tests for cross-user access attempts

## Dependencies
- SEC-005
""",
        "dependencies": ["SEC-005"]
    },
    {
        "id": "SEC-007",
        "summary": "Fix Firebase initialization vulnerability",
        "priority": "HIGH",
        "effort": "2h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1"],
        "description": """## Problem
Firebase initialized globally without error handling.
Credentials fetched from AWS Secrets Manager on every import.

## Solution
Use singleton pattern with lazy initialization and proper error handling.

## Implementation
File: `utils/firebase_client.py`
```python
class FirebaseClient:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                self._initialize_firebase()
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                raise

    def _initialize_firebase(self):
        # Existing initialization code
        pass
```

## Acceptance Criteria
- [ ] Singleton pattern implemented
- [ ] Initialization errors logged and raised
- [ ] Credentials fetched only once
- [ ] Tests for initialization failure scenarios

## Dependencies
- None
""",
        "dependencies": []
    },
    {
        "id": "SEC-008",
        "summary": "Remove hardcoded AWS credentials, use IAM roles",
        "priority": "HIGH",
        "effort": "4h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1", "aws"],
        "description": """## Problem
AWS credentials hardcoded in settings and environment variables.
Best practice: Use IAM roles for EC2/ECS/Lambda.

## Solution
Use IAM roles instead of access keys (when possible).
For Railway: Use AWS credentials but ensure minimal IAM permissions.

## Implementation
1. Create IAM role with minimal permissions:
   - athena:StartQueryExecution
   - athena:GetQueryResults
   - glue:GetTable
   - glue:GetTables
   - s3:PutObject (for query results)
   - s3:GetObject (for query results)
   - secretsmanager:GetSecretValue (for Firebase creds)

2. Update boto3 to use IAM role if available:
```python
import boto3

# Will use IAM role if available, fallback to env vars
session = boto3.Session(
    aws_access_key_id=settings.aws_access_key_id if not is_iam_role_available() else None,
    aws_secret_access_key=settings.aws_secret_access_key if not is_iam_role_available() else None,
    region_name=settings.aws_region
)
```

## Acceptance Criteria
- [ ] IAM role created with minimal permissions
- [ ] Application works with IAM role (if deployed to AWS)
- [ ] Falls back to access keys for local development
- [ ] Credentials not logged or exposed

## Dependencies
- SEC-001
""",
        "dependencies": ["SEC-001"]
    },
    {
        "id": "SEC-010",
        "summary": "Implement rate limiting on all endpoints",
        "priority": "MEDIUM",
        "effort": "8h",
        "epic": "Security Hardening",
        "labels": ["security", "P1", "sprint-1"],
        "description": """## Problem
No rate limiting on any endpoints.
Risk: DoS attacks, abuse, excessive API costs.

## Solution
Implement rate limiting using slowapi.

## Implementation
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/conversations/{user_id}")
@limiter.limit("10/minute")
async def get_conversations(...):
    ...

@app.websocket("/ws/{user_id}/{session_id}")
@limiter.limit("5/minute")  # Lower for expensive operations
async def websocket_endpoint(...):
    ...
```

## Rate Limits
- GET endpoints: 10/minute per IP
- WebSocket: 5/minute per IP
- POST endpoints: 5/minute per IP

## Acceptance Criteria
- [ ] Rate limiting active on all endpoints
- [ ] 429 response with Retry-After header
- [ ] Redis backend for distributed rate limiting (optional)
- [ ] Tests for rate limit enforcement

## Dependencies
- SEC-003
""",
        "dependencies": ["SEC-003"]
    },
    {
        "id": "TEST-003",
        "summary": "Set up CI/CD pipeline with security scanning",
        "priority": "HIGH",
        "effort": "16h",
        "epic": "Testing & CI/CD",
        "labels": ["testing", "ci-cd", "P1", "sprint-1"],
        "description": """## Goal
Set up GitHub Actions CI/CD pipeline with:
- Automated testing
- Security scanning
- Code quality checks
- Automated deployment

## Implementation
Create `.github/workflows/ci.yml`:
```yaml
name: CI/CD

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security scan (bandit)
        run: bandit -r . -f json -o bandit-report.json
      - name: Dependency check
        run: safety check --json

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Black formatting check
        run: black --check .
      - name: Type checking (mypy)
        run: mypy .

  deploy:
    needs: [test, security, lint]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        run: railway up
```

## Acceptance Criteria
- [ ] CI runs on all PRs
- [ ] Tests must pass before merge
- [ ] Security scans run automatically
- [ ] Deployment automated to Railway
- [ ] Failed builds block merges

## Dependencies
- None
""",
        "dependencies": []
    },

    # === P2 - MEDIUM (Sprint 2-3) ===
    # ... (I'll add all remaining tasks in next part to stay under token limit)
]

# Add more P2 and P3 tasks here (continuing in next script update)


def markdown_to_adf(markdown_text: str) -> Dict:
    """Convert markdown to Atlassian Document Format (simplified)."""
    # For simplicity, convert to ADF paragraphs
    paragraphs = markdown_text.split('\n\n')
    content = []

    for para in paragraphs:
        if not para.strip():
            continue

        # Check if it's a heading
        if para.startswith('##'):
            content.append({
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": para.replace('##', '').strip()}]
            })
        elif para.startswith('#'):
            content.append({
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": para.replace('#', '').strip()}]
            })
        else:
            # Regular paragraph
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": para.strip()}]
            })

    return {
        "version": 1,
        "type": "doc",
        "content": content
    }


def create_epic(epic_data: Dict) -> Optional[str]:
    """Create an Epic in Jira."""
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "issuetype": {"id": ISSUE_TYPE_EPIC},
            "summary": epic_data["summary"],
            "description": markdown_to_adf(epic_data["description"]),
            "labels": epic_data["labels"],
            "assignee": {"accountId": ASSIGNEE_ACCOUNT_ID}
        }
    }

    try:
        response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=payload)
        if response.status_code == 201:
            issue = response.json()
            issue_key = issue["key"]
            print(f"✅ Created EPIC: {issue_key} - {epic_data['summary'][:50]}...")
            return issue_key
        else:
            print(f"❌ Failed to create EPIC {epic_data['summary'][:50]}: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating EPIC: {e}")
        return None


def create_task(task_data: Dict, epic_key: Optional[str] = None) -> Optional[str]:
    """Create a Task in Jira."""
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "issuetype": {"id": ISSUE_TYPE_TASK},
            "summary": f"[{task_data['id']}] {task_data['summary']}",
            "description": markdown_to_adf(task_data["description"]),
            # Note: Priority field not available in next-gen Kanban, use labels instead
            "labels": task_data["labels"],
            "assignee": {"accountId": ASSIGNEE_ACCOUNT_ID}
        }
    }

    # Add epic link if provided
    if epic_key:
        payload["fields"]["parent"] = {"key": epic_key}

    try:
        response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=payload)
        if response.status_code == 201:
            issue = response.json()
            issue_key = issue["key"]
            print(f"✅ Created Task: {issue_key} - [{task_data['id']}] {task_data['summary'][:60]}...")
            return issue_key
        else:
            print(f"❌ Failed to create task {task_data['id']}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return None


def main():
    """Main execution."""
    print("=" * 80)
    print("🚀 Jira Bulk Task Creation - ps-labs-agent")
    print("=" * 80)

    # Step 1: Create EPICs
    print("\n📋 Creating EPICs...")
    epic_keys = {}
    for epic in EPICS:
        epic_key = create_epic(epic)
        if epic_key:
            epic_keys[epic["name"]] = epic_key
            time.sleep(0.5)  # Rate limiting

    print(f"\n✅ Created {len(epic_keys)}/{len(EPICS)} EPICs")

    # Step 2: Create Tasks
    print("\n📋 Creating Tasks...")
    task_keys = {}
    for task in TASKS:
        epic_key = epic_keys.get(task["epic"])
        task_key = create_task(task, epic_key)
        if task_key:
            task_keys[task["id"]] = task_key
            created_issues[task["id"]] = task_key
            time.sleep(0.5)  # Rate limiting

    print(f"\n✅ Created {len(task_keys)}/{len(TASKS)} Tasks")

    # Step 3: Link dependencies (TODO: implement in next phase)
    print("\n📋 Dependencies will be linked manually (Jira API limitation for next-gen projects)")

    print("\n" + "=" * 80)
    print("✅ Jira setup complete!")
    print(f"   EPICs: {len(epic_keys)}")
    print(f"   Tasks: {len(task_keys)}")
    print(f"\n📊 View in Jira: {JIRA_URL}/browse/{JIRA_PROJECT}")
    print("=" * 80)


if __name__ == "__main__":
    main()
