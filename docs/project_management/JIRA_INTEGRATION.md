# Jira Integration Guide

**Project**: PSAGENT (Key: PSAG)
**Platform**: Photosphere Labs Jira
**URL**: https://photospherelabs.atlassian.net/browse/PSAG
**Board**: https://photospherelabs.atlassian.net/jira/software/projects/PSAG/board

---

## Working with Jira - Core Principles

**⚠️ IMPORTANT**: This project works VERY closely with Jira for all task management. When working on this codebase:

1. **Before Starting Work**: Check Jira for current tasks and priorities
2. **During Development**: Update task status (To Do → In Progress → Done)
3. **When Finding Issues**: Create new Jira tasks immediately
4. **When Seeing Improvements**: Add tasks to Jira backlog with appropriate priority
5. **After Completing Work**: Mark tasks as Done and update TODO.md if needed

### Single Source of Truth

- **Jira** = Task tracking, priorities, sprints, status
- **TODO.md** = High-level implementation notes and current work in progress
- **This Document** = How to work with Jira

---

## Epic Organization

All tasks are organized into 8 EPICs by theme:

### PSAG-1: 🔒 Security Hardening (13 tasks)
**Theme**: Critical security vulnerabilities and hardening
**Focus Areas**:
- Credential rotation and management
- Authentication & authorization (JWT)
- CORS and rate limiting
- SQL injection protection
- Input validation and sanitization
- Production deployment security

**When to Add Tasks Here**:
- Security vulnerabilities discovered
- Authentication/authorization gaps
- API security issues
- Data exposure risks

---

### PSAG-2: 🏗️ Architecture & Design (7 tasks)
**Theme**: System design improvements and refactoring
**Focus Areas**:
- LLM provider abstraction layer
- Service layer architecture
- Repository pattern implementation
- Dependency injection
- API versioning
- Event sourcing for workflow state

**When to Add Tasks Here**:
- Major architectural changes
- Design pattern implementations
- System refactoring needs
- Scalability improvements

---

### PSAG-3: 🧪 Testing & CI/CD (3 tasks)
**Theme**: Test coverage and continuous integration
**Focus Areas**:
- Unit test suite (>80% coverage)
- Integration tests
- CI/CD pipeline with security scanning
- Test organization and fixtures
- Automated testing on PRs

**When to Add Tasks Here**:
- Testing gaps discovered
- CI/CD improvements needed
- Test coverage issues
- Build/deployment automation

---

### PSAG-4: 🐛 Code Quality & Refactoring (7 tasks)
**Theme**: Code quality improvements and bug fixes
**Focus Areas**:
- Error handling refactoring
- Logging improvements
- Type hints
- Magic value extraction
- Function size reduction
- Naming conventions

**When to Add Tasks Here**:
- Code smell detected
- Bugs found
- Readability issues
- Linting/formatting problems

---

### PSAG-5: ⚙️ Technical Debt (10 tasks)
**Theme**: Technical debt paydown and infrastructure
**Focus Areas**:
- Firebase initialization refactoring
- Dependency injection
- Retry logic for external services
- Connection pooling
- Caching strategy (Redis)
- Health checks and monitoring
- Metrics (Prometheus)

**When to Add Tasks Here**:
- Technical debt accumulating
- Infrastructure improvements needed
- Performance bottlenecks
- Monitoring/observability gaps

---

### PSAG-6: ⚙️ Configuration & Environment (3 tasks)
**Theme**: Configuration management and environment setup
**Focus Areas**:
- Environment variable validation
- Separate dev/prod configurations
- Remove sensitive files from repo
- LLM model configuration
- Secrets management

**When to Add Tasks Here**:
- Configuration issues
- Environment setup problems
- Secrets management needs

---

### PSAG-7: ⚡ Dependencies & Performance (4 tasks)
**Theme**: Dependencies and performance optimization
**Focus Areas**:
- Dependency audit and updates
- Dependency lock file
- Pagination for large queries
- Schema fetching optimization

**When to Add Tasks Here**:
- Performance issues discovered
- Dependency vulnerabilities
- Optimization opportunities

---

### PSAG-55: 🚀 Feature Development
**Theme**: New feature development and multi-agent system enhancements
**Focus Areas**:
- New agent implementations (Competitor Intelligence, Creative Agent, Financial Analyst, Media Planner, Sentiment Analyst)
- Enhanced LLM capabilities and prompt improvements
- New data sources and integrations (Meta Ads Library, web scraping, P&L data)
- User experience improvements
- Frontend integration and API enhancements
- Conversation management features (title generation, history, context)
- Agent orchestration improvements (parallel execution, workflow optimization)
- Tool development for specialized agents

**When to Add Tasks Here**:
- New feature requests
- Agent capability enhancements
- New data source integrations
- UX/UI improvements
- API endpoint additions
- Conversation features
- Agent coordination improvements
- Tool implementations

