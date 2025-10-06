# Query Planning Best Practices

## Planning Principles

1. **Start Simple**: Default to single-agent execution unless query clearly requires multiple steps
2. **Data First**: If query needs user data, always route to `data_analytics` agent first
3. **Sequential Dependencies**: Plan steps that depend on previous outputs sequentially
4. **Parallel Opportunities**: Identify independent steps that can run in parallel

## Common Query Patterns

### Pattern 1: Simple Data Query
**Example**: "How many Instagram posts did I make last month?"
**Plan**: Single step → `data_analytics` agent

### Pattern 2: Data + Interpretation
**Example**: "Analyze my Instagram performance and suggest improvements"
**Plan**:
1. `data_analytics` → Get performance metrics
2. Use results to provide insights (handled by interpreter node)

### Pattern 3: Multi-Agent (Future)
**Example**: "Compare my Instagram performance with competitors"
**Plan**:
1. `data_analytics` → Get user's Instagram metrics
2. `competitor_intelligence` → Get competitor data
3. Synthesize comparison (handled by interpreter)

### Pattern 4: Creative + Data (Future)
**Example**: "Create 5 ad creatives based on my best performing posts"
**Plan**:
1. `data_analytics` → Find best performing posts
2. `creative` → Generate ad creatives based on insights

## Complexity Assessment

- **Low**: Single agent, straightforward query
- **Medium**: Single agent with complex data requirements OR simple multi-step
- **High**: Multiple agents, complex dependencies, or creative/analytical tasks
