#!/usr/bin/env python3
"""
Add remaining 33 tasks to Jira (P2 and P3 tasks).
"""
import requests
import time
from typing import Dict, Optional

# Jira Configuration
JIRA_EMAIL = "sagnik@photospherelabs.com"
JIRA_TOKEN = "ATATT3xFfGF0ZwcHnEAlPK5lOJmcG5d9F0vLR99bky9NK0J5meRY5YICJL-13ybOC4iorIASRJuiujJO8z14pjzb1nATQNwbwDS9Cv2FWrfQOzMlMLepk93rNXl5nATduTKkUO1i86OkaLCuWs3IWM5TSaUAN9y18EKO9oxlnJUQZiG9d37jPW0=9C16B523"
JIRA_URL = "https://photospherelabs.atlassian.net"
JIRA_PROJECT = "PSAG"
ASSIGNEE_ACCOUNT_ID = "712020:0e79e054-9f07-4f7c-91f3-73834452b521"
ISSUE_TYPE_TASK = "10008"

session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_TOKEN)
session.headers.update({"Content-Type": "application/json"})

# EPIC keys (from previous run)
EPIC_KEYS = {
    "Security Hardening": "PSAG-1",
    "Architecture & Design": "PSAG-2",
    "Testing & CI/CD": "PSAG-3",
    "Code Quality & Refactoring": "PSAG-4",
    "Technical Debt": "PSAG-5",
    "Configuration & Environment": "PSAG-6",
    "Dependencies & Performance": "PSAG-7",
}


def adf(text: str):
    """Create simple ADF paragraph."""
    return {
        "version": 1,
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    }


def create_task(task_id, summary, effort, epic_name, labels, description):
    """Create task in Jira."""
    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "issuetype": {"id": ISSUE_TYPE_TASK},
            "summary": f"[{task_id}] {summary}",
            "description": adf(description),
            "labels": labels,
            "assignee": {"accountId": ASSIGNEE_ACCOUNT_ID},
            "parent": {"key": EPIC_KEYS[epic_name]}
        }
    }

    try:
        response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=payload)
        if response.status_code == 201:
            key = response.json()["key"]
            print(f"✅ {key} - [{task_id}] {summary[:50]}... ({effort})")
            return key
        else:
            print(f"❌ Failed [{task_id}]: {response.text[:150]}")
    except Exception as e:
        print(f"❌ Error [{task_id}]: {e}")
    return None


