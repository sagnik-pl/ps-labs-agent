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

We have data from three platforms:
- **Instagram** (5 tables) - Social media content and engagement
- **Facebook Ads** (12 tables) - Advertising campaigns, performance, and breakdowns
- **Google Analytics** (8 tables) - Website traffic, ecommerce, and user behavior

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

---

### Facebook Ads Tables

#### CRITICAL: Facebook Ads Table Structure

**Hierarchical Structure:**
- facebook_campaigns (top level)
- facebook_ad_sets (middle level)
- facebook_ads (bottom level - individual ads)
- facebook_ad_creatives (creative assets)

**Performance Data:**
- facebook_ads_insights (base metrics - INCREMENTAL)
- facebook_ads_insights_age_and_gender (demographic breakdown)
- facebook_ads_insights_delivery_platform_and_device_platform (platform breakdown)
- facebook_ads_insights_action_type (action breakdown)
- facebook_ads_insights_action_reaction (reaction breakdown)
- facebook_ads_insights_action_product_id (product breakdown)
- facebook_ads_insights_action_conversion_device (device breakdown)
- facebook_dma_insights (geographic DMA breakdown)

#### Key Characteristics

**`facebook_ads_insights` is INCREMENTAL:**
- Updates daily with new date_start records
- One row per ad_id + date_start combination
- Use `date_start` column for time-based filtering
- Contains: spend, impressions, clicks, conversions, revenue metrics

**Date Filtering:**
```sql
-- ✅ CORRECT: Use date_start for time filtering
WHERE date_start >= '2024-01-01'
  AND date_start <= '2024-12-31'

-- ✅ CORRECT: Last 30 days
WHERE date_start >= CURRENT_DATE - INTERVAL '30' DAY
```

**Hierarchical Joins:**
```sql
-- To get campaign-level metrics from ad-level data
SELECT
  c.campaign_name,
  SUM(i.spend) as total_spend,
  SUM(i.impressions) as total_impressions
FROM facebook_ads_insights i
LEFT JOIN facebook_ads a ON i.ad_id = a.id AND i.user_id = a.user_id
LEFT JOIN facebook_ad_sets ads ON a.adset_id = ads.id AND a.user_id = ads.user_id
LEFT JOIN facebook_campaigns c ON ads.campaign_id = c.id AND ads.user_id = c.user_id
WHERE i.user_id = '{user_id}'
  AND i.date_start >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY c.campaign_name
```

**ALWAYS join on id AND user_id** for:
- Data isolation
- Query performance
- Correct results

#### Common Query Patterns

**Total Spend and ROAS:**
```sql
SELECT
  SUM(spend) as total_spend,
  SUM(purchase_value) as total_revenue,
  SUM(purchase_value) / NULLIF(SUM(spend), 0) as roas
FROM facebook_ads_insights
WHERE user_id = '{user_id}'
  AND date_start >= CURRENT_DATE - INTERVAL '30' DAY
```

**Campaign Performance:**
```sql
SELECT
  c.campaign_name,
  c.status,
  SUM(i.spend) as spend,
  SUM(i.impressions) as impressions,
  SUM(i.clicks) as clicks,
  SUM(i.clicks) * 100.0 / NULLIF(SUM(i.impressions), 0) as ctr
FROM facebook_ads_insights i
LEFT JOIN facebook_ads a ON i.ad_id = a.id AND i.user_id = a.user_id
LEFT JOIN facebook_ad_sets ads ON a.adset_id = ads.id AND a.user_id = ads.user_id
LEFT JOIN facebook_campaigns c ON ads.campaign_id = c.id AND ads.user_id = c.user_id
WHERE i.user_id = '{user_id}'
  AND i.date_start >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY c.campaign_name, c.status
ORDER BY spend DESC
```

**Demographic Breakdown:**
```sql
-- Use the age_and_gender breakdown table
SELECT
  age,
  gender,
  SUM(spend) as spend,
  SUM(impressions) as impressions
FROM facebook_ads_insights_age_and_gender
WHERE user_id = '{user_id}'
  AND date_start >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY age, gender
ORDER BY spend DESC
```

