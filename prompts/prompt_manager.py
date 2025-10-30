"""
Prompt management system for agent prompts and knowledge bases.

Cache Version: 2025-10-30-v4 (Force reload after GA table rename from ga_* to google_analytics_*)
"""
from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json
from datetime import datetime


class PromptManager:
    """
    Centralized prompt management system.

    Features:
    - Load prompts from YAML/JSON files
    - Version control for prompts
    - Inject knowledge bases into prompts
    - Track prompt usage and performance
    """

    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize prompt manager.

        Args:
            prompts_dir: Directory containing prompt files
        """
        self.prompts_dir = Path(prompts_dir)
        self.agents_dir = self.prompts_dir / "agents"
        self.knowledge_dir = self.prompts_dir / "knowledge"
        self.templates_dir = self.prompts_dir / "templates"

        # Cache for loaded prompts
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}
        self._knowledge_cache: Dict[str, str] = {}

    def get_agent_prompt(
        self,
        agent_name: str,
        version: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get prompt for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., 'planner', 'data_analytics')
            version: Optional specific version (defaults to 'latest')
            variables: Variables to inject into the prompt template

        Returns:
            Formatted prompt string
        """
        version = version or "latest"
        cache_key = f"{agent_name}:{version}"

        # Check cache
        if cache_key not in self._prompt_cache:
            self._load_agent_prompt(agent_name, version)

        prompt_data = self._prompt_cache.get(cache_key, {})
        prompt_template = prompt_data.get("prompt", "")

        # Inject knowledge bases FIRST (before variable substitution)
        knowledge_refs = prompt_data.get("knowledge_bases", [])
        for kb_name in knowledge_refs:
            kb_content = self.get_knowledge_base(kb_name)
            # Use a different marker that won't conflict with format strings
            prompt_template = prompt_template.replace(
                f"{{{{KNOWLEDGE:{kb_name}}}}}", kb_content
            )

        # Then inject variables
        if variables:
            prompt_template = prompt_template.format(**variables)

        return prompt_template

    def get_knowledge_base(self, kb_name: str) -> str:
        """
        Load a knowledge base file.

        Args:
            kb_name: Name of knowledge base (e.g., 'athena_best_practices')

        Returns:
            Knowledge base content as string
        """
        if kb_name not in self._knowledge_cache:
            kb_path = self.knowledge_dir / f"{kb_name}.md"

            if not kb_path.exists():
                return f"[Knowledge base '{kb_name}' not found]"

            with open(kb_path, "r") as f:
                self._knowledge_cache[kb_name] = f.read()

        return self._knowledge_cache[kb_name]

    def _load_agent_prompt(self, agent_name: str, version: str):
        """Load agent prompt from file."""
        # Try version-specific file first
        prompt_path = self.agents_dir / f"{agent_name}.v{version}.yaml"

        # Fallback to non-versioned file
        if not prompt_path.exists():
            prompt_path = self.agents_dir / f"{agent_name}.yaml"

        if not prompt_path.exists():
            # Fallback to empty prompt
            self._prompt_cache[f"{agent_name}:{version}"] = {
                "prompt": "",
                "metadata": {}
            }
            return

        with open(prompt_path, "r") as f:
            prompt_data = yaml.safe_load(f)

        cache_key = f"{agent_name}:{version}"
        self._prompt_cache[cache_key] = prompt_data

    def save_agent_prompt(
        self,
        agent_name: str,
        prompt: str,
        version: str = "latest",
        metadata: Optional[Dict[str, Any]] = None,
        knowledge_bases: Optional[list] = None
    ):
        """
        Save an agent prompt to file.

        Args:
            agent_name: Name of the agent
            prompt: Prompt text
            version: Version identifier
            metadata: Optional metadata (description, author, etc.)
            knowledge_bases: List of knowledge base names to inject
        """
        prompt_data = {
            "version": version,
            "prompt": prompt,
            "metadata": metadata or {
                "created_at": datetime.now().isoformat(),
                "description": f"Prompt for {agent_name} agent"
            },
            "knowledge_bases": knowledge_bases or []
        }

        # Save to file
        filename = f"{agent_name}.v{version}.yaml" if version != "latest" else f"{agent_name}.yaml"
        filepath = self.agents_dir / filename

        with open(filepath, "w") as f:
            yaml.dump(prompt_data, f, default_flow_style=False, sort_keys=False)

        # Update cache
        cache_key = f"{agent_name}:{version}"
        self._prompt_cache[cache_key] = prompt_data

    def list_agent_prompts(self, agent_name: str) -> list:
        """List all versions of an agent's prompts."""
        versions = []
        for prompt_file in self.agents_dir.glob(f"{agent_name}*.yaml"):
            if ".v" in prompt_file.stem:
                version = prompt_file.stem.split(".v")[1]
            else:
                version = "latest"
            versions.append(version)
        return versions

    def clear_cache(self):
        """Clear the prompt cache (useful when prompts are updated)."""
        self._prompt_cache.clear()
        self._knowledge_cache.clear()


# Global instance
prompt_manager = PromptManager()
