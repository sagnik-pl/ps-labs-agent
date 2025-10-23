# Review of Existing Semantic Layer Tables

## Overview

The ps-labs-agent repository already has semantic layer definitions for 2 Instagram tables:
- `instagram_media`
- `instagram_media_insights`

This document provides a **completeness check** and suggests any enhancements or missing elements to add to the existing definitions.

---

## Table 1: instagram_media

### Current Schema in Glue Data Catalog

**Columns (9 total):**
1. `id` (string) - Media post ID
2. `media_type` (string) - Type of media (IMAGE, VIDEO, CAROUSEL_ALBUM, REELS)
3. `thumbnail_url` (string) - Thumbnail image URL
4. `caption` (string) - Post caption text
5. `timestamp` (timestamp) - When the post was published
6. `permalink` (string) - Instagram post URL
7. `username` (string) - Username who posted
8. `glue_processed_at` (timestamp) - ETL processing timestamp
9. `source` (string) - Data source identifier

**Partitions:**
- `user_id` (string)
- `year` (string)
- `month` (string)
- `day` (string)

### Suggested Enhancements for Existing Schema

If the agent's schema is missing any of these details, add them:

```yaml
instagram_media:
  description: "Instagram media posts including images, videos, carousels, and reels. Contains post metadata like captions, timestamps, and media types."
  category: "social_media"

  columns:
    id:
      name: "id"
      type: "string"
      description: "Unique Instagram media post ID (format: 17960366022605142400)"
      primary_key: true
      important: true
      notes: "Use this ID to join with instagram_media_insights for performance data"

    media_type:
      name: "media_type"
      type: "string"
      description: "Type of Instagram post"
      important: true
      enum_values: ["IMAGE", "VIDEO", "CAROUSEL_ALBUM", "REELS"]
      common_filters: ["media_type = 'REELS'", "media_type IN ('IMAGE', 'VIDEO')"]
      notes: "REELS have different metrics (watch time) than other types"

    thumbnail_url:
      name: "thumbnail_url"
      type: "string"
      description: "URL to the post's thumbnail image on Instagram CDN"
      notes: "May expire after some time"

    caption:
      name: "caption"
      type: "string"
      description: "Text caption/description of the post"
      searchable: true
      important: true
      notes: "Use for content analysis, hashtag extraction, sentiment analysis"

    timestamp:
      name: "timestamp"
      type: "timestamp"
      description: "When the post was published on Instagram"
      important: true
      common_filters: ["timestamp >= date_add('day', -30, current_date)"]
      notes: "Use this for time-based analysis, NOT the partition columns"

    permalink:
      name: "permalink"
      type: "string"
      description: "Direct link to the Instagram post"
      notes: "Format: www.instagram.com/p/[shortcode]/"

    username:
      name: "username"
      type: "string"
      description: "Instagram username who posted this media"
      searchable: true
      important: true

    glue_processed_at:
      name: "glue_processed_at"
      type: "timestamp"
      description: "Timestamp when this record was processed by Glue ETL pipeline"
      system_column: true

    source:
      name: "source"
      type: "string"
      description: "Data source identifier - always 'instagram/media' or 'instagram_media'"
      system_column: true

    user_id:
      name: "user_id"
      type: "string"
      description: "Firebase user ID - REQUIRED for all queries"
      partition_key: true
      filter_required: true
      important: true

    year:
      name: "year"
      type: "string"
      description: "Partition: Year from raw data sync (NOT from timestamp)"
      partition_key: true
      notes: "Use for partition pruning, but filter on timestamp for actual date ranges"

    month:
      name: "month"
      type: "string"
      description: "Partition: Month from raw data sync"
      partition_key: true

    day:
      name: "day"
      type: "string"
      description: "Partition: Day from raw data sync"
      partition_key: true

  primary_key: ["id", "user_id"]
  partition_keys: ["user_id", "year", "month", "day"]

  common_joins:
    - table: "instagram_media_insights"
      type: "INNER JOIN"
      on: ["id"]
      description: "Join media posts with their performance metrics (likes, reach, saves)"

    - table: "instagram_users"
      type: "LEFT JOIN"
      on: ["user_id"]
      description: "Enrich posts with account profile information"

  important_notes:
    - "ALWAYS filter by user_id for performance"
    - "Use timestamp field for date filtering, NOT partition columns"
    - "Partition columns are from sync date, not post date"
    - "Join with media_insights to get performance data (likes, reach, etc.)"
    - "REELS have additional metrics (avg_watch_time) in media_insights"

  example_queries:
    - description: "Get recent posts with basic info"
      sql: |
        SELECT
          id,
          media_type,
          caption,
          timestamp,
          permalink,
          username
        FROM ps_labs_prod_processed_catalog.instagram_media
        WHERE user_id = '{user_id}'
          AND timestamp >= date_add('day', -30, current_date)
        ORDER BY timestamp DESC
        LIMIT 50

    - description: "Get posts by media type"
      sql: |
        SELECT
          media_type,
          COUNT(*) as post_count,
          MIN(timestamp) as first_post,
          MAX(timestamp) as latest_post
        FROM ps_labs_prod_processed_catalog.instagram_media
        WHERE user_id = '{user_id}'
          AND year = '2025'
        GROUP BY media_type
        ORDER BY post_count DESC

    - description: "Search posts by caption keyword"
      sql: |
        SELECT
          id,
          caption,
          media_type,
          timestamp,
          permalink
        FROM ps_labs_prod_processed_catalog.instagram_media
        WHERE user_id = '{user_id}'
          AND LOWER(caption) LIKE '%{keyword}%'
          AND timestamp >= date_add('day', -90, current_date)
        ORDER BY timestamp DESC
        LIMIT 20
```

