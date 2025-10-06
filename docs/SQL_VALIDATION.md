# SQL Query Validation System

## Overview

The system now has a **SQL validation layer** that ensures all SQL queries are correct, secure, and efficient before execution.

## Architecture

### New Workflow

```
Query → SQL Generator → SQL Validator → (valid?) → SQL Executor → Results
             ↑              ↓
             └─ retry ──────┘
            (if invalid, up to 3 times)
```

### Key Components

#### 1. **SQL Generator Node**
- **Purpose**: Generate SQL queries from natural language
- **Input**: User query, table schemas, user_id
- **Output**: SQL query
- **Prompt**: `prompts/agents/sql_generator.yaml`

#### 2. **SQL Validator Node**
- **Purpose**: Validate SQL queries before execution
- **Checks**: Security, correctness, efficiency, completeness
- **Output**: Valid/Invalid + detailed feedback
- **Prompt**: `prompts/agents/sql_validator.yaml`

#### 3. **SQL Executor Node**
- **Purpose**: Execute validated SQL queries
- **Safety**: Only runs queries that passed validation
- **Output**: Query results or error messages

## Validation Criteria

### Critical Checks (Must Pass) ⚠️

1. **User Isolation** - CRITICAL for security
   - Must filter by `user_id = 'user123'`
   - JOINs must include user_id

2. **Table/Column Existence**
   - All tables must exist
   - All columns must exist in schemas

3. **SQL Syntax**
   - Valid SQL syntax
   - Correct operators, quotes, keywords
   - Proper GROUP BY for aggregations

4. **Query Completeness**
   - Fully answers user's question
   - Has all necessary columns
   - Includes required JOINs

### Important Checks

5. **JOIN Logic**
   - Instagram tables: JOIN on both `id` AND `user_id`

6. **Performance**
   - Uses partition columns (user_id, year, month, day)
   - Has LIMIT for large results
   - Selects specific columns

7. **Safety**
   - No destructive operations (DELETE, DROP, UPDATE)
   - Safe division (no division by zero)
   - Proper type casting

## Validation Loop

### How It Works

1. **Generate SQL**
   - LLM creates SQL query from natural language
   - Uses table schemas and athena best practices

2. **Validate SQL**
   - Checks all criteria
   - Returns True/False + feedback

3. **If Invalid (False)**
   - Sends feedback to SQL generator
   - Regenerates SQL with corrections
   - Validates again
   - Max 3 retries

4. **If Valid (True)**
   - Proceeds to execution
   - Runs query against Athena

### Example Validation Flow

**Attempt 1**:
```sql
-- Missing user_id filter ❌
SELECT * FROM instagram_media LIMIT 10
```
**Validation**: INVALID
**Feedback**: "Critical: Query must filter by user_id for data isolation"

**Attempt 2**:
```sql
-- Has user_id but wrong column ❌
SELECT id, text FROM instagram_media
WHERE user_id = 'user123' LIMIT 10
```
**Validation**: INVALID
**Feedback**: "Column 'text' does not exist. Use 'caption' instead."

**Attempt 3**:
```sql
-- Correct! ✅
SELECT id, caption FROM instagram_media
WHERE user_id = 'user123' LIMIT 10
```
**Validation**: VALID
**Proceeds to execution**

## Knowledge Bases

### `sql_query_validation.md`

Comprehensive validation knowledge including:
- User isolation requirements
- Table/column existence checks
- SQL syntax rules
- Athena-specific syntax
- Common errors and fixes
- Validation checklist

### `athena_best_practices.md`

Best practices for Athena queries:
- Partition pruning
- Join optimization
- Engagement calculations
- Performance tips

## Validation Response Format

```json
{
  "is_valid": true/false,
  "confidence": "high|medium|low",
  "validation_score": 85,
  "passed_checks": [
    "user_isolation",
    "table_existence",
    "column_existence",
    "sql_syntax",
    "completeness",
    "join_logic",
    "performance",
    "safety"
  ],
  "failed_checks": [],
  "critical_issues": [],
  "warnings": [
    "Could use LIMIT clause for better performance"
  ],
  "feedback": "Query is valid but could be optimized...",
  "corrected_query": "Optional corrected version",
  "reasoning": "Validation passed all critical checks"
}
```

## Example Validations

### Example 1: Valid Query ✅

**User Query**: "Show my top posts by engagement"

**Generated SQL**:
```sql
SELECT
  m.caption,
  (i.likes + i.comments + i.saved + i.shares) AS total_engagement
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = '45up1lHMF2N4SwAJc6iMEOdLg9y1'
ORDER BY total_engagement DESC
LIMIT 10
```

**Validation Result**:
- ✅ Has user_id filter
- ✅ Correct JOIN logic (both id and user_id)
- ✅ Valid syntax
- ✅ Answers the question
- ✅ Has LIMIT clause
- ✅ VALID - Score: 95/100

### Example 2: Missing user_id ❌

**Generated SQL**:
```sql
SELECT caption FROM instagram_media LIMIT 10
```

**Validation Result**:
- ❌ Missing user_id filter (CRITICAL)
- ✅ Valid syntax
- ✅ Has LIMIT
- ❌ INVALID - Score: 30/100

**Feedback**: "Critical: Query must filter by user_id = 'user_id_value' for data isolation and security."

### Example 3: Wrong Column Name ❌

**Generated SQL**:
```sql
SELECT id, media_url FROM instagram_media
WHERE user_id = 'user123'
```

**Validation Result**:
- ✅ Has user_id filter
- ❌ Column 'media_url' doesn't exist
- ✅ Valid syntax otherwise
- ❌ INVALID - Score: 65/100

