# Semantic Layer Extension: Complete Data Pipeline Coverage

## Overview

This semantic layer extension adds comprehensive support for **new data tables** from the ps-labs-data pipeline:

### New Tables Added:
1. **instagram_users** - Instagram business profile information (follower counts, bio, media counts)
2. **instagram_user_insights** - Daily Instagram account-level metrics (reach, follower growth)
3. **facebook_ads_insights_demographics_dma_region** - Facebook Ads performance by DMA region
4. **google_analytics_ecommerce_purchases_item_name_report** - GA4 e-commerce product performance
5. There are more new tables which was added later

### Existing Tables Enhanced:
5. **instagram_media** - Instagram posts (already in agent, see EXISTING_TABLES_REVIEW.md for enhancements)
6. **instagram_media_insights** - Post performance metrics (already in agent, see EXISTING_TABLES_REVIEW.md for enhancements)

### Files Generated:
1. **`schemas_extended.yaml`** - Complete schema catalog for 4 new tables with 200+ columns documented
2. **`query_patterns_extended.yaml`** - 17 pre-built query patterns for new tables
3. **`EXISTING_TABLES_REVIEW.md`** - Enhancement suggestions for 2 existing tables + 3 additional query patterns
Note: Since newer tables were added later - files names could have changed. 

---

## Summary of Coverage

### Instagram Tables (4 total: 2 new + 2 enhanced):
**New Tables:**
- **instagram_users**: Full profile data with follower counts, media counts, biography
- **instagram_user_insights**: Daily metrics including reach, weekly reach, monthly reach, follower growth

**Existing Tables (Enhanced):**
- **instagram_media**: Posts with captions, timestamps, media types (see EXISTING_TABLES_REVIEW.md)
- **instagram_media_insights**: Post performance - likes, reach, saves, shares, comments (see EXISTING_TABLES_REVIEW.md)

**Query Patterns Added (9 total for Instagram):**
- 6 patterns for new tables (profile, growth, reach)
- Latest Instagram profile information
- Follower growth tracking
- Daily reach metrics
- Follower growth rate analysis
- Reach to follower ratio (penetration rate)
- 3 patterns for existing tables (top posts, REELS performance, performance by type)

### Facebook Advertising (1 table):
- **facebook_ads_insights_demographics_dma_region**: Complete Facebook Ads metrics by geographic market (DMA)

**Query Patterns Added (5):**
- Performance by DMA/geographic market
- Campaign performance summary
- Ad quality score analysis
- Daily ad spend trend

### Google Analytics E-commerce (1 table):
- **google_analytics_ecommerce_purchases_item_name_report**: Product performance with conversion funnel metrics

**Query Patterns Added (6):**
- Top selling products by revenue
- Product conversion funnel analysis
- Underperforming products identification
- Daily e-commerce trend
- Product performance comparison/benchmarking

---

## Integration Steps for ps-labs-agent Repository

### Step 1: Copy Schema Definitions

Add the contents of `schemas_extended.yaml` to the existing `semantic_layer/schemas.yaml` file in the agent repo.

**Location:** `ps-labs-agent/semantic_layer/schemas.yaml`

**Action:** Append the 4 new table definitions under the existing `tables:` section:

```yaml
tables:
  # Existing instagram_media and instagram_media_insights...

  # ADD THESE NEW TABLES:
  instagram_users:
    description: "Instagram business account profile information..."
    # ... (copy full definition from schemas_extended.yaml)

  instagram_user_insights:
    description: "Daily Instagram account-level metrics..."
    # ... (copy full definition)

  facebook_ads_insights_demographics_dma_region:
    description: "Facebook Ads performance metrics by DMA..."
    # ... (copy full definition)

  google_analytics_ecommerce_purchases_item_name_report:
    description: "Google Analytics 4 e-commerce item performance..."
    # ... (copy full definition)
```

### Step 2: Add Query Patterns

Add the contents of `query_patterns_extended.yaml` to the existing `semantic_layer/query_patterns.yaml` file.

### Step 3: Review and Enhance Existing Tables

**Important:** The agent already has definitions for `instagram_media` and `instagram_media_insights`.

**Action:** Review `EXISTING_TABLES_REVIEW.md` and add any missing details to the existing schema definitions:

1. **Enhanced Column Metadata** - Add important flags, common filters, usage notes
2. **3 Additional Query Patterns** - Top posts, REELS performance, performance by media type
3. **Critical Notes** - Common mistakes like `saved` vs `saves` column name
4. **Join Patterns** - Proper join syntax between media and insights tables

The review document provides complete YAML snippets ready to merge into existing definitions.

**Location:** `ps-labs-agent/semantic_layer/query_patterns.yaml`

**Action:** Append the 17 new patterns under the existing `patterns:` section, and merge the keyword/question pattern matching:

```yaml
patterns:
  # Existing patterns...

  # ADD THESE NEW PATTERNS:
  instagram_latest_profile:
    name: "Latest Instagram Profile Information"
    # ... (copy full definition from query_patterns_extended.yaml)

  instagram_follower_growth:
    # ... (copy full definition)

  # ... (add all 17 patterns)

# MERGE THESE into existing pattern_matching section:
pattern_matching:
  keywords:
    # Existing keywords...
    # ADD new keywords from query_patterns_extended.yaml
    profile: ["instagram_latest_profile"]
    growth: ["instagram_follower_growth", "instagram_follower_growth_rate"]
    dma: ["facebook_ads_performance_by_dma"]
    bestsellers: ["ga_top_selling_products"]
    # ... etc

  question_patterns:
    # Existing patterns...
    # ADD new question patterns
    - pattern: ".*(follower|instagram).*grow.*"
      suggested_patterns: ["instagram_follower_growth", "instagram_follower_growth_rate"]
    # ... etc
```

### Step 4: Update Table Registry (if applicable)

If the agent has a table registry or index file, add the 4 new tables to the available tables list.

### Step 5: Update Documentation

Update any agent documentation to reflect the new tables and capabilities:

- Instagram: Now supports profile data AND user insights (reach, growth)
- Facebook Ads: Now supports DMA-level geographic analysis
- Google Analytics: Now supports e-commerce product performance analysis

---

## Testing the Integration

After integration, test with these example questions:

### Instagram Profile & Growth:
```
"Show my current Instagram profile"
"How many followers did I gain this month?"
"What's my follower growth rate?"
"What percentage of my followers am I reaching?"
```

### Facebook Ads:
```
"Which cities are my ads performing best in?"
"Show my campaign performance summary"
"Which ads have low quality scores?"
"What's my daily ad spend trend?"
```

### Google Analytics E-commerce:
```
"What are my best-selling products?"
"Show the conversion funnel for my products"
"Which products have high views but low sales?"
"Compare product performance"
```

### Athena Query Validation:

Test queries directly in Athena to ensure they work:

```sql
-- Test Instagram users
SELECT * FROM ps_labs_prod_processed_catalog.instagram_users
WHERE user_id = 'test_user_id'
ORDER BY year DESC, month DESC, day DESC
LIMIT 1;

-- Test Instagram user insights
SELECT * FROM ps_labs_prod_processed_catalog.instagram_user_insights
WHERE user_id = 'test_user_id'
  AND CAST(date AS timestamp) >= date_add('day', -7, current_date)
ORDER BY date DESC;

-- Test Facebook Ads
SELECT dma, SUM(spend) as spend
FROM ps_labs_prod_processed_catalog.facebook_ads_insights_demographics_dma_region
WHERE user_id = 'test_user_id'
  AND date_start >= date_add('day', -30, current_date)
GROUP BY dma
ORDER BY spend DESC
LIMIT 10;

-- Test Google Analytics
SELECT itemname, SUM(itemrevenue) as revenue
FROM ps_labs_prod_processed_catalog.google_analytics_ecommerce_purchases_item_name_report
WHERE user_id = 'test_user_id'
  AND CAST(date AS integer) >= CAST(format_datetime(date_add('day', -30, current_date), 'yyyyMMdd') AS integer)
GROUP BY itemname
ORDER BY revenue DESC
LIMIT 10;
```

---

## Key Features of This Extension

### 1. Comprehensive Column Documentation
- Every column has business-focused descriptions
- Important columns are flagged with `important: true`
- System columns (ETL metadata) clearly marked
- Common mistakes and gotchas documented in `notes`

### 2. Rich Metadata for Query Generation
- **Aggregatable flags**: Know which columns can be summed/averaged
- **Filter requirements**: user_id must always be filtered
- **Common filters**: Pre-defined filter examples for each column
- **Used in metrics**: Which metrics/calculations use each column
- **Enum values**: Valid values for categorical columns

### 3. Join Patterns Documented
- Each table documents common joins with other tables
- Join keys and conditions specified
- Use cases for each join explained

### 4. Production-Ready Query Templates
- All queries filter by user_id (required for performance)
- Use partition columns (year/month/day) efficiently
- Include NULLIF to prevent division by zero
- Proper aggregations and grouping
- Sensible defaults and limits

### 5. Pattern Matching Intelligence
- Keyword-based pattern matching for quick lookups
- Regex-based question pattern matching
- Multiple patterns can be suggested for ambiguous questions

---

## Architecture Notes

### Partition Strategy
All tables use the same partition strategy:
```
user_id={id}/year={yyyy}/month={mm}/day={dd}/
```

**Critical:** ALWAYS filter by `user_id` first for performance. This enables partition pruning.

### Data Refresh Patterns

1. **instagram_users** - FULL REFRESH
   - Each sync replaces previous data
   - Use most recent partition for current state

2. **instagram_user_insights** - INCREMENTAL
   - Each row is a daily snapshot
   - Use `date` field for time-based queries
   - Partitions derived from `date` field

3. **facebook_ads_insights_demographics_dma_region** - INCREMENTAL
   - Each row is a DMA-level daily snapshot
   - Multiple rows per ad per day (one per DMA)

4. **google_analytics_ecommerce_purchases_item_name_report** - INCREMENTAL
   - Each row is item-level daily metrics
   - Use YYYYMMDD format in `date` field

### Complex Data Types