**Examples**:
- Implement Competitor Intelligence Agent with Meta Ads Library integration
- Add creative generation capabilities with DALL-E/Midjourney
- Build Financial Analyst Agent for P&L analysis and forecasting
- Create Media Planner Agent for budget optimization
- Add sentiment analysis agent with web scraping
- Enhance conversation title generation
- Add conversation search and filtering
- Implement agent result caching
- Add streaming response improvements

---

## Priority Labels

Tasks are prioritized using labels (next-gen Jira doesn't have priority field):

- **P0 (CRITICAL)**: Security issues, production blockers, data loss risks
- **P1 (HIGH)**: Important features, significant bugs, security hardening
- **P2 (MEDIUM)**: Quality improvements, technical debt, nice-to-haves
- **P3 (LOW)**: Future enhancements, low-priority refactoring, backlog items

---

## How to Add Tasks to Jira

### Method 1: Via Jira Web UI (Recommended for Quick Tasks)

1. Go to https://photospherelabs.atlassian.net/browse/PSAG
2. Click "Create" button
3. Fill in:
   - **Issue Type**: Task
   - **Summary**: [ID] Brief description (e.g., "[SEC-014] Add API key rotation")
   - **Description**: Problem, solution, acceptance criteria
   - **Epic Link**: Select appropriate EPIC (Security, Architecture, etc.)
   - **Labels**: Add priority (P0/P1/P2/P3) and type (security, bug, etc.)
   - **Assignee**: Sagnik (default)
4. Click "Create"

### Method 2: Via Python Script (For Bulk Tasks)

Use the existing scripts:

```bash
# For single tasks with full descriptions
python create_jira_tasks.py  # Modify TASKS list first

# For bulk simple tasks
python add_remaining_tasks.py  # Add to TASKS list
```

### Method 3: Via Jira REST API (For Automation)

```python
import requests

session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_TOKEN)

payload = {
    "fields": {
        "project": {"key": "PSAG"},
        "issuetype": {"id": "10008"},  # Task
        "summary": "[TASK-ID] Task summary",
        "description": {
            "version": 1,
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": "Task description"}]
            }]
        },
        "labels": ["P2", "bug"],
        "assignee": {"accountId": "712020:0e79e054-9f07-4f7c-91f3-73834452b521"},
        "parent": {"key": "PSAG-4"}  # Epic link
    }
}

response = session.post(
    "https://photospherelabs.atlassian.net/rest/api/3/issue",
    json=payload
)
```

---

## Daily Workflow with Jira

### Morning
1. Open Jira board: https://photospherelabs.atlassian.net/jira/software/projects/PSAG/board
2. Review "In Progress" tasks
3. Check "To Do" for next priority tasks
4. Move task to "In Progress" before starting work

### During Work
1. Update task description with findings/notes
2. Add comments for blockers or questions
3. If you discover new issues → Create new Jira task immediately
4. If task scope grows → Split into multiple tasks

### End of Day
1. Update task status
2. Add comments on progress
3. Move completed tasks to "Done"
4. Plan next day's tasks

---

## Useful Jira Filters

Create these filters for easier navigation:

```jql
# P0 Critical Tasks
project = PSAG AND labels = P0 AND status != Done

# Current Sprint (P0 + P1)
project = PSAG AND labels IN (P0, P1) AND status != Done

# My In Progress
project = PSAG AND assignee = currentUser() AND status = "In Progress"

# Security Tasks
project = PSAG AND labels = security AND status != Done

# Blocked Tasks
project = PSAG AND status = Blocked
```

---

## When to Create New Tasks

### Bugs Found
1. Create task immediately
2. Add label: `bug`, `P1` or `P2` (depending on severity)
3. Link to appropriate EPIC (usually Quality or Security)
4. Add reproduction steps and error logs

### Improvement Opportunities
1. Create task with label `P2` or `P3`
2. Add description of current state vs desired state
3. Link to appropriate EPIC (Architecture, Tech Debt, etc.)
4. Add to backlog

### Security Issues
1. **CRITICAL**: Create task with `P0` label
2. Add label: `security`
3. Link to Security Hardening EPIC (PSAG-1)
4. Add details: vulnerability, impact, mitigation steps

### Technical Debt
1. Create task with label `tech-debt`, `P2` or `P3`
2. Link to Technical Debt EPIC (PSAG-5)
3. Add description: what's wrong, why it's debt, how to fix

---

## Task Template

Use this template when creating tasks:

```markdown
## Problem
[Brief description of the issue or need]

## Current State
[How things work now]

## Desired State
[How things should work]

## Solution
[Proposed approach to fix/implement]

## Implementation Notes
[Technical details, file paths, code snippets]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass
- [ ] Documentation updated

## Dependencies
[List of tasks that must be completed first]

## References
[Links to docs, issues, PRs]
```

---

## Credentials Setup

To use Jira scripts, create `.jira_credentials` file (already in .gitignore):

```bash
JIRA_EMAIL=sagnik@photospherelabs.com
JIRA_TOKEN=your_jira_api_token_here
JIRA_URL=https://photospherelabs.atlassian.net
JIRA_PROJECT=PSAG
```

Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens

---

## References

- **Jira Board**: https://photospherelabs.atlassian.net/jira/software/projects/PSAG/board
- **All Tasks**: https://photospherelabs.atlassian.net/browse/PSAG
- **Setup Summary**: [docs/JIRA_SETUP_SUMMARY.md](../JIRA_SETUP_SUMMARY.md)
- **Project Management**: [docs/project_management/project_management.md](project_management.md)
- **Jira REST API Docs**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/

---

<!--
## PROMPT FOR SETTING UP JIRA INTEGRATION IN OTHER REPOS

Use this prompt to set up similar Jira integration in other repositories:

```
I want to set up Jira project management for this repository following best practices. Here's what I need:

1. **Project Setup**:
   - Project name: [YOUR_PROJECT_NAME]
   - Project key: [4-LETTER_KEY]
   - Project type: Kanban (for solo developer speed)
   - Default assignee: [YOUR_NAME/EMAIL]

2. **Epic Organization**:
   Analyze the codebase and create EPICs for:
   - Security (authentication, authorization, vulnerabilities)
   - Architecture (design patterns, refactoring, scalability)
   - Testing (unit tests, integration tests, CI/CD)
   - Code Quality (bugs, code smells, technical debt)
   - Performance (optimization, caching, database)
   - Configuration (environment setup, secrets management)
   - Dependencies (package updates, security patches)

3. **Task Migration**:
   - Review TODO.md, README.md, and codebase comments
   - Extract all TODOs, FIXMEs, and improvement notes
   - Create Jira tasks with:
     - Descriptive summaries with [TASK-ID] prefix
     - Detailed descriptions (Problem, Solution, Acceptance Criteria)
     - Priority labels (P0=Critical, P1=High, P2=Medium, P3=Low)
     - Type labels (security, bug, feature, tech-debt, etc.)
     - Effort estimates in hours
     - Epic links
     - Dependencies documented

4. **Scripts to Create**:
   - `jira_setup.py` - Connection testing and project info
   - `create_jira_tasks.py` - Create EPICs and tasks
   - `.jira_credentials` - Credentials file (add to .gitignore)

5. **Documentation to Create**:
   - `docs/JIRA_INTEGRATION.md` - How to work with Jira
   - `docs/JIRA_SETUP_SUMMARY.md` - Setup details and stats
   - Update CLAUDE.md - Add Jira workflow instructions
   - Update README.md - Add link to Jira project

6. **Priority Guidelines**:
   - P0 (CRITICAL): Security vulnerabilities, production blockers, data loss
   - P1 (HIGH): Important features, significant bugs, security hardening
   - P2 (MEDIUM): Quality improvements, technical debt, nice-to-haves
   - P3 (LOW): Future enhancements, low-priority refactoring

7. **Workflow Integration**:
   - Daily: Check Jira board before starting work
   - During: Update task status (To Do → In Progress → Done)
   - When finding issues: Create Jira task immediately
   - When seeing improvements: Add to Jira backlog

Please analyze the codebase and create a comprehensive Jira setup following this structure.
```

### What This Setup Achieves

1. **Centralized Task Management**: All tasks in one place (Jira)
2. **Priority Visibility**: Clear priorities with P0/P1/P2/P3 labels
3. **Organized by Theme**: EPICs group related tasks
4. **Progress Tracking**: Kanban board shows status at a glance
5. **Professional Workflow**: Industry-standard project management
6. **Easy Collaboration**: Ready for team growth
7. **Documentation**: Clear instructions for daily use
8. **Automation Ready**: Scripts for bulk task creation
9. **Security**: Credentials in gitignored file
10. **Single Source of Truth**: No duplicate task tracking

### Key Files Created

- `jira_setup.py` - Test connection and get project info
- `create_jira_tasks.py` - Create EPICs and detailed tasks
- `add_remaining_tasks.py` - Bulk create simple tasks
- `.jira_credentials` - API credentials (excluded from git)
- `docs/JIRA_INTEGRATION.md` - This guide
- `docs/JIRA_SETUP_SUMMARY.md` - Setup summary with statistics
- Updated `CLAUDE.md` - Jira workflow in project instructions

### Customization Points

When adapting for other repos, customize:
1. EPIC themes (match your project's needs)
2. Priority criteria (adjust P0/P1/P2/P3 definitions)
3. Task ID prefixes (SEC, ARCH, TEST, etc.)
4. Workflow states (To Do, In Progress, Done, Blocked)
5. Labels and custom fields
6. Sprint duration and capacity planning

-->
