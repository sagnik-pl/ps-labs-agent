# Prompt Management System Guide

## Overview

Your codebase now has a **centralized prompt management system** that makes it easy to iteratively improve agent prompts by:

1. **Separating prompts from code** - All prompts in YAML files
2. **Knowledge base injection** - Reusable knowledge that updates all agents
3. **Version control** - Track prompt changes over time
4. **Easy updates** - CLI tools for managing prompts

## Quick Start

### View All Agents and Their Prompts

```bash
python manage_prompts.py list
```

### View a Specific Agent's Prompt

```bash
python manage_prompts.py show planner
python manage_prompts.py show data_analytics
```

### View All Knowledge Bases

```bash
python manage_prompts.py knowledge
```

### Test a Prompt

```bash
python manage_prompts.py test planner
```

## Directory Structure

```
prompts/
├── agents/                 # Agent prompts (YAML)
│   ├── planner.yaml
│   ├── data_analytics.yaml
│   ├── validator.yaml
│   └── interpreter.yaml
├── knowledge/             # Reusable knowledge bases (Markdown)
│   ├── available_agents.md
│   ├── athena_best_practices.md
│   └── query_planning_best_practices.md
├── templates/             # Future: reusable templates
├── prompt_manager.py      # Core prompt management
└── README.md             # Full documentation
```

## How to Improve Prompts

### Method 1: Edit YAML Files Directly

1. **Edit the prompt file:**
   ```bash
   vim prompts/agents/planner.yaml
   ```

2. **Make your changes** to the `prompt:` section

3. **Clear cache** (in production, restart the app):
   ```python
   from prompts.prompt_manager import prompt_manager
   prompt_manager.clear_cache()
   ```

4. **Test your changes:**
   ```bash
   python manage_prompts.py test planner
   python test_langgraph.py
   ```

### Method 2: Version Your Prompts (Recommended)

```python
from prompts.prompt_manager import prompt_manager

# Save a new version
prompt_manager.save_agent_prompt(
    agent_name="planner",
    prompt="""Your improved prompt here...

    {{KNOWLEDGE:available_agents}}

    User Query: {query}
    Context: {context}
    """,
    version="v2",
    metadata={
        "description": "Improved planning with better context handling",
        "author": "Your Name",
        "date": "2025-10-05",
        "changes": "Added support for complex multi-step queries"
    },
    knowledge_bases=["available_agents", "query_planning_best_practices"]
)
```

Then use the new version:
```python
prompt = prompt_manager.get_agent_prompt("planner", version="v2")
```

### Method 3: Update Knowledge Bases

The most powerful way to improve **all agents at once**:

1. **Edit a knowledge base:**
   ```bash
   vim prompts/knowledge/athena_best_practices.md
   ```

2. **Add new best practices:**
   ```markdown
   ## New Best Practice: Engagement Rate

   Calculate engagement rate as:
   (likes + comments + saves) / reach * 100

   Benchmark:
   - Good: 3-6%
   - Excellent: 6%+
   ```

3. **All agents using this knowledge base are automatically updated!**

## Adding Context to Agents

### Example: Add Instagram Insights Knowledge

1. **Create new knowledge base:**
   ```bash
   cat > prompts/knowledge/instagram_metrics.md << 'EOF'
   # Instagram Metrics Guide

   ## Key Metrics

   ### Engagement Rate
   Formula: (Likes + Comments + Saves) / Reach × 100

   Benchmarks:
   - 1-3%: Average
   - 3-6%: Good
   - 6%+: Excellent

   ### Best Posting Times
   - B2C: 12pm-1pm, 5pm-6pm
   - B2B: 7am-8am, 12pm-1pm

   ### Content Types Performance
   - Reels: Highest reach
   - Carousel: Best engagement
   - Single Image: Consistent performance
   EOF
   ```

2. **Reference in agent prompt:**
   ```yaml
   # In prompts/agents/data_analytics.yaml
   knowledge_bases:
     - athena_best_practices
     - instagram_metrics    # <-- Add this

   prompt: |
     You are a Data Analytics Agent...

     {{KNOWLEDGE:athena_best_practices}}
     {{KNOWLEDGE:instagram_metrics}}

     Use the above metrics knowledge to provide context in your analysis.
   ```

3. **Clear cache and test:**
   ```python
   from prompts.prompt_manager import prompt_manager
   prompt_manager.clear_cache()
   ```

## Best Practices for Prompt Engineering

### 1. Iterative Improvement Workflow

```bash
# 1. Test current version
python test_langgraph.py

# 2. Edit prompt
vim prompts/agents/planner.yaml

# 3. Test changes
python manage_prompts.py test planner

# 4. Full integration test
python test_langgraph.py

# 5. Commit changes
git add prompts/
git commit -m "Improve planner: Added better context handling"
```

### 2. Knowledge Base Strategy

