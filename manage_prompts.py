#!/usr/bin/env python
"""
CLI tool for managing agent prompts.

Usage:
    python manage_prompts.py list                          # List all agents
    python manage_prompts.py show planner                  # Show planner prompt
    python manage_prompts.py versions planner              # Show all versions
    python manage_prompts.py create new_agent              # Create new agent prompt
    python manage_prompts.py test planner                  # Test planner prompt
"""
import sys
import yaml
from pathlib import Path
from prompts.prompt_manager import prompt_manager


def list_agents():
    """List all available agents."""
    agents_dir = Path("prompts/agents")
    agents = set()

    for yaml_file in agents_dir.glob("*.yaml"):
        agent_name = yaml_file.stem.split(".v")[0]
        agents.add(agent_name)

    print("\n📋 Available Agents:")
    print("=" * 50)
    for agent in sorted(agents):
        versions = prompt_manager.list_agent_prompts(agent)
        print(f"  • {agent} (versions: {', '.join(versions)})")
    print()


def show_prompt(agent_name: str, version: str = "latest"):
    """Show an agent's prompt."""
    prompt_path = Path(f"prompts/agents/{agent_name}.yaml")

    if not prompt_path.exists():
        print(f"❌ Agent '{agent_name}' not found")
        return

    with open(prompt_path) as f:
        data = yaml.safe_load(f)

    print(f"\n🤖 {agent_name.upper()} Agent Prompt")
    print("=" * 50)
    print(f"Version: {data.get('version', 'unknown')}")
    print(f"Description: {data.get('metadata', {}).get('description', 'N/A')}")

    kb = data.get('knowledge_bases', [])
    if kb:
        print(f"Knowledge Bases: {', '.join(kb)}")

    print("\nPrompt:")
    print("-" * 50)
    print(data.get('prompt', 'No prompt found'))
    print()


def list_versions(agent_name: str):
    """List all versions of an agent."""
    versions = prompt_manager.list_agent_prompts(agent_name)

    if not versions:
        print(f"❌ No versions found for agent '{agent_name}'")
        return

    print(f"\n📚 Versions of '{agent_name}':")
    print("=" * 50)
    for version in versions:
        print(f"  • {version}")
    print()


def create_agent(agent_name: str):
    """Create a new agent prompt template."""
    template = f"""version: latest
metadata:
  description: {agent_name.replace('_', ' ').title()} agent
  created_at: 2025-10-05
  author: Photosphere Labs

knowledge_bases:
  - available_agents

prompt: |
  You are a {agent_name.replace('_', ' ').title()} agent.

  Your role is to:
  1. [Define role here]
  2. [Define responsibilities]

  {{{{KNOWLEDGE:available_agents}}}}

  User Context: {{context}}
  Query: {{query}}

  [Add specific instructions here]
"""

    filepath = Path(f"prompts/agents/{agent_name}.yaml")

    if filepath.exists():
        response = input(f"⚠️  Agent '{agent_name}' already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    with open(filepath, 'w') as f:
        f.write(template)

    print(f"✅ Created agent prompt: {filepath}")
    print(f"\nNext steps:")
    print(f"1. Edit the prompt: vim {filepath}")
    print(f"2. Add to workflow: Update workflow/nodes.py")
    print(f"3. Test: python manage_prompts.py test {agent_name}")


def test_prompt(agent_name: str):
    """Test an agent prompt with sample variables."""
    try:
        prompt = prompt_manager.get_agent_prompt(
            agent_name,
            variables={
                "query": "Sample query for testing",
                "context": "Sample context",
                "user_id": "test_user",
                "result": "Sample result",
                "plan_reasoning": "Sample plan"
            }
        )

        print(f"\n🧪 Testing '{agent_name}' prompt")
        print("=" * 50)
        print(prompt)
        print()

    except Exception as e:
        print(f"❌ Error testing prompt: {e}")


def list_knowledge():
    """List all knowledge bases."""
    kb_dir = Path("prompts/knowledge")
    print("\n📚 Knowledge Bases:")
    print("=" * 50)

    for kb_file in sorted(kb_dir.glob("*.md")):
        kb_name = kb_file.stem
        with open(kb_file) as f:
            first_line = f.readline().strip()

        print(f"  • {kb_name}")
        print(f"    {first_line}")
    print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_agents()

    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py show <agent_name>")
            sys.exit(1)
        show_prompt(sys.argv[2])

    elif command == "versions":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py versions <agent_name>")
            sys.exit(1)
        list_versions(sys.argv[2])

    elif command == "create":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py create <agent_name>")
            sys.exit(1)
        create_agent(sys.argv[2])

    elif command == "test":
        if len(sys.argv) < 3:
            print("Usage: python manage_prompts.py test <agent_name>")
            sys.exit(1)
        test_prompt(sys.argv[2])

    elif command == "knowledge":
        list_knowledge()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