**Facebook Ads** has complex nested arrays:
- `actions`, `conversions`, `action_values`, `purchase_roas`
- These contain attribution window breakdowns (1d_click, 7d_click, 28d_click)
- Use `CROSS JOIN UNNEST` to extract specific values

Example:
```sql
SELECT
  ad_name,
  action.action_type,
  action.value
FROM facebook_ads_insights_demographics_dma_region
CROSS JOIN UNNEST(conversions) AS t(action)
WHERE action.action_type = 'purchase'
```

---

## Common Use Cases Enabled

### Brand Growth Analysis:
- Track Instagram follower growth over time
- Calculate growth rates and acceleration
- Measure reach penetration (% of followers reached)
- Correlate posting activity with growth

### Geographic Marketing Optimization:
- Identify best-performing geographic markets (DMAs)
- Optimize ad spend by region
- Find underperforming markets
- A/B test creatives by geography

### E-commerce Product Intelligence:
- Identify bestsellers and top revenue drivers
- Find products with high views but low conversion
- Analyze conversion funnel drop-off points
- Compare product performance vs benchmarks

### Advertising ROI & Efficiency:
- Track cost per click, cost per link click by campaign
- Monitor ad quality scores
- Identify campaigns needing optimization
- Analyze daily spend trends

---

## Data Quality Notes

### Instagram User Insights:
- Some dates may have null/zero values for reach metrics
- `online_followers` is a JSON string that needs parsing
- Follower count can decrease (unfollows)

### Facebook Ads:
- Quality rankings only available for active ads with sufficient data
- Some complex array fields may be null
- Spend is in account currency (check `account_currency`)
- DMA names may vary (normalize if needed)

### Google Analytics:
- Item names include variant details (size, color, etc.)
- Zero revenue doesn't mean zero purchases (check `itemspurchased`)
- Date format is YYYYMMDD (need to cast for date comparisons)
- Rates are pre-calculated (don't recalculate to avoid rounding errors)

---

## Future Enhancements

Potential additions for future iterations:

1. **Cross-Platform Analysis:**
   - Join Instagram media with user insights to correlate post performance with reach
   - Combine Facebook Ads with Google Analytics to track full customer journey
   - Attribution modeling across platforms

2. **Advanced Metrics:**
   - Cohort analysis for followers
   - Lifetime value calculations
   - Predictive churn models
   - Seasonality detection

3. **Additional Tables:**
   - Instagram media (already in semantic layer, can extend)
   - Instagram media insights (already in semantic layer)
   - Facebook campaigns/adsets (parent levels)
   - Google Analytics traffic sources
   - Shopify orders (if available)

---

## Support and Troubleshooting

### Common Issues:

**Issue:** Query returns no results
- **Check:** user_id filter is correct
- **Check:** Date partitions exist for requested time range
- **Check:** Table has data for that user

**Issue:** Query timeout
- **Check:** user_id filter is present
- **Check:** Using partition columns in WHERE clause
- **Check:** Not scanning too many partitions

**Issue:** "Column not found" error
- **Check:** Column names match exactly (case-sensitive in some contexts)
- **Check:** Complex columns may need UNNEST
- **Check:** Using correct database name (prod vs dev)

### Debugging Queries:

1. **Start simple:** Test with COUNT(*) and user_id filter
2. **Add partitions:** Add year/month/day filters
3. **Verify data:** Check sample rows before aggregating
4. **Build up:** Add columns and aggregations incrementally

---

## Files in This Delivery

1. **schemas_extended.yaml** (2,800+ lines)
   - 4 new table definitions
   - 200+ columns documented
   - Rich metadata and examples

2. **query_patterns_extended.yaml** (600+ lines)
   - 17 query patterns for new tables
   - Multiple use cases per pattern
   - Keyword and regex pattern matching

3. **EXISTING_TABLES_REVIEW.md** (1,100+ lines)
   - Complete review of 2 existing Instagram tables
   - Enhanced schema definitions with all metadata
   - 3 additional query patterns
   - Critical notes on common mistakes
   - Join patterns and example queries

4. **INTEGRATION_INSTRUCTIONS.md** (this file)
   - Step-by-step integration guide
   - Testing procedures
   - Architecture notes
   - Troubleshooting guide

5. **README.md**
   - Quick reference and overview
   - File descriptions and stats

---

## Validation Checklist

Before deploying to production:

- [ ] All 4 table schemas added to agent's schemas.yaml
- [ ] All 17 query patterns added to agent's query_patterns.yaml
- [ ] Pattern matching keywords merged correctly
- [ ] Test queries run successfully in Athena
- [ ] Agent can answer test questions
- [ ] Documentation updated
- [ ] User-facing features updated to reflect new capabilities

---

## Contact and Questions

For questions about this semantic layer extension:
- Data schema questions: Reference `docs/development/DOC_DATA_SCHEMA.md` in ps-labs-data repo
- Glue job configs: See `data-pipelines/config/glue_jobs_config.yaml`
- Processing logic: Check `data-pipelines/glue_jobs/glue_processing_*.py`

---

**Generated:** 2025-10-22
**Version:** 1.0
**Coverage:** 4 tables, 200+ columns, 17 query patterns