**Do:**
- ✅ Keep knowledge bases focused (one topic per file)
- ✅ Use descriptive names (`instagram_metrics.md` not `kb1.md`)
- ✅ Update knowledge bases as you learn
- ✅ Share knowledge across agents

**Don't:**
- ❌ Put agent-specific logic in knowledge bases
- ❌ Duplicate knowledge across multiple files
- ❌ Mix unrelated topics in one knowledge base

### 3. Versioning Strategy

**When to version:**
- Major prompt changes
- Breaking changes to prompt structure
- A/B testing different approaches

**Version naming:**
- `latest` - Current production version
- `v1`, `v2`, `v3` - Numbered versions
- `experiment-feature-name` - Experimental versions

### 4. Testing Prompts

Always test prompt changes:

```python
# Test individual prompt
python manage_prompts.py test planner

# Test full workflow
python test_langgraph.py

# Test with real data
python main.py
# Enter test query: "Show my top Instagram posts"
```

## Creating New Agents

### Step 1: Create Agent Prompt

```bash
python manage_prompts.py create competitor_intelligence
```

This creates `prompts/agents/competitor_intelligence.yaml`

### Step 2: Edit the Prompt

```yaml
version: latest
metadata:
  description: Competitor intelligence agent
  created_at: 2025-10-05

knowledge_bases:
  - available_agents
  - competitor_research_methods

prompt: |
  You are a Competitor Intelligence Agent.

  Your role is to:
  1. Research competitor performance
  2. Analyze competitor strategies
  3. Provide competitive insights

  {{KNOWLEDGE:available_agents}}
  {{KNOWLEDGE:competitor_research_methods}}

  Competitor: {competitor_name}
  Analysis Type: {analysis_type}

  Provide detailed competitive analysis.
```

### Step 3: Create Node Function

Add to `workflow/nodes.py`:

```python
def competitor_intelligence_node(self, state: AgentState) -> Dict[str, Any]:
    """Competitor intelligence agent node."""

    # Load prompt
    prompt = self.prompt_manager.get_agent_prompt(
        "competitor_intelligence",
        variables={
            "competitor_name": state.get("competitor_name", ""),
            "analysis_type": state.get("analysis_type", "general")
        }
    )

    # Execute agent logic...
    # Return results
```

### Step 4: Add to Workflow Graph

In `workflow/graph.py`:

```python
workflow.add_node("competitor_intelligence", nodes.competitor_intelligence_node)
```

## Advanced: A/B Testing Prompts

```python
from prompts.prompt_manager import prompt_manager
import random

# Create two versions
prompt_manager.save_agent_prompt("planner", prompt_v1, version="v1")
prompt_manager.save_agent_prompt("planner", prompt_v2, version="v2")

# Randomly select version for testing
version = random.choice(["v1", "v2"])
prompt = prompt_manager.get_agent_prompt("planner", version=version)

# Track which version performed better
# (implement your own metrics tracking)
```

## Integration with LangSmith (Future)

For production monitoring and prompt management:

```python
from langsmith import Client

client = Client()

# Push to LangSmith Hub
client.push_prompt(
    "planner-agent",
    prompt,
    description="Query planner for e-commerce analytics"
)

# Pull from Hub
prompt = client.pull_prompt("planner-agent:production")
```

## Monitoring Prompt Performance

Track these metrics to know when to improve prompts:

- **Response Quality**: User feedback, ratings
- **Accuracy**: Did it answer correctly?
- **Completeness**: Full answer vs partial?
- **Token Usage**: Efficiency
- **Error Rate**: How often does it fail?

## Example: Full Improvement Cycle

Let's improve the Data Analytics agent:

### 1. Current State
```bash
python manage_prompts.py show data_analytics
```

### 2. Add New Knowledge
```bash
cat > prompts/knowledge/sql_optimization.md << 'EOF'
# SQL Query Optimization

## Partition Pruning
Always filter on partition columns first:
- user_id
- year, month, day

## Performance Tips
1. Use LIMIT for large result sets
2. Avoid SELECT * in production
3. Use WHERE before JOIN when possible
EOF
```

### 3. Update Agent Prompt
```yaml
# prompts/agents/data_analytics.yaml
knowledge_bases:
  - athena_best_practices
  - sql_optimization  # New!

prompt: |
  ...existing prompt...

  {{KNOWLEDGE:sql_optimization}}

  Optimize all queries for performance.
```

### 4. Test
```bash
python manage_prompts.py test data_analytics
python test_langgraph.py
```

### 5. Deploy & Monitor
```bash
git add prompts/
git commit -m "Add SQL optimization knowledge to data analytics agent"
git push
```

Monitor performance and iterate!

## Summary

✅ **Prompts are separate from code** - Easy to update without touching Python
✅ **Knowledge bases** - Share context across all agents
✅ **Version control** - Track changes over time
✅ **CLI tools** - Easy management with `manage_prompts.py`
✅ **Modular** - Each agent has its own prompt file
✅ **Testable** - Test prompts before deploying

**To improve any agent, just edit its YAML file or update knowledge bases!**
