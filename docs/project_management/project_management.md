# Project Management - Task Backlog
## ps-labs-agent Multi-Agent Analytics System

**Last Updated**: 2025-10-11
**Source**: [vulns_and_issues.md](vulns_and_issues.md)
**Total Tasks**: 44

---

## Overview

This document tracks all tasks identified from the security and code quality analysis. Tasks are organized by priority and include severity levels, types, effort estimates, and dependencies.

### Task Summary

| Priority | Count | Description |
|----------|-------|-------------|
| **P0 - CRITICAL** | 4 | Security vulnerabilities requiring immediate action |
| **P1 - HIGH** | 15 | Critical security and quality issues for current sprint |
| **P2 - MEDIUM** | 22 | Important improvements for next sprint |
| **P3 - LOW** | 3 | Nice-to-have improvements for backlog |

### Task Types

| Type | Count | Description |
|------|-------|-------------|
| 🔒 **Security** | 13 | Security vulnerabilities and improvements |
| 🐛 **Bug** | 7 | Code quality and error handling issues |
| ⚙️ **Tech Debt** | 10 | Technical debt and refactoring needs |
| 🏗️ **Architecture** | 7 | Architectural improvements |
| ⚡ **Performance** | 2 | Performance optimizations |
| 🧪 **Testing** | 3 | Testing infrastructure |
| 📦 **Dependencies** | 2 | Dependency management |

---

## P0 - CRITICAL (Do NOW)

### Sprint 0 - Immediate Action Required

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **SEC-001** | Rotate all exposed API keys and AWS credentials | 🔒 Security | CRITICAL | 2h | ⬜ Todo | None |
| **SEC-002** | Implement JWT authentication on WebSocket endpoints | 🔒 Security | CRITICAL | 8h | ⬜ Todo | SEC-001 |
| **SEC-003** | Add authentication to REST API endpoints | 🔒 Security | CRITICAL | 4h | ⬜ Todo | SEC-002 |
| **SEC-013** | Secure Railway production deployment | 🔒 Security | CRITICAL | 6h | ⬜ Todo | SEC-001, SEC-002, SEC-003 |

**Sprint Goal**: Secure all API endpoints and rotate compromised credentials

#### SEC-013 Details: Production API Security (Railway Deployment)

**Current State**: ⚠️ Railway deployment at `https://ps-labs-agent-backend-production.up.railway.app/` is **publicly accessible** without authentication.

**Vulnerabilities Identified**:

1. **No Authentication** (CRITICAL)
   - Anyone can connect to WebSocket if they know/guess a `user_id`
   - No token or session validation
   - Risk: Unauthorized access to any user's data

2. **No Authorization** (CRITICAL)
   - No checks on who can access which conversations
   - Any request with a valid `user_id` can read all conversations
   - Risk: Data breach, privacy violation

3. **CORS Wide Open** (HIGH)
   - `allow_origins=["*"]` allows any website to call the API
   - Risk: CSRF attacks, malicious websites can make requests on behalf of users
   - **Fix**: `allow_origins=["https://your-frontend-domain.com"]`

4. **Data Exposure** (CRITICAL)
   - Endpoints exposing user data without authentication:
     - `GET /conversations/{user_id}` - Read all conversations
     - `GET /conversations/{user_id}/{conversation_id}/messages` - Read all messages
     - `WS /ws/{user_id}/{session_id}` - Send queries on behalf of user
   - Risk: Anyone with a user_id can read/write their data

5. **No Rate Limiting** (HIGH)
   - Risk: DoS attacks, abuse, excessive costs

**Required Fixes** (Post-Demo):

```python
# 1. Add JWT Authentication
@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    token: str = Depends(verify_jwt_token)  # NEW
):
    # Verify token user_id matches request user_id
    if token.user_id != user_id:
        raise HTTPException(403, "Unauthorized")
    # ... existing code

# 2. Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ps-labs-app.vercel.app"],  # Only frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Add Rate Limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/conversations/{user_id}")
@limiter.limit("10/minute")  # 10 requests per minute
async def get_conversations(user_id: str, token: str = Depends(verify_jwt_token)):
    # Verify token
    if token.user_id != user_id:
        raise HTTPException(403)
    # ... existing code
```