---

## Table 2: instagram_media_insights

### Current Schema in Glue Data Catalog

**Columns (14 total):**
1. `id` (string) - Media post ID (joins with instagram_media.id)
2. `page_id` (string) - Facebook Page ID
3. `business_account_id` (string) - Instagram Business Account ID
4. `likes` (bigint) - Number of likes
5. `reach` (bigint) - Number of unique accounts reached
6. `saved` (bigint) - Number of saves (bookmarks)
7. `shares` (bigint) - Number of shares
8. `follows` (bigint) - Number of follows from this post
9. `comments` (bigint) - Number of comments
10. `profile_visits` (string) - Number of profile visits from this post
11. `ig_reels_avg_watch_time` (double) - Average watch time for reels (seconds)
12. `ig_reels_video_view_total_time` (double) - Total watch time for reels (seconds)
13. `glue_processed_at` (timestamp) - ETL processing timestamp
14. `source` (string) - Data source identifier

**Partitions:**
- `user_id` (string)
- `year` (string)
- `month` (string)
- `day` (string)

### Suggested Enhancements for Existing Schema

If the agent's schema is missing any of these details, add them:

```yaml
instagram_media_insights:
  description: "Performance metrics for Instagram media posts including likes, reach, saves, shares, comments, and reels watch time. Join with instagram_media for complete post analysis."
  category: "social_media"

  columns:
    id:
      name: "id"
      type: "string"
      description: "Instagram media post ID - joins with instagram_media.id"
      primary_key: true
      important: true
      notes: "Use this to join with instagram_media table for post details"

    page_id:
      name: "page_id"
      type: "string"
      description: "Facebook Page ID associated with the Instagram account"
      notes: "Use to correlate with Facebook data if needed"

    business_account_id:
      name: "business_account_id"
      type: "string"
      description: "Instagram Business Account ID - joins with instagram_users.id"
      important: true

    likes:
      name: "likes"
      type: "bigint"
      description: "Number of likes on this post"
      aggregatable: true
      important: true
      used_in_metrics: ["engagement_rate", "total_likes", "avg_likes_per_post"]
      notes: "Core engagement metric"

    reach:
      name: "reach"
      type: "bigint"
      description: "Number of unique accounts that saw this post"
      aggregatable: true
      important: true
      used_in_metrics: ["engagement_rate", "reach_rate", "viral_coefficient"]
      notes: "Different from impressions - counts unique viewers only"

    saved:
      name: "saved"
      type: "bigint"
      description: "Number of times this post was saved/bookmarked"
      aggregatable: true
      important: true
      used_in_metrics: ["save_rate", "content_value_score"]
      notes: "IMPORTANT: Column name is 'saved' NOT 'saves' - common mistake!"

    shares:
      name: "shares"
      type: "bigint"
      description: "Number of times this post was shared"
      aggregatable: true
      important: true
      used_in_metrics: ["share_rate", "viral_score"]
      notes: "Indicates viral potential and content quality"

    follows:
      name: "follows"
      type: "bigint"
      description: "Number of new follows generated by this post"
      aggregatable: true
      important: true
      used_in_metrics: ["follow_rate", "content_to_follower_conversion"]
      notes: "Measures content's ability to convert viewers to followers"

    comments:
      name: "comments"
      type: "bigint"
      description: "Number of comments on this post"
      aggregatable: true
      important: true
      used_in_metrics: ["comment_rate", "engagement_rate"]

    profile_visits:
      name: "profile_visits"
      type: "string"
      description: "Number of profile visits generated by this post"
      notes: "Type is string but contains numeric value - cast to int for calculations"

    ig_reels_avg_watch_time:
      name: "ig_reels_avg_watch_time"
      type: "double"
      description: "Average watch time in seconds for REELS only"
      aggregatable: true
      important: true
      only_for_media_type: "REELS"
      used_in_metrics: ["avg_watch_time", "retention_rate"]
      notes: "NULL for non-REELS media types"

    ig_reels_video_view_total_time:
      name: "ig_reels_video_view_total_time"
      type: "double"
      description: "Total watch time in seconds for REELS only"
      aggregatable: true
      only_for_media_type: "REELS"
      used_in_metrics: ["total_watch_time", "view_duration"]
      notes: "NULL for non-REELS media types"

    glue_processed_at:
      name: "glue_processed_at"
      type: "timestamp"
      description: "Timestamp when this record was processed by Glue ETL pipeline"
      system_column: true

    source:
      name: "source"
      type: "string"
      description: "Data source identifier - always 'instagram/media_insights' or 'instagram_media_insights'"
      system_column: true

    user_id:
      name: "user_id"
      type: "string"
      description: "Firebase user ID - REQUIRED for all queries"
      partition_key: true
      filter_required: true
      important: true

    year:
      name: "year"
      type: "string"
      description: "Partition: Year from raw data sync"
      partition_key: true

    month:
      name: "month"
      type: "string"
      description: "Partition: Month from raw data sync"
      partition_key: true

    day:
      name: "day"
      type: "string"
      description: "Partition: Day from raw data sync"
      partition_key: true

  primary_key: ["id", "user_id"]
  partition_keys: ["user_id", "year", "month", "day"]

  common_joins:
    - table: "instagram_media"
      type: "INNER JOIN"
      on: ["id", "user_id"]
      description: "Essential join to get post details (caption, timestamp, media_type, permalink)"

    - table: "instagram_users"
      type: "LEFT JOIN"
      on: ["user_id", "business_account_id = id"]
      description: "Enrich with account profile data"

  important_notes:
    - "ALWAYS filter by user_id for performance"
    - "MUST join with instagram_media to get post timestamp, caption, media_type"
    - "Column name is 'saved' NOT 'saves' - common mistake!"
    - "Reels metrics (avg_watch_time, total_time) are NULL for non-REELS posts"
    - "Calculate engagement rate: (likes + comments + saved + shares) / reach * 100"
    - "profile_visits is stored as string - cast to int for calculations"

  example_queries:
    - description: "Get top performing posts by engagement"
      sql: |
        SELECT
          m.id,
          m.caption,
          m.media_type,
          m.timestamp,
          m.permalink,
          mi.likes,
          mi.reach,
          mi.saved,
          mi.comments,
          mi.shares,
          (mi.likes + mi.comments + mi.saved + mi.shares) as total_engagement,
          CAST((mi.likes + mi.comments + mi.saved + mi.shares) AS double) / NULLIF(mi.reach, 0) * 100 as engagement_rate
        FROM ps_labs_prod_processed_catalog.instagram_media m
        INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
          ON m.id = mi.id AND m.user_id = mi.user_id
        WHERE m.user_id = '{user_id}'
          AND m.timestamp >= date_add('day', -30, current_date)
        ORDER BY total_engagement DESC
        LIMIT 20

    - description: "Analyze REELS performance with watch time"
      sql: |
        SELECT
          m.id,
          m.caption,
          m.timestamp,
          m.permalink,
          mi.likes,
          mi.reach,
          mi.saved,
          mi.ig_reels_avg_watch_time,
          mi.ig_reels_video_view_total_time,
          mi.ig_reels_video_view_total_time / NULLIF(mi.reach, 0) as avg_watch_time_per_viewer
        FROM ps_labs_prod_processed_catalog.instagram_media m
        INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
          ON m.id = mi.id AND m.user_id = mi.user_id
        WHERE m.user_id = '{user_id}'
          AND m.media_type = 'REELS'
          AND m.timestamp >= date_add('day', -30, current_date)
          AND mi.ig_reels_avg_watch_time IS NOT NULL
        ORDER BY mi.ig_reels_avg_watch_time DESC
        LIMIT 20

    - description: "Calculate engagement metrics by media type"
      sql: |
        SELECT
          m.media_type,
          COUNT(DISTINCT m.id) as post_count,
          AVG(mi.likes) as avg_likes,
          AVG(mi.reach) as avg_reach,
          AVG(mi.saved) as avg_saved,
          AVG(mi.comments) as avg_comments,
          AVG(mi.shares) as avg_shares,
          AVG(CAST((mi.likes + mi.comments + mi.saved + mi.shares) AS double) / NULLIF(mi.reach, 0) * 100) as avg_engagement_rate
        FROM ps_labs_prod_processed_catalog.instagram_media m
        INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
          ON m.id = mi.id AND m.user_id = mi.user_id
        WHERE m.user_id = '{user_id}'
          AND m.year = '2025'
        GROUP BY m.media_type
        ORDER BY avg_engagement_rate DESC
```

