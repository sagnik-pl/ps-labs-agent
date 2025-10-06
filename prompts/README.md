# Prompt Management System

This directory contains all agent prompts and knowledge bases for the multi-agent system.

## Directory Structure

```
prompts/
├── agents/           # Agent-specific prompts
│   ├── planner.yaml
│   ├── data_analytics.yaml
│   ├── validator.yaml
│   └── interpreter.yaml
├── knowledge/        # Reusable knowledge bases
│   ├── available_agents.md
│   ├── query_planning_best_practices.md
│   └── athena_best_practices.md
├── templates/        # Reusable prompt templates
└── prompt_manager.py # Prompt management system
```

## How It Works

### 1. Agent Prompts (YAML files)

Each agent has a YAML file defining its prompt:

```yaml
version: latest
metadata:
  description: Agent description
  created_at: 2025-10-05
  author: Your name

knowledge_bases:
  - knowledge_base_name_1
  - knowledge_base_name_2

prompt: |
  Your agent prompt here...
  {{KNOWLEDGE:knowledge_base_name_1}}

  Variables: {variable_name}
```

### 2. Knowledge Bases (Markdown files)

Reusable knowledge that gets injected into prompts:

- `available_agents.md` - List of all agents and their capabilities
- `athena_best_practices.md` - SQL and Athena query best practices
- `query_planning_best_practices.md` - How to plan multi-agent queries

### 3. Using the Prompt Manager

```python
from prompts.prompt_manager import prompt_manager

# Get agent prompt with variables
prompt = prompt_manager.get_agent_prompt(
    "planner",
    variables={
        "query": "Show my top posts",
        "context": "Previous conversation..."
    }
)

# Get specific version
prompt = prompt_manager.get_agent_prompt(
    "planner",
    version="v2",
    variables={...}
)

# Get knowledge base directly
kb = prompt_manager.get_knowledge_base("athena_best_practices")
```

## Updating Prompts

### Option 1: Edit YAML Files Directly

```bash
# Edit the prompt file
vim prompts/agents/planner.yaml

# Clear cache to reload
python -c "from prompts.prompt_manager import prompt_manager; prompt_manager.clear_cache()"
```

### Option 2: Version Your Prompts

```python
from prompts.prompt_manager import prompt_manager

# Save new version
prompt_manager.save_agent_prompt(
    agent_name="planner",
    prompt="Your new improved prompt...",
    version="v2",
    metadata={
        "description": "Improved planning logic",
        "author": "Your name",
        "changes": "Added support for multi-step queries"
    },
    knowledge_bases=["available_agents", "query_planning_best_practices"]
)

# Use specific version
prompt = prompt_manager.get_agent_prompt("planner", version="v2")
```

### Option 3: A/B Testing

```python
# Load different versions for comparison
prompt_v1 = prompt_manager.get_agent_prompt("planner", version="v1")
prompt_v2 = prompt_manager.get_agent_prompt("planner", version="v2")

# Test both and compare results
```

## Adding New Knowledge Bases

1. Create a new `.md` file in `prompts/knowledge/`:

```bash
vim prompts/knowledge/instagram_insights.md
```

2. Add knowledge content:

```markdown
# Instagram Insights Knowledge

## Key Metrics
- Reach: Unique accounts that saw your content
- Impressions: Total times your content was displayed
...
```

3. Reference in agent prompt YAML:

```yaml
knowledge_bases:
  - instagram_insights

prompt: |
  {{KNOWLEDGE:instagram_insights}}

  Now use this knowledge to help users...
```

## Best Practices

### 1. Iterative Improvement
- Start with a basic prompt
- Version it (v1, v2, v3...)
- Track what changes improved performance
- Keep metadata about why changes were made

### 2. Knowledge Base Organization
- Keep knowledge bases focused and modular
- One topic per knowledge base
- Use descriptive names
- Update knowledge bases as you learn

### 3. Version Control
- Commit prompt changes to git
- Use meaningful commit messages
- Tag major prompt versions
- Document what changed and why

### 4. Testing
- Test prompt changes before deploying
- Compare old vs new versions
- Track metrics (response quality, accuracy, etc.)

## Examples

### Add Instagram Analysis Knowledge

```bash
# 1. Create knowledge base
cat > prompts/knowledge/instagram_analysis.md << EOF
# Instagram Performance Analysis

## Engagement Rate Formula
(Likes + Comments + Saves) / Reach × 100

## Benchmarks
- Good: 3-6%
- Excellent: 6%+
EOF

# 2. Update data_analytics.yaml
# Add to knowledge_bases:
#   - instagram_analysis

# 3. Update prompt to use the knowledge
# {{KNOWLEDGE:instagram_analysis}}
```

### Version a Prompt

```python
# Save improved version
from prompts.prompt_manager import prompt_manager

new_prompt = """You are an advanced data analytics agent...
{{KNOWLEDGE:athena_best_practices}}
{{KNOWLEDGE:instagram_analysis}}

Additional context: {context}
User query: {query}
"""

prompt_manager.save_agent_prompt(
    "data_analytics",
    new_prompt,
    version="v2",
    metadata={
        "description": "Added Instagram analysis knowledge",
        "date": "2025-10-05",
        "improvements": "Better engagement rate calculations"
    },
    knowledge_bases=["athena_best_practices", "instagram_analysis"]
)
```

## Integration with LangSmith (Future)

For production, consider integrating with LangSmith Hub:

```python
from langsmith import Client

client = Client()

# Push prompt to LangSmith Hub
client.push_prompt(
    "data-analytics-agent",
    prompt_template,
    description="Data analytics agent prompt"
)

# Pull from Hub
prompt = client.pull_prompt("data-analytics-agent:latest")
```

## Monitoring

Track prompt performance:
- Response quality
- User satisfaction
- Error rates
- Token usage

Use this data to continuously improve prompts.