**Implementation Priority**:
1. ✅ **DONE**: Set `ENVIRONMENT=production` in Railway (Firebase connection fixed)
2. ⬜ **Post-Demo**: Rotate credentials (SEC-001)
3. ⬜ **Post-Demo**: Implement JWT auth (SEC-002, SEC-003)
4. ⬜ **Post-Demo**: Fix CORS configuration
5. ⬜ **Post-Demo**: Add rate limiting

**For Demo**: Current setup acceptable if:
- Using test/demo data only
- URL not shared publicly
- User IDs are UUIDs (not predictable sequential IDs)

**Effort Estimate**: 6 hours (depends on SEC-001, SEC-002, SEC-003 completion)

---

## P1 - HIGH (Current Sprint)

### Sprint 1 - Security Hardening

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **SEC-004** | Fix CORS configuration (remove wildcard origins) | 🔒 Security | HIGH | 2h | ⬜ Todo | SEC-003 |
| **SEC-005** | Add SQL injection protections for LLM-generated queries | 🔒 Security | HIGH | 16h | ⬜ Todo | None |
| **SEC-006** | Implement user_id validation in data access layer | 🔒 Security | HIGH | 8h | ⬜ Todo | SEC-005 |
| **SEC-007** | Fix Firebase initialization vulnerability | 🔒 Security | HIGH | 2h | ⬜ Todo | None |
| **SEC-008** | Remove hardcoded AWS credentials, use IAM roles | 🔒 Security | HIGH | 4h | ⬜ Todo | SEC-001 |
| **SEC-010** | Implement rate limiting on all endpoints | 🔒 Security | MEDIUM | 8h | ⬜ Todo | SEC-003 |
| **TEST-003** | Set up CI/CD pipeline with security scanning | 🧪 Testing | HIGH | 16h | ⬜ Todo | None |

**Sprint Goal**: Complete security hardening and establish CI/CD

---

## P2 - MEDIUM (Next Sprint)

### Sprint 2 - Code Quality & Architecture

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **QUAL-001** | Refactor error handling (remove bare except blocks) | 🐛 Bug | HIGH | 12h | ⬜ Todo | None |
| **QUAL-002** | Replace print statements with proper logging | 🐛 Bug | MEDIUM | 4h | ⬜ Todo | None |
| **QUAL-003** | Add type hints to all public methods | 🐛 Bug | MEDIUM | 8h | ⬜ Todo | None |
| **QUAL-004** | Extract magic values to constants/config | 🐛 Bug | MEDIUM | 4h | ⬜ Todo | None |
| **QUAL-005** | Refactor large functions (break down 200+ line functions) | 🐛 Bug | MEDIUM | 12h | ⬜ Todo | None |
| **ARCH-001** | Create LLM provider abstraction layer | 🏗️ Architecture | HIGH | 12h | ⬜ Todo | None |
| **ARCH-002** | Separate concerns in workflow nodes | 🏗️ Architecture | HIGH | 16h | ⬜ Todo | ARCH-001 |
| **ARCH-003** | Implement service layer architecture | 🏗️ Architecture | MEDIUM | 20h | ⬜ Todo | ARCH-002 |

**Sprint Goal**: Improve code quality and establish clean architecture

