# AWS Athena Query Best Practices

## Data Isolation & Security

### User ID Filtering (CRITICAL)
```sql
-- ALWAYS filter by user_id - it's a partition column
WHERE user_id = '{user_id}'
```

**Why**:
- Ensures data isolation between users
- Improves query performance (partition pruning)
- Required for security and compliance

## Table Schemas

### Instagram Tables

#### CRITICAL: Instagram Table Refresh Types

**`instagram_media` is a FULL REFRESH snapshot table:**
- Contains ALL media posts from the beginning of time (not just recent posts)
- The `timestamp` column represents when each post was originally published on Instagram
- To get posts from last 30 days: `WHERE m.timestamp >= date_add('day', -30, current_date)`
- DO NOT assume this table only contains recent data

**`instagram_media_insights` has NO timestamp column:**
- Contains engagement metrics (reach, likes, comments, saved, shares)
- To filter by post publication date, you MUST join with instagram_media
- NEVER query this table alone for time-based queries

**Partition columns (year, month, day):**
- Represent when the ETL job processed the data (glue_processed_at date)
- NOT when the post was published on Instagram
- Use for performance optimization, but NOT for user-facing time filters

#### `instagram_media`
- **Timestamp Column**: `timestamp` (when content was posted)
- **Columns**: id, media_type, caption, timestamp, permalink, username
- **Partition**: user_id, year, month, day
- **Refresh Type**: FULL REFRESH (contains all posts ever)

#### `instagram_media_insights`
- **Metrics**: reach, impressions, likes, comments, saved, shares
- **No timestamp column** - use JOIN with instagram_media
- **Partition**: user_id, year, month, day

#### Joining Instagram Tables (REQUIRED for Performance Queries)

For ANY query asking about Instagram performance, engagement, reach, or metrics:
1. You MUST join both tables
2. Filter by post publication time using m.timestamp
3. Get metrics from instagram_media_insights

```sql
-- CORRECT: Join both tables, filter by timestamp
SELECT
  m.timestamp,
  m.caption,
  m.media_type,
  mi.reach,
  mi.likes,
  mi.comments,
  mi.saved,
  mi.shares
FROM instagram_media m
LEFT JOIN instagram_media_insights mi
  ON m.id = mi.id AND m.user_id = mi.user_id
WHERE m.user_id = '{user_id}'
  AND m.timestamp >= date_add('day', -30, current_date)
ORDER BY mi.reach DESC
LIMIT 10
```

**ALWAYS join on BOTH `id` AND `user_id`** for:
- Data isolation
- Query performance
- Correct results

**Common Mistakes to Avoid:**
```sql
-- ❌ WRONG: Query instagram_media without time filter
SELECT COUNT(*) FROM instagram_media WHERE user_id = '{user_id}'
-- Returns ALL posts ever (not last 30 days)

-- ❌ WRONG: Try to filter instagram_media_insights by timestamp
SELECT * FROM instagram_media_insights
WHERE user_id = '{user_id}' AND timestamp >= date_add('day', -30, current_date)
-- ERROR: instagram_media_insights has NO timestamp column

-- ❌ WRONG: Use partition columns for time filtering
SELECT * FROM instagram_media_insights
WHERE user_id = '{user_id}' AND year = '2025' AND month = '01'
-- Returns insights processed in Jan 2025, NOT posts published in last 30 days
```

## Query Optimization

1. **Use partition columns**: user_id, year, month, day
2. **Limit results**: Add LIMIT clause for large datasets
3. **Select specific columns**: Avoid SELECT *
4. **Use appropriate date filters**: Filter by year/month/day partitions

## Common Query Patterns

### Recent Posts Performance
```sql
SELECT
  m.timestamp,
  m.caption,
  m.media_type,
  i.reach,
  i.likes,
  i.comments
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = '{user_id}'
  AND m.year = 2025
  AND m.month = 10
ORDER BY m.timestamp DESC
LIMIT 10
```

### Top Performing Content
```sql
SELECT
  m.caption,
  i.reach,
  i.likes,
  (CAST(i.likes AS DOUBLE) / NULLIF(i.reach, 0)) * 100 as engagement_rate
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = '{user_id}'
ORDER BY engagement_rate DESC
LIMIT 10
```

### Time Series Analysis
```sql
SELECT
  DATE_TRUNC('day', m.timestamp) as date,
  COUNT(*) as posts,
  AVG(i.reach) as avg_reach,
  AVG(i.likes) as avg_likes
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = '{user_id}'
GROUP BY DATE_TRUNC('day', m.timestamp)
ORDER BY date DESC
```
