# Semantic Layer Generation Instructions for Data Pipeline Repo

## Context

You are working in the **data pipeline repository** that has direct access to all AWS Glue jobs, raw data sources, and processed datasets. Your task is to analyze these datasets and generate semantic layer configuration files that will be used in the **agent repository** (ps-labs-agent) for intelligent query generation and validation.

The agent repo has already created a semantic layer for Instagram datasets (`instagram_media` and `instagram_media_insights`). You need to extend this for **all other datasets** in the pipeline.

---

## Your Mission

Generate two YAML files for each dataset/table in the data pipeline:

1. **`schemas.yaml`** - Complete schema catalog with column definitions
2. **`query_patterns.yaml`** - Pre-built query templates for common analytics questions

Then create a **integration prompt** that explains how to add these to the existing semantic layer.

---

## Phase 1: Dataset Discovery & Analysis

### Step 1: Discover All Glue Tables

```bash
# List all Glue databases
aws glue get-databases --region us-east-2

# List all tables in each database
aws glue get-tables --database-name <database_name> --region us-east-2

# Get detailed schema for each table
aws glue get-table --database-name <database_name> --table-name <table_name> --region us-east-2
```

**For each table, collect:**
- Table name
- Database name
- Column names and types
- Partition keys
- Description (if available)
- Storage location

### Step 2: Fetch Sample Data

For each table, query sample data to understand:
- Actual column values and formats
- Data ranges and patterns
- Relationships between columns
- Common use cases

```sql
-- Run in Athena
SELECT * FROM <database>.<table> LIMIT 10;

-- Check distinct values for categorical columns
SELECT DISTINCT column_name FROM <database>.<table> LIMIT 20;

-- Check data ranges for numeric/date columns
SELECT
  MIN(column_name) as min_value,
  MAX(column_name) as max_value,
  COUNT(*) as total_rows
FROM <database>.<table>;
```

### Step 3: Identify Table Categories

Categorize each table into:
- `social_media` - Instagram, Facebook, TikTok data
- `ecommerce` - Shopify, orders, products, customers
- `advertising` - Meta Ads, Google Ads, TikTok Ads
- `analytics` - Google Analytics, website traffic
- `financial` - Revenue, costs, P&L data
- `inventory` - Stock levels, SKUs
- `other` - Miscellaneous tables

---

## Phase 2: Generate schemas.yaml

### Format Reference

Study the existing `schemas.yaml` structure for Instagram tables. Follow the **exact same format**:

```yaml
version: "1.0"
last_updated: "2025-10-22"

tables:
  <table_name>:
    description: "Clear description of what this table contains"
    category: "social_media|ecommerce|advertising|analytics|financial|inventory|other"
    columns:
      <column_name>:
        name: "exact_column_name"
        type: "string|bigint|double|timestamp|date|boolean|array|struct"
        description: "What this column represents"
        # Optional attributes:
        primary_key: true|false
        partition_key: true|false
        required: true|false
        filter_required: true|false  # For user_id, tenant_id, etc.
        aggregatable: true|false     # Can be used in SUM, AVG, etc.
        searchable: true|false       # Text columns
        enum_values: ["value1", "value2"]  # For categorical columns
        common_filters: ["example filter 1", "example filter 2"]
        used_in_metrics: ["metric_name1", "metric_name2"]
        important: true|false        # Flag critical columns
        notes: "Important notes about this column (e.g., common mistakes)"
        only_for_media_type: "REELS"  # Conditional columns
        system_column: true|false     # ETL metadata columns
    primary_key: ["col1", "col2"]
    partition_keys: ["user_id", "year", "month", "day"]
    common_joins:
      - table: "related_table_name"
        type: "INNER JOIN|LEFT JOIN"
        on: ["join_column1", "join_column2"]
        description: "Why and when to use this join"
    important_notes:
      - "Critical note 1 about using this table"
      - "Common mistake to avoid"
      - "Performance consideration"
    example_queries:
      - description: "What this query does"
        sql: |
          SELECT column1, column2
          FROM table_name
          WHERE user_id = '{user_id}'
          LIMIT 10
```

### Key Guidelines for schemas.yaml

1. **Column Descriptions**: Be specific and business-focused
   - L Bad: "id column"
   -  Good: "Unique order ID from Shopify (format: gid://shopify/Order/12345)"

2. **Flag Important Columns**:
   - Columns that **must** be filtered (user_id, tenant_id)
   - Columns with **common mistakes** (like 'saved' vs 'saves')
   - Columns used in **metric calculations**

3. **Document Joins**:
   - Which tables commonly join together
   - What columns to join on
   - When to use each join

4. **Add Common Filters**:
   - Time-based: `>= date_add('day', -30, current_date)`
   - Status filters: `status = 'completed'`
   - Category filters: `order_type IN ('retail', 'wholesale')`

5. **Include Example Queries**:
   - 2-3 realistic query examples per table
   - Show proper user_id filtering
   - Demonstrate common use cases

