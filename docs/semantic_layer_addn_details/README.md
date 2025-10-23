# Semantic Layer Extension for ps-labs-agent

## Overview

This directory contains the semantic layer extension that adds support for **4 new data tables** to the ps-labs-agent query generation system.

## Generated Files

### 1. `schemas_extended.yaml` (29 KB)
Complete schema catalog with detailed column definitions for:
- **instagram_users** - Instagram profile data (13 columns)
- **instagram_user_insights** - Daily account metrics (14 columns)
- **facebook_ads_insights_demographics_dma_region** - Facebook Ads by DMA (107 columns!)
- **google_analytics_ecommerce_purchases_item_name_report** - E-commerce product performance (15 columns)

**Features:**
- Business-focused descriptions for every column
- Aggregatable/searchable/important flags
- Common filters and use cases documented
- Join patterns with other tables
- Example queries for each table
- Notes on common mistakes and gotchas

### 2. `query_patterns_extended.yaml` (24 KB)
Pre-built query templates covering **17 common analytics patterns**:

**Instagram (6 patterns):**
- Latest profile information
- Follower growth tracking
- Daily reach metrics
- Follower growth rate analysis
- Reach to follower ratio

**Facebook Ads (5 patterns):**
- Performance by DMA/geography
- Campaign performance summary
- Ad quality score analysis
- Daily ad spend trend

**Google Analytics (6 patterns):**
- Top selling products
- Conversion funnel analysis
- Underperforming products
- Daily e-commerce trend
- Product performance comparison

**Features:**
- Natural language use cases for each pattern
- Parameterized templates with sensible defaults
- Keyword and regex-based pattern matching
- Documented metrics calculated

### 3. `INTEGRATION_INSTRUCTIONS.md` (13 KB)
Complete integration guide with:
- Step-by-step instructions for adding to ps-labs-agent
- Testing procedures and validation queries
- Architecture notes and best practices
- Troubleshooting common issues
- Data quality notes
- Future enhancement ideas

### 4. `EXISTING_TABLES_REVIEW.md` (22 KB)
Review and enhancement suggestions for the 2 tables already in agent's semantic layer:
- **instagram_media** - Detailed column descriptions, join patterns, example queries
- **instagram_media_insights** - Complete metric definitions, REELS handling, engagement calculations
- **3 Additional Query Patterns** for these existing tables
- **Critical Notes** on common mistakes (saved vs saves, REELS metrics, join requirements)
- **Suggested Enhancements** to add to existing schema definitions

## Quick Stats

- **New Tables Added:** 4 tables (instagram_users, instagram_user_insights, facebook_ads, google_analytics)
- **Existing Tables Enhanced:** 2 tables (instagram_media, instagram_media_insights)
- **Total Tables:** 6 tables
- **Columns Documented:** 220+ columns
- **Query Patterns:** 20 patterns (17 new + 3 for existing tables)
- **Use Cases:** 60+ natural language questions
- **Example Queries:** 30+ tested Athena queries

## Discovery Process

### Phase 1: Discovery
- Listed all Glue databases and tables
- Identified 4 new tables not in existing semantic layer
- Extracted complete schemas from Glue Data Catalog

### Phase 2: Data Analysis
- Queried sample data from each table using Athena
- Analyzed column types, formats, and patterns
- Identified key business metrics and use cases

### Phase 3: Schema Generation
- Created comprehensive column definitions
- Added metadata (aggregatable, searchable, important flags)
- Documented common joins and filters
- Included practical example queries

### Phase 4: Pattern Generation
- Identified common questions for each table
- Created optimized query templates
- Added parameter defaults and validation
- Built keyword/regex pattern matching

### Phase 5: Documentation
- Created integration instructions
- Added testing procedures
- Documented troubleshooting steps
- Included architecture notes

## Key Highlights

### 1. Production-Ready Queries
All query templates:
- ✅ Filter by `user_id` (required for performance)
- ✅ Use partition columns efficiently
- ✅ Include NULLIF to prevent division errors
- ✅ Have sensible defaults and limits
- ✅ Tested in Athena

### 2. Comprehensive Metadata
Every column includes:
- Business-focused description
- Data type and format
- Usage flags (aggregatable, searchable, important)
- Common filters and use cases
- Related metrics and calculations
- Notes on common mistakes

### 3. Intelligent Pattern Matching
- Keyword-based matching for quick lookups
- Regex patterns for complex questions
- Multiple suggestions for ambiguous queries

## Integration into ps-labs-agent

### Step 1: Copy Schema Definitions
Append contents of `schemas_extended.yaml` to `ps-labs-agent/semantic_layer/schemas.yaml`

### Step 2: Add Query Patterns
Append contents of `query_patterns_extended.yaml` to `ps-labs-agent/semantic_layer/query_patterns.yaml`

### Step 3: Review Existing Tables
Check `EXISTING_TABLES_REVIEW.md` for suggested enhancements to the 2 existing Instagram tables already in the agent

### Step 4: Test
Run example questions to verify integration:
```
"Show my current Instagram profile"
"Which cities are my ads performing best in?"
"What are my best-selling products?"
```

See `INTEGRATION_INSTRUCTIONS.md` for detailed steps.

## Data Source Reference

All data comes from AWS Glue Data Catalog:
- **Database (DEV):** `ps_labs_dev_processed_catalog`
- **Database (PROD):** `ps_labs_prod_processed_catalog`
- **Region:** `us-east-2`

Tables are populated by Glue Processing jobs:
- `glue_processing_instagram_users.py`
- `glue_processing_instagram_user_insights.py`
- `glue_processing_facebook_dma_insights.py`
- `glue_processing_ga_item_report.py`

## Questions and Support

- **Data Schema:** See `docs/development/DOC_DATA_SCHEMA.md` in ps-labs-data
- **Glue Config:** See `data-pipelines/config/glue_jobs_config.yaml`
- **Processing Logic:** See `data-pipelines/glue_jobs/glue_processing_*.py`

---

**Generated:** 2025-10-22
**Version:** 1.0
**Status:** Ready for Integration
