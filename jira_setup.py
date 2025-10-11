#!/usr/bin/env python3
"""
Jira bulk task creation script for ps-labs-agent project.
"""
import requests
import json
from typing import Dict, List, Optional

# Jira Configuration
JIRA_EMAIL = "sagnik@photospherelabs.com"
JIRA_TOKEN = "ATATT3xFfGF0ZwcHnEAlPK5lOJmcG5d9F0vLR99bky9NK0J5meRY5YICJL-13ybOC4iorIASRJuiujJO8z14pjzb1nATQNwbwDS9Cv2FWrfQOzMlMLepk93rNXl5nATduTKkUO1i86OkaLCuWs3IWM5TSaUAN9y18EKO9oxlnJUQZiG9d37jPW0=9C16B523"
JIRA_URL = "https://photospherelabs.atlassian.net"
JIRA_PROJECT = "PSAG"

# Create session
session = requests.Session()
session.auth = (JIRA_EMAIL, JIRA_TOKEN)
session.headers.update({"Content-Type": "application/json"})


def test_connection():
    """Test Jira API connection."""
    try:
        response = session.get(f"{JIRA_URL}/rest/api/3/myself")
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Connected as: {user['displayName']} ({user['emailAddress']})")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_project_info():
    """Get project information."""
    try:
        response = session.get(f"{JIRA_URL}/rest/api/3/project/{JIRA_PROJECT}")
        if response.status_code == 200:
            project = response.json()
            print(f"\n✅ Project: {project['name']} ({project['key']})")
            print(f"   ID: {project['id']}")
            print(f"   Style: {project.get('style', 'classic')}")
            print(f"\n   Issue Types:")
            for it in project.get('issueTypes', []):
                print(f"     - {it['name']:15} (ID: {it['id']})")
            return project
        else:
            print(f"❌ Project not found: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def list_all_projects():
    """List all available projects."""
    try:
        response = session.get(f"{JIRA_URL}/rest/api/3/project")
        if response.status_code == 200:
            projects = response.json()
            print(f"\nAvailable Projects:")
            print("=" * 50)
            for p in projects:
                print(f"  {p['key']:15} - {p['name']}")
            return projects
        else:
            print(f"❌ Failed to list projects: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Jira Setup Test")
    print("=" * 60)

    # Test connection
    if not test_connection():
        exit(1)

    # List all projects
    list_all_projects()

    # Get project info
    get_project_info()