---

## Phase 3: Generate query_patterns.yaml

### Format Reference

Study the existing `query_patterns.yaml` structure. Follow the **exact same format**:

```yaml
version: "1.0"
last_updated: "2025-10-22"

patterns:
  <pattern_name>:
    name: "Human-Readable Pattern Name"
    category: "social_media|ecommerce|advertising|analytics|financial"
    description: "What this query pattern does"
    use_cases:
      - "Natural language question 1"
      - "Natural language question 2"
      - "Natural language question 3"
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
        default: 10
    template: |
      SELECT
        column1,
        column2,
        aggregation_expression AS metric_name
      FROM table_name
      WHERE user_id = '{user_id}'
        AND timestamp >= date_add('day', -{days}, current_date)
      ORDER BY metric_name DESC
      LIMIT {limit}
    metrics_calculated:
      - "metric_name1"
      - "metric_name2"

pattern_matching:
  keywords:
    <keyword>: ["pattern_name1", "pattern_name2"]

  question_patterns:
    - pattern: ".*regex pattern.*"
      suggested_patterns: ["pattern_name1", "pattern_name2"]
```

### Query Pattern Guidelines

1. **Identify Common Questions**:
   - What do users typically ask about this data?
   - Examples:
     - "What are my best-selling products?"
     - "Show revenue by channel"
     - "Top customers by lifetime value"

2. **Create Optimized Templates**:
   - Include all necessary columns
   - Use proper aggregations
   - Add appropriate filters
   - Include sorting and limits

3. **Parameterize Properly**:
   - Always include `user_id` as required
   - Common params: `days`, `limit`, `min_value`, `category`
   - Provide sensible defaults

4. **Add Keyword Matching**:
   - Map keywords to patterns
   - Create regex for complex matching
   - Think about how users phrase questions

5. **Document Metrics**:
   - List which metrics are calculated
   - Reference metric definitions if available

### Common Pattern Types to Create

**For E-commerce Tables:**
- Top products by revenue/units
- Revenue by time period
- Customer lifetime value analysis
- Order fulfillment metrics
- Inventory turnover
- Average order value trends

**For Advertising Tables:**
- ROAS by campaign/ad set
- CPA trends over time
- Top performing ads
- Budget pacing analysis
- Audience performance comparison

**For Analytics Tables:**
- Traffic sources breakdown
- Conversion funnel analysis
- Page performance metrics
- User behavior patterns
- Session analytics

**For Financial Tables:**
- P&L summary by period
- Gross margin by product/category
- Cost breakdown analysis
- Revenue forecasting data
- Cash flow analysis

---

## Phase 4: Generate Integration Prompt

After creating `schemas.yaml` and `query_patterns.yaml`, create a **third file** called `INTEGRATION_INSTRUCTIONS.md` that contains a prompt to copy-paste into the agent repo.

### Integration Prompt Template

```markdown
# Semantic Layer Extension: [Dataset Category] Tables

## Overview
This adds semantic layer support for [X] new tables from the data pipeline:
- Table 1: Purpose
- Table 2: Purpose
- ...

## Files Generated
1. `schemas_[category].yaml` - Schema catalog for [X] tables
2. `query_patterns_[category].yaml` - [Y] query patterns for common questions

## Integration Steps

### Step 1: Add Schema Files
Copy the generated schema definitions to:
`config/semantic_layer/schemas.yaml`

Add to the `tables:` section:
[Paste schema definitions here]

### Step 2: Add Query Patterns
Copy the generated patterns to:
`config/semantic_layer/query_patterns.yaml`

Add to the `patterns:` section:
[Paste pattern definitions here]

### Step 3: Update Semantic Layer Module
No code changes needed! The semantic layer automatically loads all tables and patterns.

### Step 4: Test Integration
Run this test to verify:
\`\`\`bash
python3 -c "
from utils.semantic_layer import semantic_layer
print(f'Total tables: {len(semantic_layer.schemas)}')
print(f'Total patterns: {len(semantic_layer.query_patterns)}')

# Test new tables
for table in ['table1', 'table2']:
    schema = semantic_layer.get_table_schema(table)
    print(f'{table}: {\"\" if schema else \"L\"}')
"
\`\`\`

### Step 5: Update SQL Generator
If needed, update `workflow/nodes.py` sql_generator_node to detect new table types:

\`\`\`python
if "shopify" in query.lower() or "order" in query.lower():
    for table_name in ["shopify_orders", "shopify_products"]:
        semantic_schema = semantic_layer.get_schema_for_sql_gen(table_name)
        # ... existing code
\`\`\`

### Step 6: Update Knowledge Bases (Optional)
If you created detailed metric definitions, add them to:
`prompts/knowledge/metric_definitions.md`

Follow the existing format for metric documentation.

### Step 7: Add to Data Interpreter (Optional)
If metrics are crucial for interpretation, add to:
`prompts/agents/data_interpreter.yaml`

Add new knowledge bases if created.

## Testing Checklist
- [ ] Schema files load without errors
- [ ] All new tables validate successfully
- [ ] Query patterns match correctly
- [ ] SQL generator uses new schemas
- [ ] Example queries execute successfully
- [ ] Column validation works for new tables

## Deployment
After testing locally:
1. Commit changes to `smarter_agents` branch
2. Deploy to Railway
3. Test with live queries
```