---

## Suggested Query Patterns to Add

### Pattern 1: Top Performing Posts
```yaml
instagram_top_posts_by_engagement:
  name: "Top Instagram Posts by Engagement"
  category: "social_media"
  description: "Identify best performing posts based on total engagement (likes + comments + saves + shares)"
  use_cases:
    - "Show my best performing Instagram posts"
    - "Which posts got the most engagement?"
    - "Top posts this month"
    - "Best content by engagement rate"
  parameters:
    user_id:
      required: true
      type: "string"
    days:
      required: false
      type: "int"
      default: 30
    limit:
      required: false
      type: "int"
      default: 20
  template: |
    SELECT
      m.id,
      m.caption,
      m.media_type,
      m.timestamp,
      m.permalink,
      mi.likes,
      mi.reach,
      mi.saved,
      mi.comments,
      mi.shares,
      (mi.likes + mi.comments + mi.saved + mi.shares) as total_engagement,
      CAST((mi.likes + mi.comments + mi.saved + mi.shares) AS double) / NULLIF(mi.reach, 0) * 100 as engagement_rate
    FROM ps_labs_prod_processed_catalog.instagram_media m
    INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
      ON m.id = mi.id AND m.user_id = mi.user_id
    WHERE m.user_id = '{user_id}'
      AND m.timestamp >= date_add('day', -{days}, current_date)
    ORDER BY total_engagement DESC
    LIMIT {limit}
  metrics_calculated:
    - "total_engagement"
    - "engagement_rate"
```