---

### Google Analytics Tables

#### CRITICAL: Google Analytics Table Characteristics

**All GA tables are INCREMENTAL:**
- Update daily with new date records
- Use `date` column (format: yyyyMMdd, e.g., "20240115")
- One row per date + dimension combination

**Key Tables:**
- ga_website_overview (high-level site metrics)
- ga_daily_active_users (user activity metrics)
- ga_pages (page-level performance)
- ga_pages_path_report (page path analysis)
- ga_traffic_sources (traffic source attribution)
- ga_traffic_acquisition_session_medium (medium breakdown)
- ga_traffic_acquisition_session_source (source breakdown)
- ga_item_report (ecommerce product performance)

#### Date Column Format

**CRITICAL:** GA date format is `yyyyMMdd` STRING, not DATE type.

```sql
-- ✅ CORRECT: Convert string date to date type for filtering
WHERE date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY

-- ✅ CORRECT: Direct string comparison (be careful with format)
WHERE date >= '20240101'
  AND date <= '20241231'

-- ❌ WRONG: Treating as date directly
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
```

#### Common Query Patterns

**Website Traffic Overview:**
```sql
SELECT
  date_parse(date, '%Y%m%d') as visit_date,
  totalUsers,
  newUsers,
  sessions,
  engagementRate,
  bounceRate
FROM ga_website_overview
WHERE user_id = '{user_id}'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY
ORDER BY visit_date DESC
```

**Traffic Source Analysis:**
```sql
SELECT
  sessionDefaultChannelGroup,
  SUM(sessions) as total_sessions,
  SUM(totalUsers) as total_users,
  AVG(CAST(averageSessionDuration AS DOUBLE)) as avg_duration
FROM ga_traffic_sources
WHERE user_id = '{user_id}'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY sessionDefaultChannelGroup
ORDER BY total_sessions DESC
```

**Top Products (Ecommerce):**
```sql
SELECT
  itemName,
  SUM(itemRevenue) as revenue,
  SUM(itemsPurchased) as units_sold,
  SUM(itemRevenue) / NULLIF(SUM(itemsPurchased), 0) as avg_price
FROM ga_item_report
WHERE user_id = '{user_id}'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY itemName
ORDER BY revenue DESC
LIMIT 20
```

**Page Performance:**
```sql
SELECT
  pageTitle,
  pagePath,
  SUM(screenPageViews) as total_views,
  AVG(CAST(averageEngagementTime AS DOUBLE)) as avg_engagement_time
FROM ga_pages
WHERE user_id = '{user_id}'
  AND date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY pageTitle, pagePath
ORDER BY total_views DESC
LIMIT 20
```

---

## Cross-Platform Best Practices

### Date Filtering Summary

| Platform | Table | Date Column | Format | Example Filter |
|----------|-------|-------------|--------|----------------|
| Instagram | instagram_media | `timestamp` | TIMESTAMP | `timestamp >= date_add('day', -30, current_date)` |
| Instagram | instagram_media_insights | (none) | N/A | JOIN with instagram_media and filter on m.timestamp |
| Facebook | facebook_ads_insights | `date_start` | STRING (YYYY-MM-DD) | `date_start >= CURRENT_DATE - INTERVAL '30' DAY` |
| Google Analytics | All GA tables | `date` | STRING (yyyyMMdd) | `date_parse(date, '%Y%m%d') >= CURRENT_DATE - INTERVAL '30' DAY` |

### Partition Key Usage

**ALL tables use the same partition structure:**
- `user_id` (ALWAYS filter on this)
- `year`, `month`, `day` (optional for performance)

```sql
-- ✅ ALWAYS include user_id filter
WHERE user_id = '{user_id}'

-- ✅ Optional: Add partition filters for better performance
WHERE user_id = '{user_id}'
  AND year = '2024'
  AND month = '10'
```