**Feedback**: "Column 'media_url' does not exist in instagram_media. Available columns: id, media_type, thumbnail_url, caption, timestamp, permalink, username. Did you mean 'permalink'?"

### Example 4: Missing JOIN ❌

**Generated SQL**:
```sql
SELECT id, caption, likes FROM instagram_media
WHERE user_id = 'user123'
LIMIT 5
```

**Validation Result**:
- ✅ Has user_id filter
- ❌ Column 'likes' doesn't exist in instagram_media
- ✅ Valid syntax
- ❌ Incomplete (likes requires JOIN with instagram_media_insights)
- ❌ INVALID - Score: 60/100

**Feedback**: "Column 'likes' does not exist in instagram_media. To get engagement metrics (likes, comments, etc.), you must JOIN with instagram_media_insights table."

## Improving SQL Generation

### Option 1: Update SQL Generator Prompt

```bash
vim prompts/agents/sql_generator.yaml

# Add more examples, guidelines, or context
```

### Option 2: Add SQL Knowledge

```bash
# Add SQL patterns knowledge
cat > prompts/knowledge/sql_patterns.md << 'EOF'
# Common SQL Patterns

## Top N by Metric
SELECT column, metric
FROM table
WHERE user_id = 'user123'
ORDER BY metric DESC
LIMIT N

## Engagement Rate
SELECT
  (CAST(likes AS DOUBLE) / NULLIF(reach, 0)) * 100 as engagement_rate
FROM instagram_media_insights
EOF

# Reference in sql_generator.yaml
# knowledge_bases:
#   - athena_best_practices
#   - sql_patterns
```

### Option 3: Version the Generator

```python
from prompts.prompt_manager import prompt_manager

prompt_manager.save_agent_prompt(
    "sql_generator",
    improved_prompt,
    version="v2",
    metadata={
        "changes": "Better JOIN handling, improved engagement formulas"
    }
)
```

## Testing

### Test SQL Validation

```bash
python test_sql_validation.py
```

### What's Tested

- SQL generation from natural language
- Validation checks (user_id, syntax, completeness)
- Retry loop (up to 3 attempts)
- Query execution
- End-to-end workflow

### Example Test Output

```
✅ SQL Validation:
   Valid: True
   Validation Score: 95/100

✓ Passed Checks: user_isolation, table_existence, column_existence,
                  sql_syntax, completeness, join_logic, performance, safety

🔄 SQL Generation Retries: 0

✓ SQL includes user_id filter: True
✓ SQL has WHERE clause: True
✓ SQL has LIMIT clause: True
✓ SQL passed validation: True
```

## Configuration

### Max Retries

Default: 3 retries for SQL generation

Change in `workflow/nodes.py`:
```python
max_retries = 3  # Increase to 5 for more attempts
```

### Validation Threshold

Default: Must pass all critical checks

Modify in `prompts/agents/sql_validator.yaml`:
```yaml
# Current: is_valid = true if all critical checks pass
# Can adjust to allow some non-critical failures
```

## Common Issues & Solutions

### Issue 1: Too Many Retries

**Symptom**: Query keeps retrying, never validates

**Cause**: SQL generator not incorporating feedback

**Solution**:
- Check sql_generator.yaml prompt includes feedback handling
- Review validation feedback clarity
- Add more examples to generator

### Issue 2: False Positives

**Symptom**: Invalid queries passing validation

**Cause**: Validation too lenient

**Solution**:
- Update sql_validator.yaml to be stricter
- Add more validation checks
- Lower validation score threshold

### Issue 3: False Negatives

**Symptom**: Valid queries failing validation

**Cause**: Validation too strict

**Solution**:
- Review failed_checks in validation output
- Adjust validation criteria
- Update table schemas if outdated

## Monitoring

### Track These Metrics

- **SQL Retry Rate**: How often queries need retries
- **Validation Pass Rate**: % of queries that validate on first try
- **Common Failed Checks**: Which validation criteria fail most
- **Execution Error Rate**: Queries that pass validation but fail execution

### Example Monitoring

```python
# In production, log these:
sql_validation = result.get("sql_validation", {})

metrics = {
    "is_valid": sql_validation.get("is_valid"),
    "retry_count": result.get("sql_retry_count"),
    "validation_score": sql_validation.get("validation_score"),
    "failed_checks": sql_validation.get("failed_checks"),
}

# Log to monitoring system
log_sql_validation_metrics(metrics)
```

## Integration with Full Workflow

### Complete Flow

```
User Query
    ↓
Planner → Router → SQL Generator → SQL Validator
                        ↑              ↓
                        └─ retry ──────┘
                                       ↓
                               SQL Executor
                                       ↓
                              Data Interpreter (E-commerce brain)
                                       ↓
                         Interpretation Validator
                              ↑          ↓
                    retry ────┘    valid → Final Response
```

### All Validation Layers

1. **SQL Validation** (New!)
   - Ensures queries are correct and safe
   - Retries with feedback

2. **Data Interpretation Validation**
   - Ensures insights are high-quality
   - Checks for e-commerce context

Both layers work together to provide:
- Correct SQL queries
- Accurate data results
- Rich, actionable insights

## Summary

✅ **SQL queries are now validated before execution**
✅ **Automatic retry loop** with specific feedback (up to 3 times)
✅ **Critical security checks** (user_id filtering)
✅ **Syntax and schema validation**
✅ **Performance and efficiency checks**
✅ **Comprehensive validation knowledge base**

**The system prevents:**
- ❌ SQL injection risks
- ❌ Data leakage between users
- ❌ Syntax errors
- ❌ Non-existent table/column references
- ❌ Incomplete or incorrect queries

**Result: Safe, correct, efficient SQL queries every time!**