### Pattern 2: REELS Performance Analysis
```yaml
instagram_reels_performance:
  name: "Instagram REELS Performance Analysis"
  category: "social_media"
  description: "Analyze REELS-specific metrics including watch time and retention"
  use_cases:
    - "Show my REELS performance"
    - "Which REELS have the best watch time?"
    - "REELS engagement analysis"
    - "Top performing REELS"
  parameters:
    user_id:
      required: true
      type: "string"
    days:
      required: false
      type: "int"
      default: 30
    limit:
      required: false
      type: "int"
      default: 20
  template: |
    SELECT
      m.id,
      m.caption,
      m.timestamp,
      m.permalink,
      mi.likes,
      mi.reach,
      mi.saved,
      mi.comments,
      mi.shares,
      mi.ig_reels_avg_watch_time,
      mi.ig_reels_video_view_total_time,
      mi.ig_reels_video_view_total_time / NULLIF(mi.reach, 0) as avg_watch_time_per_viewer,
      (mi.likes + mi.comments + mi.saved + mi.shares) as total_engagement,
      CAST((mi.likes + mi.comments + mi.saved + mi.shares) AS double) / NULLIF(mi.reach, 0) * 100 as engagement_rate
    FROM ps_labs_prod_processed_catalog.instagram_media m
    INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
      ON m.id = mi.id AND m.user_id = mi.user_id
    WHERE m.user_id = '{user_id}'
      AND m.media_type = 'REELS'
      AND m.timestamp >= date_add('day', -{days}, current_date)
      AND mi.ig_reels_avg_watch_time IS NOT NULL
    ORDER BY mi.ig_reels_avg_watch_time DESC
    LIMIT {limit}
  metrics_calculated:
    - "avg_watch_time"
    - "total_watch_time"
    - "engagement_rate"
```

