# SQL Query Validation Principles

## Validation Framework

### What Makes a Good SQL Query

A high-quality SQL query for analytics should be:
1. **Correct**: Valid syntax, correct table/column names
2. **Secure**: Properly filters by user_id (data isolation)
3. **Efficient**: Uses partitions, appropriate indexes
4. **Complete**: Answers the user's question fully
5. **Safe**: No destructive operations, reasonable limits

## Critical Validation Checks

### 1. User Isolation (CRITICAL ⚠️)

**MUST HAVE**: Every query MUST filter by user_id

✅ **Correct**:
```sql
SELECT * FROM instagram_media
WHERE user_id = '45up1lHMF2N4SwAJc6iMEOdLg9y1'
```

❌ **WRONG** (Missing user_id filter):
```sql
SELECT * FROM instagram_media
```

**For JOINs**: Both tables must filter on user_id

✅ **Correct**:
```sql
SELECT m.*, i.*
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = 'user123'
```

❌ **WRONG** (JOIN without user_id):
```sql
SELECT m.*, i.*
FROM instagram_media m
JOIN instagram_media_insights i ON m.id = i.id
WHERE m.user_id = 'user123'
```

### 2. Table and Column Existence

**Check**: All table names and column names exist

Common Tables:
- `instagram_media`
- `instagram_media_insights`
- `facebook_ads_insights_demographics_dma_region`
- `google_analytics_ecommerce_purchases_item_name_report`

**Validation**:
- Has schema been checked?
- Are column names spelled correctly?
- Case sensitivity matters in some databases

### 3. SQL Syntax Correctness

Common syntax errors to check:

❌ **Missing quotes**:
```sql
WHERE user_id = user123  -- Wrong
WHERE user_id = 'user123'  -- Correct
```

❌ **Wrong date format**:
```sql
WHERE timestamp = 2025-01-01  -- Wrong
WHERE timestamp = DATE '2025-01-01'  -- Correct
```

❌ **Incorrect aggregation**:
```sql
SELECT caption, COUNT(*) FROM posts  -- Missing GROUP BY
SELECT caption, COUNT(*) FROM posts GROUP BY caption  -- Correct
```

❌ **Invalid operators**:
```sql
WHERE likes == 100  -- Wrong (== is not SQL)
WHERE likes = 100  -- Correct
```

### 4. Join Logic

**Instagram Specific**: When joining instagram_media and instagram_media_insights

✅ **Correct**:
```sql
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = 'user123'
```

**Why**:
- Join on both id AND user_id for data isolation
- Filter WHERE clause for partition pruning

### 5. Athena-Specific Syntax

**Partition Columns**:
- user_id
- year
- month
- day

✅ **Good** (uses partitions):
```sql
WHERE user_id = 'user123'
  AND year = 2025
  AND month = 10
```

**String Functions**:
- Use `LOWER()`, not `LCASE()`
- Use `SUBSTR()`, not `SUBSTRING()` (both work but SUBSTR is preferred)

**Date Functions**:
- Use `DATE_TRUNC()` for date grouping
- Use `DATE_ADD()` for date arithmetic
- Use `CAST(timestamp AS DATE)` for date conversion

**Type Casting**:
```sql
CAST(column_name AS BIGINT)
CAST(column_name AS DOUBLE)
CAST(column_name AS VARCHAR)
```

### 6. Performance Considerations

✅ **Efficient**:
```sql
SELECT id, caption, timestamp
FROM instagram_media
WHERE user_id = 'user123'
  AND year = 2025
  AND month = 10
LIMIT 100
```

⚠️ **Inefficient** (but might be necessary):
```sql
SELECT *
FROM instagram_media
WHERE user_id = 'user123'
```

**Best Practices**:
- Specify columns instead of `SELECT *`
- Use `LIMIT` for large result sets
- Filter on partition columns (user_id, year, month, day)
- Avoid unnecessary JOINs

### 7. Query Completeness

Does the query answer the user's question?

**User Query**: "Show my top 5 posts by engagement"

❌ **Incomplete**:
```sql
SELECT id, caption FROM instagram_media LIMIT 5
```

✅ **Complete**:
```sql
SELECT
  m.id,
  m.caption,
  m.timestamp,
  (i.likes + i.comments + i.saved + i.shares) as total_engagement
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = 'user123'
ORDER BY total_engagement DESC
LIMIT 5
```

## Common Errors and Fixes

### Error 1: Column Not Found

❌ **Error**:
```sql
SELECT media_url FROM instagram_media
-- Error: Column 'media_url' does not exist
```

✅ **Fix**:
```sql
-- Check schema first, then use correct column name
SELECT permalink FROM instagram_media
```

### Error 2: Ambiguous Column

❌ **Error**:
```sql
SELECT id FROM instagram_media m
JOIN instagram_media_insights i ON m.id = i.id
-- Error: Column 'id' is ambiguous
```

✅ **Fix**:
```sql
SELECT m.id FROM instagram_media m
JOIN instagram_media_insights i ON m.id = i.id
```

### Error 3: Type Mismatch

❌ **Error**:
```sql
WHERE timestamp = '2025-10-01'
-- Error: Cannot compare timestamp to string
```

✅ **Fix**:
```sql
WHERE CAST(timestamp AS DATE) = DATE '2025-10-01'
-- OR
WHERE timestamp >= TIMESTAMP '2025-10-01 00:00:00'
  AND timestamp < TIMESTAMP '2025-10-02 00:00:00'
```

