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

#### `instagram_media`
- **Timestamp Column**: `timestamp` (when content was posted)
- **Columns**: id, media_type, caption, timestamp, permalink, username
- **Partition**: user_id, year, month, day

#### `instagram_media_insights`
- **Metrics**: reach, impressions, likes, comments, saved, shares
- **No timestamp column** - use JOIN with instagram_media
- **Partition**: user_id, year, month, day

#### Joining Instagram Tables
```sql
SELECT m.timestamp, m.caption, i.reach, i.likes
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id
WHERE m.user_id = '{user_id}'
ORDER BY m.timestamp DESC
```

**ALWAYS join on BOTH `id` AND `user_id`** for:
- Data isolation
- Query performance
- Correct results

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
