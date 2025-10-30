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

**Instagram Tables (5):**
- `instagram_media`
- `instagram_media_insights`
- `instagram_user_insights`
- `instagram_user_lifetime_insights`
- `instagram_users`

**Facebook Ads Tables (12):**
- `facebook_campaigns`
- `facebook_ad_sets`
- `facebook_ads`
- `facebook_ad_creatives`
- `facebook_ads_insights`
- `facebook_ads_insights_age_and_gender`
- `facebook_ads_insights_delivery_platform_and_device_platform`
- `facebook_ads_insights_action_type`
- `facebook_ads_insights_action_reaction`
- `facebook_ads_insights_action_product_id`
- `facebook_ads_insights_action_conversion_device`
- `facebook_dma_insights`

**Google Analytics Tables (8):**
- `ga_website_overview`
- `ga_daily_active_users`
- `ga_pages`
- `ga_pages_path_report`
- `ga_traffic_sources`
- `ga_traffic_acquisition_session_medium`
- `ga_traffic_acquisition_session_source`
- `ga_item_report`

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

### Error 6: Wrong Date Column for Facebook Ads

❌ **WRONG**:
```sql
SELECT * FROM facebook_ads_insights
WHERE timestamp >= '2024-01-01'
-- ERROR: facebook_ads_insights uses 'date_start', not 'timestamp'
```

✅ **Fix**:
```sql
SELECT * FROM facebook_ads_insights
WHERE user_id = 'user123'
  AND date_start >= '2024-01-01'
```

### Error 7: Wrong Date Format for Google Analytics

❌ **WRONG**:
```sql
SELECT * FROM ga_website_overview
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
-- ERROR: GA 'date' is STRING (yyyyMMdd), not DATE type
```

✅ **Fix**:
```sql
-- Option 1: Parse date string to date type
SELECT * FROM ga_website_overview
WHERE user_id = 'user123'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY

-- Option 2: String comparison
SELECT * FROM ga_website_overview
WHERE user_id = 'user123'
  AND date >= '20240101'
```

### Error 8: Missing Hierarchical Join for Facebook Ads

❌ **INCOMPLETE**:
```sql
-- Want campaign performance but querying ad-level data without aggregation
SELECT campaign_name, spend
FROM facebook_ads_insights
WHERE user_id = 'user123'
-- ERROR: facebook_ads_insights doesn't have campaign_name
```

✅ **Fix**:
```sql
-- Properly join through hierarchy: insights -> ads -> ad_sets -> campaigns
SELECT
  c.campaign_name,
  SUM(i.spend) as total_spend
FROM facebook_ads_insights i
LEFT JOIN facebook_ads a ON i.ad_id = a.id AND i.user_id = a.user_id
LEFT JOIN facebook_ad_sets ads ON a.adset_id = ads.id AND a.user_id = ads.user_id
LEFT JOIN facebook_campaigns c ON ads.campaign_id = c.id AND ads.user_id = c.user_id
WHERE i.user_id = 'user123'
  AND i.date_start >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY c.campaign_name
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

## Platform-Specific Validation Examples

### Facebook Ads Query Validation

**User Query**: "Show me my Facebook ad campaign performance"

**Generated SQL**:
```sql
SELECT
  c.campaign_name,
  c.status,
  SUM(i.spend) as total_spend,
  SUM(i.impressions) as impressions,
  SUM(i.clicks) as clicks
FROM facebook_ads_insights i
LEFT JOIN facebook_ads a ON i.ad_id = a.id AND i.user_id = a.user_id
LEFT JOIN facebook_ad_sets ads ON a.adset_id = ads.id AND a.user_id = ads.user_id
LEFT JOIN facebook_campaigns c ON ads.campaign_id = c.id AND ads.user_id = c.user_id
WHERE i.user_id = 'user123'
  AND i.date_start >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY c.campaign_name, c.status
ORDER BY total_spend DESC
```

**Validation**:
- ✅ Has user_id filter
- ✅ Correct date column (date_start)
- ✅ Proper hierarchical joins (insights → ads → ad_sets → campaigns)
- ✅ Joins on both id AND user_id
- ✅ Proper aggregation (SUM with GROUP BY)
- ✅ Valid syntax

**Result**: VALID ✓

---

### Google Analytics Query Validation

**User Query**: "What were my top products by revenue last month?"

**Generated SQL**:
```sql
SELECT
  itemName,
  SUM(itemRevenue) as total_revenue,
  SUM(itemsPurchased) as units_sold
FROM ga_item_report
WHERE user_id = 'user123'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY itemName
ORDER BY total_revenue DESC
LIMIT 20
```

**Validation**:
- ✅ Has user_id filter
- ✅ Correct date parsing (date_parse for yyyyMMdd format)
- ✅ Proper aggregation with GROUP BY
- ✅ Correct table (ga_item_report for ecommerce)
- ✅ Has LIMIT for performance

**Result**: VALID ✓

---

### Multi-Platform Query Validation

**User Query**: "Compare Instagram engagement with Facebook ad spend"

**Generated SQL**:
```sql
-- Instagram engagement (last 30 days)
SELECT
  'Instagram' as platform,
  SUM(mi.likes + mi.comments + mi.saved + mi.shares) as total_engagement,
  AVG(mi.reach) as avg_reach
FROM instagram_media m
LEFT JOIN instagram_media_insights mi
  ON m.id = mi.id AND m.user_id = mi.user_id
WHERE m.user_id = 'user123'
  AND m.timestamp >= date_add('day', -30, current_date)

UNION ALL

-- Facebook ad spend (last 30 days)
SELECT
  'Facebook Ads' as platform,
  NULL as total_engagement,
  SUM(spend) as avg_reach
FROM facebook_ads_insights
WHERE user_id = 'user123'
  AND date_start >= CURRENT_DATE - INTERVAL '30' DAY
```

**Validation**:
- ✅ Both subqueries filter by user_id
- ✅ Correct date filtering for each platform
- ✅ Proper joins for Instagram
- ✅ UNION ALL for combining results
- ⚠️ NOTE: Column names don't match perfectly (avg_reach used for spend in second query) - consider aliasing

**Result**: VALID with minor naming inconsistency ✓

---

## Platform-Specific Validation Checklist

### Instagram Queries
- [ ] Filters by user_id
- [ ] Uses correct date column (timestamp for instagram_media)
- [ ] Joins instagram_media with instagram_media_insights for metrics
- [ ] Joins on both id AND user_id
- [ ] Does NOT try to filter instagram_media_insights by timestamp directly

### Facebook Ads Queries
- [ ] Filters by user_id
- [ ] Uses date_start column for date filtering
- [ ] Respects hierarchy (campaigns → ad_sets → ads)
- [ ] Joins on both id AND user_id for all joins
- [ ] Uses SUM() for metrics when aggregating across dates or ads
- [ ] Uses appropriate breakdown table for demographics/platforms

### Google Analytics Queries
- [ ] Filters by user_id
- [ ] Uses date_parse() for date column (yyyyMMdd format)
- [ ] Selects appropriate table (website_overview vs pages vs traffic_sources vs item_report)
- [ ] Uses correct column names (camelCase format)
- [ ] Uses CAST() for numeric fields when needed