### Error 4: Division by Zero

❌ **Risky**:
```sql
SELECT likes / reach as engagement_rate
-- Error if reach = 0
```

✅ **Safe**:
```sql
SELECT
  CASE
    WHEN reach > 0 THEN CAST(likes AS DOUBLE) / reach * 100
    ELSE 0
  END as engagement_rate
-- OR
SELECT CAST(likes AS DOUBLE) / NULLIF(reach, 0) * 100 as engagement_rate
```

### Error 5: Missing user_id Filter

❌ **CRITICAL ERROR**:
```sql
SELECT * FROM instagram_media
LIMIT 10
```

✅ **Fix**:
```sql
SELECT * FROM instagram_media
WHERE user_id = 'user123'
LIMIT 10
```

## Validation Checklist

When validating a SQL query, check:

- [ ] **User Isolation**: Filters by user_id in WHERE clause?
- [ ] **Table Names**: All tables exist and spelled correctly?
- [ ] **Column Names**: All columns exist in their tables?
- [ ] **JOIN Logic**: Joins use both id AND user_id (for Instagram)?
- [ ] **SQL Syntax**: Valid SQL syntax (quotes, operators, keywords)?
- [ ] **Data Types**: Correct type casting and comparisons?
- [ ] **Aggregations**: Proper GROUP BY for aggregated queries?
- [ ] **Performance**: Uses partitions, has LIMIT where appropriate?
- [ ] **Completeness**: Fully answers the user's question?
- [ ] **Safety**: No DELETE, DROP, UPDATE, or other destructive ops?

## Red Flags

Immediately reject if:

🚩 **No user_id filter** - Critical security/isolation issue
🚩 **Destructive operations** - DELETE, DROP, UPDATE, TRUNCATE
🚩 **Invalid table/column names** - Will fail on execution
🚩 **Syntax errors** - Won't execute
🚩 **Missing required JOINs** - Won't answer the question

## Confidence Levels

### High Confidence (Valid)
- All checklist items passed
- Uses correct schema
- Efficient and safe
- Fully answers query

### Medium Confidence (Needs Improvement)
- Minor inefficiencies
- Could be more specific
- Missing optional optimizations
- Still functionally correct

### Low Confidence (Invalid)
- Missing user_id filter
- Syntax errors
- Wrong table/column names
- Won't answer the question
- Security issues

## Example Validations

### Example 1: Valid Query

**User Query**: "Show my recent Instagram posts"

**Generated SQL**:
```sql
SELECT id, caption, timestamp, media_type
FROM instagram_media
WHERE user_id = 'user123'
ORDER BY timestamp DESC
LIMIT 10
```

**Validation**:
- ✅ Has user_id filter
- ✅ Correct table and columns
- ✅ Valid syntax
- ✅ Answers the question
- ✅ Efficient (has LIMIT)

**Result**: VALID ✓

### Example 2: Missing user_id

**User Query**: "Show my top posts"

**Generated SQL**:
```sql
SELECT id, caption FROM instagram_media LIMIT 10
```

**Validation**:
- ❌ **MISSING user_id filter** - CRITICAL
- ✅ Correct table and columns
- ✅ Valid syntax
- ⚠️ Missing engagement metrics

**Result**: INVALID ✗

**Feedback**: "Critical: Query must filter by user_id for data isolation. Also missing engagement metrics to determine 'top' posts. Need to JOIN with instagram_media_insights."

### Example 3: Wrong Column Name

**User Query**: "Show posts with captions"

**Generated SQL**:
```sql
SELECT id, text FROM instagram_media
WHERE user_id = 'user123'
```

**Validation**:
- ✅ Has user_id filter
- ✅ Correct table
- ❌ Wrong column name ('text' should be 'caption')
- ✅ Valid syntax otherwise

**Result**: INVALID ✗

**Feedback**: "Column 'text' does not exist in instagram_media table. Use 'caption' instead."

### Example 4: Incomplete JOIN

**User Query**: "Show my top posts by likes"

**Generated SQL**:
```sql
SELECT m.id, m.caption, i.likes
FROM instagram_media m
JOIN instagram_media_insights i ON m.id = i.id
WHERE m.user_id = 'user123'
ORDER BY i.likes DESC
LIMIT 5
```

**Validation**:
- ✅ Has user_id filter
- ✅ Correct tables and columns
- ❌ **JOIN missing user_id** - Should join on both id AND user_id
- ✅ Valid syntax
- ✅ Answers the question

**Result**: INVALID ✗

**Feedback**: "JOIN should include user_id for data isolation and performance. Change to: JOIN instagram_media_insights i ON m.id = i.id AND m.user_id = i.user_id"

## Special Cases

### Engagement Rate Calculation

✅ **Correct**:
```sql
SELECT
  (CAST(likes AS DOUBLE) + comments + saved) / NULLIF(reach, 0) * 100 as engagement_rate
FROM instagram_media_insights
WHERE user_id = 'user123'
```

### Time-based Aggregation

✅ **Correct**:
```sql
SELECT
  DATE_TRUNC('day', timestamp) as date,
  COUNT(*) as posts_per_day
FROM instagram_media
WHERE user_id = 'user123'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY date DESC
```

### Text Search

✅ **Correct**:
```sql
SELECT id, caption
FROM instagram_media
WHERE user_id = 'user123'
  AND LOWER(caption) LIKE '%product%'
```
