# Jira Integration Setup Prompt for Other Repositories

**Copy and paste this entire prompt into Claude Code when working on a new repository.**

---

I want to set up Jira project management for this repository following the exact same structure as ps-labs-agent. Here are the details:

## Jira Credentials

**These are already set up and should be reused:**
- **Jira URL**: https://photospherelabs.atlassian.net
- **Email**: sagnik@photospherelabs.com
- **API Token**: (stored in .jira_credentials file)
- **Assignee**: Sagnik (Account ID: 712020:0e79e054-9f07-4f7c-91f3-73834452b521)

**What needs to be different:**
- **Project Key**: [NEW_PROJECT_KEY] (I'll create this in Jira first)
- **Project Name**: [NEW_PROJECT_NAME]

## Setup Tasks

### 1. Analyze Existing Project Management

**Analyze these files to extract tasks:**
- `docs/project_management/*.md` - Look for TODO lists, checklists, task tracking
- `TODO.md` - Extract all pending tasks
- `README.md` - Check for TODO sections or improvement notes
- Code comments - Search for `TODO:`, `FIXME:`, `HACK:`, `XXX:` comments
- Any vulnerability or issues documentation

**Categorize tasks into themes (EPICs):**

Common EPIC themes to consider:
1. **🔒 Security Hardening** - Security vulnerabilities, authentication, authorization, credential management
2. **🏗️ Architecture & Design** - System design, refactoring, design patterns, scalability
3. **🧪 Testing & CI/CD** - Test coverage, integration tests, CI/CD pipeline, automation
4. **🐛 Code Quality & Refactoring** - Error handling, logging, type hints, code smells
5. **⚙️ Technical Debt** - Infrastructure improvements, retry logic, monitoring, observability
6. **⚙️ Configuration & Environment** - Environment setup, secrets management, config validation
7. **⚡ Dependencies & Performance** - Dependency updates, optimization, caching
8. **🚀 Feature Development** - New features, enhancements, capability additions

**Analyze each task and assign:**
- Priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- Effort estimate in hours
- EPIC theme
- Type labels (security, bug, feature, tech-debt, etc.)

### 2. Create Jira Scripts

**Create these files:**

**File: `.jira_credentials`** (Add to .gitignore)
```
JIRA_EMAIL=sagnik@photospherelabs.com
JIRA_TOKEN=<existing_token>
JIRA_URL=https://photospherelabs.atlassian.net
JIRA_PROJECT=[NEW_PROJECT_KEY]
```

**File: `jira_setup.py`** - Connection testing script
- Test Jira API connection
- Verify project exists
- List project info and issue types
- Use same code structure as ps-labs-agent/jira_setup.py

**File: `create_jira_tasks.py`** - Create EPICs and tasks
- Define all EPICs with descriptions
- Define all tasks with full details (Problem, Solution, Acceptance Criteria)
- Use Atlassian Document Format (ADF) for descriptions
- Link tasks to EPICs
- Add labels for priority and type
- Use same code structure as ps-labs-agent/create_jira_tasks.py

**Important code patterns:**
- Load credentials from `.jira_credentials` file (never hardcode)
- Use ADF format for descriptions: `markdown_to_adf()` function
- Include rate limiting: `time.sleep(0.3)` between API calls
- Handle errors gracefully with try/except

### 3. Create Documentation

**File: `docs/project_management/JIRA_INTEGRATION.md`**

Structure:
```markdown
# Jira Integration Guide

## Working with Jira - Core Principles
[5 core principles from ps-labs-agent]

## Epic Organization
[List all EPICs with:
- Theme description
- Focus areas
- When to add tasks here
- Examples]

## Priority Labels
[P0, P1, P2, P3 definitions]

## How to Add Tasks to Jira
[3 methods: Web UI, Python script, REST API]

## Daily Workflow with Jira
[Morning, during work, end of day routines]

## Useful Jira Filters
[JQL queries for common views]

## When to Create New Tasks
[Bugs, improvements, security, tech debt]

## Task Template
[Standard template for creating tasks]

## Credentials Setup
[How to set up .jira_credentials]
```

Use ps-labs-agent's JIRA_INTEGRATION.md as template, but customize for this repo's specific EPICs and workflow.

**File: `docs/JIRA_SETUP_SUMMARY.md`**

Document the migration:
- What was created (X EPICs, Y tasks)
- Migration stats
- EPIC breakdown
- Technical implementation details
- Scripts created
- API details
- Success criteria

Use ps-labs-agent's JIRA_SETUP_SUMMARY.md as template.

### 4. Update CLAUDE.md (Project Instructions)

**Add this section to CLAUDE.md:**

```markdown
## Project Management

**⚠️ CRITICAL**: This project works VERY closely with Jira for all task management.

### Jira Integration (PRIMARY)

**Jira Project**: [PROJECT_NAME] (Key: [PROJECT_KEY])
**Board**: https://photospherelabs.atlassian.net/jira/software/projects/[PROJECT_KEY]/board
**All Tasks**: https://photospherelabs.atlassian.net/browse/[PROJECT_KEY]

**When working on this codebase, you MUST**:

1. **Before Starting Work**: Check Jira board for current tasks and priorities
2. **During Development**: Reference Jira task IDs in commits and comments
3. **When Finding Issues**: Create new Jira tasks immediately (don't just note in code)
4. **When Seeing Improvements**: Add tasks to Jira backlog with appropriate priority (P0/P1/P2/P3)
5. **After Completing Work**: Update Jira task status to Done

**Detailed Jira Workflow**: See [docs/project_management/JIRA_INTEGRATION.md](docs/project_management/JIRA_INTEGRATION.md)

### TODO.md (Secondary)

**TODO Tracking**: This project maintains [TODO.md](TODO.md) for high-level implementation notes:
- Check TODO.md for current work-in-progress implementation details
- Update TODO.md when working on complex multi-step features
- Use TODO.md for technical notes, but use Jira for task tracking
```

### 5. Clean Up Duplicate Information

**In `docs/project_management/` files:**

Remove detailed task lists and checklists. Replace with:
- Links to Jira board
- JQL queries to view specific task types
- High-level summaries only

**Example transformation:**

**Before:**
```markdown
## Security Tasks

- [ ] SEC-001: Rotate API keys
  - [ ] Generate new keys
  - [ ] Update services
  - [ ] Revoke old keys
- [ ] SEC-002: Add authentication
  - [ ] Implement JWT
  - [ ] Add middleware
```

**After:**
```markdown
## Security Tasks

**All security tasks tracked in Jira**: https://photospherelabs.atlassian.net/browse/[PROJECT_KEY]

**Priority P0 Tasks**:
- [PROJECT_KEY]-X: [SEC-001] Rotate API keys
- [PROJECT_KEY]-Y: [SEC-002] Add authentication

**View all security tasks**: `project = [PROJECT_KEY] AND labels = security`
```

**Keep these files for reference:**
- Deployment guides (deployment_plan.md, railway_deployment_guide.md)
- Architecture documentation
- Technical specifications
- API documentation

**But remove:**
- Detailed task checklists
- Task descriptions and acceptance criteria (now in Jira)
- Sprint planning details (now in Jira)

### 6. Update .gitignore

Add to .gitignore:
```
# Jira credentials
.jira_credentials
```

### 7. Migration Workflow

**Step-by-step process:**

1. Create Jira project at https://photospherelabs.atlassian.net
   - Select Kanban (for solo developer speed)
   - Set project key (e.g., "MYPROJ")
   - Set default assignee to Sagnik

2. Create `.jira_credentials` file with credentials

3. Test connection:
   ```bash
   python jira_setup.py
   ```

4. Review and customize EPICs and tasks in `create_jira_tasks.py`

5. Create EPICs and tasks:
   ```bash
   python create_jira_tasks.py
   ```

6. Create documentation:
   - Write JIRA_INTEGRATION.md
   - Write JIRA_SETUP_SUMMARY.md
   - Update CLAUDE.md

7. Clean up duplicate information:
   - Review all files in docs/project_management/
   - Replace task checklists with Jira links
   - Keep architectural/deployment docs

8. Update project_management.md:
   - Add Jira links at top
   - List EPICs
   - Show high-level stats
   - Remove detailed task tracking

9. Commit changes:
   ```bash
   git add .jira_credentials .gitignore
   git add jira_setup.py create_jira_tasks.py
   git add docs/
   git add CLAUDE.md
   git commit -m "feat: Set up Jira project management integration"
   ```

## Expected Outcome

After setup, this repo will have:

✅ **Jira Project** with all tasks organized by EPICs
✅ **JIRA_INTEGRATION.md** with comprehensive workflow guide
✅ **JIRA_SETUP_SUMMARY.md** documenting the migration
✅ **Updated CLAUDE.md** with Jira workflow instructions
✅ **Clean docs/project_management/** with no duplicate task tracking
✅ **Scripts** for creating tasks (jira_setup.py, create_jira_tasks.py)
✅ **Single source of truth** for all tasks (Jira)

## Reference Repository

See **ps-labs-agent** repository for complete working example:
- jira_setup.py
- create_jira_tasks.py
- add_remaining_tasks.py
- docs/project_management/JIRA_INTEGRATION.md
- docs/JIRA_SETUP_SUMMARY.md
- CLAUDE.md (Project Management section)

## Important Notes

1. **Never hardcode credentials** - Always load from .jira_credentials
2. **Use ADF format** for Jira descriptions (next-gen requirement)
3. **Rate limit API calls** - Add 0.3s sleep between requests
4. **Priority via labels** - Next-gen Kanban uses labels, not priority field
5. **No story points** - Use effort estimates in hours instead
6. **Document everything** - Migration stats, EPIC organization, workflows

---

**Now please:**
1. Analyze this repository's existing task management
2. Categorize tasks into appropriate EPICs
3. Create the Jira scripts (.jira_credentials, jira_setup.py, create_jira_tasks.py)
4. Create the documentation (JIRA_INTEGRATION.md, JIRA_SETUP_SUMMARY.md)
5. Update CLAUDE.md with Jira workflow instructions
6. Clean up duplicate information from docs/project_management/
7. Execute the migration workflow
8. Verify everything works

Let me know when you're ready to start!