---

## Execution Instructions

### For You (Claude in Data Pipeline Repo):

**Phase 1 - Discovery:**
1. Run Glue API commands to list all databases and tables
2. Query sample data for each table (10-20 rows)
3. Document findings in a structured format

**Phase 2 - Schema Generation:**
1. For each table, create a complete schema definition following the Instagram example
2. Include all columns with rich metadata
3. Add common joins, notes, and example queries
4. Save as `schemas_[category].yaml` (e.g., `schemas_ecommerce.yaml`, `schemas_advertising.yaml`)

**Phase 3 - Pattern Generation:**
1. Brainstorm 3-5 common questions per table/category
2. Create optimized query templates for each question
3. Add keyword and pattern matching rules
4. Save as `query_patterns_[category].yaml`

**Phase 4 - Integration Instructions:**
1. Create `INTEGRATION_INSTRUCTIONS.md` with copy-paste ready content
2. Include the actual YAML content to add
3. Provide clear step-by-step integration steps
4. Add testing commands

### Deliverables

For each category of tables (e.g., ecommerce, advertising, analytics):

1. **`schemas_[category].yaml`**
   - Complete schema catalog
   - All columns documented
   - Join patterns defined
   - Example queries included

2. **`query_patterns_[category].yaml`**
   - 3-5+ common query patterns
   - Parameterized templates
   - Use cases documented
   - Keyword matching rules

3. **`INTEGRATION_INSTRUCTIONS_[category].md`**
   - Copy-paste ready integration prompt
   - Step-by-step instructions
   - Testing checklist
   - Example code snippets

---

## Quality Checklist

Before finalizing, ensure:

### Schema Quality:
- [ ] All columns have descriptions
- [ ] Data types are accurate
- [ ] Partition keys identified
- [ ] Join patterns documented
- [ ] Common filters provided
- [ ] Important notes added
- [ ] Example queries tested
- [ ] Common mistakes documented

### Query Pattern Quality:
- [ ] Patterns cover 80% of common questions
- [ ] Templates are optimized (use partitions, limits)
- [ ] Parameters have sensible defaults
- [ ] Use cases are realistic
- [ ] Keyword matching is comprehensive
- [ ] Metrics calculated are documented

### Integration Quality:
- [ ] Instructions are clear and actionable
- [ ] YAML is properly formatted
- [ ] Examples are copy-paste ready
- [ ] Testing steps are included
- [ ] Edge cases are considered

---

## Tips for Success

1. **Be Thorough**: Document everything you discover. Future Claude won't have access to raw data.

2. **Think Like a User**: What questions would a brand owner ask? Create patterns for those.

3. **Copy the Style**: Match the existing Instagram schema format exactly. Consistency is critical.

4. **Test Your YAML**: Validate YAML syntax before delivering. Use `yamllint` or online validators.

5. **Provide Context**: In descriptions, explain business meaning, not just technical details.

6. **Flag Common Errors**: If you see column names that might be confused, add warning notes.

7. **Optimize Queries**: Include LIMIT clauses, use partition columns, avoid SELECT *.

8. **Document Assumptions**: If data quality issues exist, document them in notes.

---

## Example Workflow

```bash
# 1. Discover Shopify tables
aws glue get-tables --database-name ps_labs_prod_processed_catalog --region us-east-2 | grep -i shopify

# 2. Get schema for shopify_orders
aws glue get-table --database-name ps_labs_prod_processed_catalog --table-name shopify_orders --region us-east-2 > shopify_orders_schema.json

# 3. Query sample data
athena query --query "SELECT * FROM ps_labs_prod_processed_catalog.shopify_orders LIMIT 10" > sample_data.txt

# 4. Analyze and create schemas_ecommerce.yaml

# 5. Create query_patterns_ecommerce.yaml with patterns like:
#    - top_selling_products
#    - revenue_by_day
#    - customer_lifetime_value
#    - order_fulfillment_metrics

# 6. Create INTEGRATION_INSTRUCTIONS_ecommerce.md

# 7. Deliver all three files
```

---

## Start Your Work Here

Begin by running:

```bash
# List all databases
aws glue get-databases --region us-east-2 | jq '.DatabaseList[].Name'

# For each database, list tables
# Focus on: ps_labs_prod_processed_catalog, ps_labs_dev_processed_catalog
```

Then proceed through Phases 1-4 systematically.

**Good luck! The agent repo is counting on you to extend its intelligence! =€**