# Define all remaining tasks
TASKS = [
    # P2 - Quality
    ("QUAL-001", "Refactor error handling (remove bare except)", "12h", "Code Quality & Refactoring", ["quality", "bug", "P2"], "Remove all bare except blocks and implement proper error handling with specific exceptions. Add logging for all caught exceptions."),
    ("QUAL-002", "Replace print statements with proper logging", "4h", "Code Quality & Refactoring", ["quality", "bug", "P2"], "Replace all print() calls with structured logging (logging.info, logging.error, etc.). Configure log levels and formats."),
    ("QUAL-003", "Add type hints to all public methods", "8h", "Code Quality & Refactoring", ["quality", "P2"], "Add Python type hints to all function signatures and class attributes for better IDE support and type checking."),
    ("QUAL-004", "Extract magic values to constants/config", "4h", "Code Quality & Refactoring", ["quality", "P2"], "Move hardcoded values (timeouts, retries, limits) to constants or configuration files."),
    ("QUAL-005", "Break down large functions (<50 lines)", "12h", "Code Quality & Refactoring", ["quality", "P2"], "Refactor functions over 50 lines into smaller, focused functions following single responsibility principle."),
    ("QUAL-006", "Standardize naming conventions (PEP 8)", "8h", "Code Quality & Refactoring", ["quality", "P3"], "Ensure all code follows PEP 8 naming conventions for variables, functions, classes, and modules."),
    ("QUAL-007", "Add comprehensive docstrings", "12h", "Code Quality & Refactoring", ["quality", "P3"], "Add docstrings to all modules, classes, and functions following Google or NumPy docstring format."),

    # P2 - Architecture
    ("ARCH-001", "Create LLM provider abstraction layer", "12h", "Architecture & Design", ["architecture", "P2"], "Abstract LLM calls (OpenAI, Anthropic) behind interface to allow easy provider switching and testing."),
    ("ARCH-002", "Separate concerns in workflow nodes", "16h", "Architecture & Design", ["architecture", "P2"], "Refactor workflow nodes to separate business logic from LangGraph orchestration. Create service classes."),
    ("ARCH-003", "Implement service layer architecture", "20h", "Architecture & Design", ["architecture", "P2"], "Create service layer between API endpoints and business logic for better separation of concerns and testability."),
    ("ARCH-004", "Implement repository pattern", "16h", "Architecture & Design", ["architecture", "P3"], "Abstract database/Firestore access behind repository interfaces for cleaner data access layer."),
    ("ARCH-005", "Add API versioning (v1, v2)", "8h", "Architecture & Design", ["architecture", "P3"], "Implement API versioning to allow backward-compatible changes and future API iterations."),
    ("ARCH-006", "Refactor to async workflow execution", "20h", "Architecture & Design", ["architecture", "P3"], "Optimize workflow execution with async/await patterns for better concurrency and performance."),
    ("ARCH-007", "Implement event sourcing for workflow state", "24h", "Architecture & Design", ["architecture", "P3"], "Add event sourcing pattern to track workflow state changes for debugging and audit trails."),

    # P2 - Tech Debt
    ("DEBT-001", "Refactor Firebase initialization (singleton)", "4h", "Technical Debt", ["tech-debt", "P2"], "Implement singleton pattern for Firebase initialization to avoid multiple initialization calls."),
    ("DEBT-002", "Replace global singletons with dependency injection", "16h", "Technical Debt", ["tech-debt", "P2"], "Remove global singletons and implement dependency injection pattern for better testing and flexibility."),
    ("DEBT-003", "Add retry logic for external services (tenacity)", "8h", "Technical Debt", ["tech-debt", "P2"], "Implement retry logic with exponential backoff for all external API calls (OpenAI, Athena, Firebase)."),
    ("DEBT-004", "Move LLM models to configuration", "4h", "Technical Debt", ["tech-debt", "P2"], "Extract hardcoded LLM model names to configuration for easier testing and model switching."),
    ("DEBT-005", "Implement database connection pooling", "8h", "Technical Debt", ["tech-debt", "P2"], "Add connection pooling for Athena and Firestore connections to improve performance and resource usage."),
    ("DEBT-006", "Add caching strategy (Redis/in-memory)", "12h", "Technical Debt", ["tech-debt", "P2"], "Implement caching for table schemas, user profiles, and frequent queries using Redis or in-memory cache."),
    ("DEBT-007", "Enhance prompt management (versioning, A/B)", "20h", "Technical Debt", ["tech-debt", "P3"], "Add prompt versioning and A/B testing framework for experimenting with different prompts."),
    ("DEBT-008", "Add comprehensive health checks", "6h", "Technical Debt", ["tech-debt", "P2"], "Implement health check endpoints for Firebase, Athena, OpenAI connections with status monitoring."),
    ("DEBT-009", "Add request ID tracking for debugging", "4h", "Technical Debt", ["tech-debt", "P3"], "Implement request ID tracking across all logs and API calls for easier debugging and tracing."),
    ("DEBT-010", "Implement metrics and monitoring (Prometheus)", "16h", "Technical Debt", ["tech-debt", "P2"], "Add Prometheus metrics for request latency, error rates, and system health monitoring."),

    # P2 - Testing
    ("TEST-001", "Create unit test suite (>80% coverage)", "40h", "Testing & CI/CD", ["testing", "P2"], "Write comprehensive unit tests for all modules with >80% code coverage. Use pytest fixtures and mocks."),
    ("TEST-002", "Reorganize test files (move to tests/)", "2h", "Testing & CI/CD", ["testing", "P3"], "Move all test files from root to tests/ directory with proper structure (tests/unit, tests/integration)."),

    # P2 - Security
    ("SEC-009", "Sanitize error messages (remove sensitive data)", "4h", "Security Hardening", ["security", "P2"], "Ensure error messages don't leak sensitive information (credentials, user data, internal paths)."),
    ("SEC-011", "Add input validation for user queries", "6h", "Security Hardening", ["security", "P2"], "Validate and sanitize all user inputs to prevent injection attacks and malformed data."),
    ("SEC-012", "Add Firestore ownership validation", "4h", "Security Hardening", ["security", "P2"], "Ensure Firestore queries include ownership checks so users can only access their own data."),

    # P3 - Configuration
    ("CONF-001", "Add environment variable validation", "4h", "Configuration & Environment", ["configuration", "P3"], "Validate all required environment variables at startup and provide helpful error messages if missing."),
    ("CONF-002", "Separate dev/prod configurations", "6h", "Configuration & Environment", ["configuration", "P3"], "Create separate configuration files for development and production environments."),
    ("CONF-003", "Remove sensitive policy file from repo", "1h", "Configuration & Environment", ["security", "P3"], "Remove athena-policy.json from git history and add to .gitignore."),

    # P3 - Dependencies & Performance
    ("DEP-001", "Audit and update dependencies", "4h", "Dependencies & Performance", ["dependencies", "P3"], "Run dependency audit (safety, pip-audit) and update packages with known vulnerabilities."),
    ("DEP-002", "Implement dependency lock file", "2h", "Dependencies & Performance", ["dependencies", "P3"], "Add requirements-lock.txt or use pipenv/poetry for reproducible builds."),
    ("PERF-001", "Add pagination to conversation queries", "6h", "Dependencies & Performance", ["performance", "P3"], "Implement pagination for /conversations endpoint to handle users with many conversations."),
    ("PERF-002", "Optimize schema fetching (batch + cache)", "6h", "Dependencies & Performance", ["performance", "P3"], "Batch schema fetching and add caching to reduce Athena/Glue API calls."),
]

print("=" * 80)
print(f"Adding {len(TASKS)} remaining tasks to Jira")
print("=" * 80)

created = 0
for task in TASKS:
    if create_task(*task):
        created += 1
    time.sleep(0.3)  # Rate limiting

print("\n" + "=" * 80)
print(f"✅ Created {created}/{len(TASKS)} tasks")
print(f"📊 View all tasks: {JIRA_URL}/browse/{JIRA_PROJECT}")
print("=" * 80)