### Sprint 3 - Technical Debt

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **DEBT-001** | Refactor Firebase initialization (singleton pattern) | ⚙️ Tech Debt | HIGH | 4h | ⬜ Todo | None |
| **DEBT-002** | Replace global singletons with dependency injection | ⚙️ Tech Debt | HIGH | 16h | ⬜ Todo | ARCH-003 |
| **DEBT-003** | Add retry logic for external services (tenacity) | ⚙️ Tech Debt | MEDIUM | 8h | ⬜ Todo | None |
| **DEBT-004** | Move LLM models to configuration | ⚙️ Tech Debt | MEDIUM | 4h | ⬜ Todo | None |
| **DEBT-005** | Implement database connection pooling | ⚙️ Tech Debt | MEDIUM | 8h | ⬜ Todo | None |
| **DEBT-006** | Add caching strategy (Redis/in-memory) | ⚙️ Tech Debt | MEDIUM | 12h | ⬜ Todo | None |
| **DEBT-008** | Add comprehensive health checks | ⚙️ Tech Debt | MEDIUM | 6h | ⬜ Todo | None |
| **DEBT-010** | Implement metrics and monitoring (Prometheus) | ⚙️ Tech Debt | MEDIUM | 16h | ⬜ Todo | None |

**Sprint Goal**: Pay down technical debt and improve reliability

### Sprint 4 - Testing & Quality Assurance

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **TEST-001** | Create unit test suite (>80% coverage) | 🧪 Testing | CRITICAL | 40h | ⬜ Todo | ARCH-003 |
| **TEST-002** | Reorganize test files (move to tests/ directory) | 🧪 Testing | LOW | 2h | ⬜ Todo | None |
| **SEC-009** | Sanitize error messages (remove sensitive data) | 🔒 Security | MEDIUM | 4h | ⬜ Todo | None |
| **SEC-011** | Add input validation for user queries | 🔒 Security | MEDIUM | 6h | ⬜ Todo | None |
| **SEC-012** | Add Firestore ownership validation | 🔒 Security | MEDIUM | 4h | ⬜ Todo | SEC-006 |

**Sprint Goal**: Establish comprehensive testing and final security improvements

---

## P3 - LOW (Backlog)

### Future Improvements

| ID | Task | Type | Severity | Effort | Status | Dependencies |
|----|------|------|----------|--------|--------|--------------|
| **QUAL-006** | Standardize naming conventions (PEP 8) | 🐛 Bug | LOW | 8h | ⬜ Backlog | None |
| **QUAL-007** | Add comprehensive docstrings | 🐛 Bug | LOW | 12h | ⬜ Backlog | None |
| **DEBT-007** | Enhance prompt management (versioning, A/B testing) | ⚙️ Tech Debt | MEDIUM | 20h | ⬜ Backlog | None |
| **DEBT-009** | Add request ID tracking for debugging | ⚙️ Tech Debt | LOW | 4h | ⬜ Backlog | None |
| **ARCH-004** | Implement repository pattern | 🏗️ Architecture | MEDIUM | 16h | ⬜ Backlog | ARCH-003 |
| **ARCH-005** | Add API versioning (v1, v2) | 🏗️ Architecture | MEDIUM | 8h | ⬜ Backlog | None |
| **ARCH-006** | Refactor to async workflow execution | 🏗️ Architecture | MEDIUM | 20h | ⬜ Backlog | ARCH-002 |
| **ARCH-007** | Implement event sourcing for workflow state | 🏗️ Architecture | LOW | 24h | ⬜ Backlog | ARCH-006 |
| **CONF-001** | Add environment variable validation | ⚙️ Tech Debt | MEDIUM | 4h | ⬜ Backlog | None |
| **CONF-002** | Separate dev/prod configurations | ⚙️ Tech Debt | MEDIUM | 6h | ⬜ Backlog | CONF-001 |
| **CONF-003** | Remove sensitive policy file from repo | 🔒 Security | LOW | 1h | ⬜ Backlog | None |
| **DEP-001** | Audit and update dependencies | 📦 Dependencies | MEDIUM | 4h | ⬜ Backlog | None |
| **DEP-002** | Implement dependency lock file | 📦 Dependencies | MEDIUM | 2h | ⬜ Backlog | DEP-001 |
| **PERF-001** | Add pagination to conversation queries | ⚡ Performance | MEDIUM | 6h | ⬜ Backlog | None |
| **PERF-002** | Optimize schema fetching (batch + cache) | ⚡ Performance | LOW | 6h | ⬜ Backlog | DEBT-006 |