### Pattern 3: Content Performance by Type
```yaml
instagram_performance_by_media_type:
  name: "Instagram Performance by Media Type"
  category: "social_media"
  description: "Compare performance across different media types (IMAGE, VIDEO, CAROUSEL, REELS)"
  use_cases:
    - "Which content type performs best?"
    - "Compare REELS vs carousel performance"
    - "Performance by media type"
    - "What content should I post more of?"
  parameters:
    user_id:
      required: true
      type: "string"
    days:
      required: false
      type: "int"
      default: 30
  template: |
    SELECT
      m.media_type,
      COUNT(DISTINCT m.id) as post_count,
      AVG(mi.likes) as avg_likes,
      AVG(mi.reach) as avg_reach,
      AVG(mi.saved) as avg_saved,
      AVG(mi.comments) as avg_comments,
      AVG(mi.shares) as avg_shares,
      AVG((mi.likes + mi.comments + mi.saved + mi.shares)) as avg_total_engagement,
      AVG(CAST((mi.likes + mi.comments + mi.saved + mi.shares) AS double) / NULLIF(mi.reach, 0) * 100) as avg_engagement_rate,
      SUM(mi.likes) as total_likes,
      SUM(mi.reach) as total_reach
    FROM ps_labs_prod_processed_catalog.instagram_media m
    INNER JOIN ps_labs_prod_processed_catalog.instagram_media_insights mi
      ON m.id = mi.id AND m.user_id = mi.user_id
    WHERE m.user_id = '{user_id}'
      AND m.timestamp >= date_add('day', -{days}, current_date)
    GROUP BY m.media_type
    ORDER BY avg_engagement_rate DESC
  metrics_calculated:
    - "avg_engagement_rate_by_type"
    - "best_performing_media_type"
```

---

## Critical Notes for Agent Implementation

### Common Mistakes to Avoid

1. **Column Name Error:**
   - ❌ WRONG: `saves`
   - ✅ CORRECT: `saved`
   - This is the #1 mistake - the column is called `saved` NOT `saves`

2. **Missing Join:**
   - Always join `instagram_media_insights` with `instagram_media`
   - Media insights alone doesn't have timestamp, caption, or media_type
   - Use: `INNER JOIN ON m.id = mi.id AND m.user_id = mi.user_id`

3. **REELS Metrics:**
   - `ig_reels_avg_watch_time` and `ig_reels_video_view_total_time` are NULL for non-REELS
   - Always filter `media_type = 'REELS'` when using these columns
   - Check for `IS NOT NULL` to avoid division errors

4. **Engagement Rate Calculation:**
   - Use: `(likes + comments + saved + shares) / NULLIF(reach, 0) * 100`
   - Always use NULLIF to prevent division by zero
   - Note it's `saved` not `saves`

5. **Date Filtering:**
   - Filter on `instagram_media.timestamp` for actual post date
   - Don't use partition columns (year/month/day) for date ranges
   - Partitions are from sync date, not post date

---

## Summary

**For instagram_media:**
- Schema is simple with 9 columns
- Main value: Post metadata (caption, type, timestamp, permalink)
- Must join with media_insights to get performance data

**For instagram_media_insights:**
- Schema has 14 columns including engagement metrics
- Critical column name: `saved` (NOT `saves`) ⚠️
- REELS have special metrics (watch time)
- Must join with media to get post context

**Recommended Actions:**
1. Review existing agent schema - ensure all column metadata is present
2. Add the 3 suggested query patterns
3. Add critical notes about `saved` vs `saves` mistake
4. Document REELS-specific metric handling
5. Include example join queries