---

## Sprint Planning

### Recommended Sprint Allocation

#### Sprint 0 (Week 1) - EMERGENCY
- **Focus**: Critical security fixes
- **Tasks**: SEC-001, SEC-002, SEC-003, SEC-013
- **Effort**: 20 hours
- **Team**: 1 senior engineer

#### Sprint 1 (Weeks 2-3)
- **Focus**: Security hardening + CI/CD
- **Tasks**: SEC-004, SEC-005, SEC-006, SEC-007, SEC-008, SEC-010, TEST-003
- **Effort**: 56 hours (~1.5 sprints)
- **Team**: 2 engineers

#### Sprint 2 (Weeks 4-5)
- **Focus**: Code quality & architecture
- **Tasks**: QUAL-001 to QUAL-005, ARCH-001 to ARCH-003
- **Effort**: 84 hours (~2 sprints)
- **Team**: 2-3 engineers

#### Sprint 3 (Weeks 6-7)
- **Focus**: Technical debt
- **Tasks**: DEBT-001 to DEBT-010
- **Effort**: 74 hours (~2 sprints)
- **Team**: 2 engineers

#### Sprint 4 (Weeks 8-10)
- **Focus**: Testing & final security
- **Tasks**: TEST-001, TEST-002, SEC-009, SEC-011, SEC-012
- **Effort**: 56 hours (~1.5 sprints)
- **Team**: 2-3 engineers

**Total Timeline**: ~10 weeks for P0-P2 tasks

---

## Task Dependencies Graph

```
SEC-001 (Rotate credentials)
  ├── SEC-002 (WebSocket auth)
  │     ├── SEC-003 (REST auth)
  │     │     ├── SEC-004 (CORS fix)
  │     │     ├── SEC-010 (Rate limiting)
  │     │     └── SEC-013 (Secure Railway deployment)
  │     └── ...
  └── SEC-008 (Remove hardcoded creds)

ARCH-001 (LLM abstraction)
  └── ARCH-002 (Workflow refactor)
        └── ARCH-003 (Service layer)
              ├── ARCH-004 (Repository pattern)
              ├── TEST-001 (Unit tests)
              └── DEBT-002 (Dependency injection)

SEC-005 (SQL injection protection)
  └── SEC-006 (User ID validation)
        └── SEC-012 (Firestore ownership)

DEBT-006 (Caching)
  └── PERF-002 (Optimize schema fetching)

CONF-001 (Env validation)
  └── CONF-002 (Separate configs)
```

---

## Effort Estimation Summary

### By Priority

| Priority | Total Hours | Sprints (2-week) | Engineers Needed |
|----------|-------------|------------------|------------------|
| P0 | 20h | 0.5 | 1 |
| P1 | 56h | 1.5 | 2 |
| P2 | 158h | 4 | 2-3 |
| P3 | 141h | 3.5 | 1-2 |
| **Total** | **375h** | **~9.5 sprints** | **2-3** |

### By Type

| Type | Count | Total Hours | Avg Hours/Task |
|------|-------|-------------|----------------|
| 🔒 Security | 13 | 72h | 5.5h |
| 🐛 Bug/Quality | 7 | 48h | 6.8h |
| ⚙️ Tech Debt | 10 | 78h | 7.8h |
| 🏗️ Architecture | 7 | 116h | 16.6h |
| 🧪 Testing | 3 | 58h | 19.3h |
| 📦 Dependencies | 2 | 6h | 3h |
| ⚡ Performance | 2 | 12h | 6h |

---

## Risk Assessment

### High Risk Items

| ID | Risk | Impact | Mitigation |
|----|------|--------|------------|
| SEC-001 | Credentials already compromised | CRITICAL | Rotate immediately, check AWS CloudTrail for unauthorized access |
| SEC-002/003 | Production system vulnerable | CRITICAL | Implement auth ASAP, consider temporary IP whitelist |
| SEC-013 | Railway production API publicly accessible | CRITICAL | Use only test data until auth implemented, don't share URL publicly |
| TEST-001 | No test coverage = regression risk | HIGH | Write tests alongside refactoring, not after |
| ARCH-003 | Large refactor may introduce bugs | HIGH | Incremental changes, feature flags, canary deployments |
| DEBT-002 | DI refactor touches entire codebase | HIGH | Use adapter pattern for gradual migration |

### Dependencies on External Factors

| Task | External Dependency | Risk Level | Notes |
|------|---------------------|------------|-------|
| SEC-008 | AWS IAM role setup | MEDIUM | DevOps team needed |
| DEBT-010 | Prometheus infrastructure | MEDIUM | Requires infrastructure team |
| DEBT-006 | Redis instance | LOW | Can use managed service |
| TEST-003 | CI/CD platform decision | LOW | GitHub Actions recommended |

---

## Success Metrics

### Sprint 0-1 (Security)
- ✅ All API endpoints require authentication
- ✅ No exposed credentials in codebase or git history
- ✅ CORS configured with specific origins
- ✅ Rate limiting active on all endpoints
- ✅ CI/CD pipeline running security scans

### Sprint 2-3 (Quality & Architecture)
- ✅ Code coverage >80%
- ✅ All functions <50 lines
- ✅ Zero bare `except Exception` blocks
- ✅ Service layer implemented
- ✅ LLM provider abstraction in place
- ✅ Retry logic on all external calls

### Sprint 4+ (Production Ready)
- ✅ Health checks passing
- ✅ Metrics dashboard operational
- ✅ All P0-P1 tasks complete
- ✅ Load testing passed
- ✅ Security audit passed

---

## Notes & Decisions

### Architectural Decisions

**2025-10-06**: Decision to implement service layer before repository pattern
- **Rationale**: Service layer provides immediate value for testing
- **Alternative Considered**: Repository pattern first
- **Trade-off**: May need minor refactor when adding repositories

**2025-10-06**: JWT chosen over session-based auth
- **Rationale**: Stateless, works well with WebSockets
- **Alternative Considered**: Session cookies with Redis
- **Trade-off**: Need secure token storage on frontend

### Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Rate Limiting | slowapi | Native FastAPI integration |
| Retry Logic | tenacity | Declarative, well-maintained |
| Metrics | Prometheus | Industry standard, great ecosystem |
| Testing | pytest | Python standard, good fixtures |
| CI/CD | GitHub Actions | Free for public repos, good integrations |
| Caching | Redis | Fast, persistent, supports complex structures |

---

## Weekly Status Template

### Week of [DATE]

**Sprint**: [Sprint Number]
**Focus**: [Sprint Goal]

#### Completed
- [ ] Task ID - Description (Xh)

#### In Progress
- [ ] Task ID - Description (Xh remaining)

#### Blocked
- [ ] Task ID - Description - Blocker reason

#### Next Week
- [ ] Task ID - Description (Xh estimated)

#### Risks & Issues
- None / [Description]

#### Metrics
- Code Coverage: X%
- Open Security Issues: X
- Test Pass Rate: X%

---

## Contact & Ownership

| Area | Owner | Backup |
|------|-------|--------|
| Security (P0) | [TBD] | [TBD] |
| Architecture | [TBD] | [TBD] |
| Testing | [TBD] | [TBD] |
| DevOps/CI/CD | [TBD] | [TBD] |

---

**Document Status**: Active
**Next Review**: Weekly during sprints
**Last Updated**: 2025-10-11

---

## Recent Updates

### 2025-10-11
- **Added SEC-013**: Railway production deployment security
  - Documented 5 critical vulnerabilities in production deployment
  - Added JWT authentication implementation guide
  - Added CORS and rate limiting fixes
  - Status: Firestore connection fixed (ENVIRONMENT=production set)
  - Post-demo action required: Implement full authentication stack
