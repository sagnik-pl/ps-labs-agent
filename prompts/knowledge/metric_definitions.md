# E-commerce Metric Definitions & Interpretation Guide

## Overview
This knowledge base provides detailed definitions, formulas, and interpretation guidelines for e-commerce and social media metrics. Use this to ensure accurate calculations and provide insightful recommendations.

---

## Social Media Metrics

### Engagement Rate

**Formula**: `(likes + comments + saved + shares) / reach × 100`

**What it measures**: Percentage of people who engaged with content after seeing it.

**Column Names** (IMPORTANT):
- ✅ Use: `i.saved` (NOT `i.saves`)
- Use: `i.likes`, `i.comments`, `i.shares`, `i.reach`

**Interpretation Guidelines**:
- **Poor** (< 1.5%): Content isn't resonating with audience
  - Action: Try more Reels, better hooks, stronger CTAs
- **Average** (1.5-2.5%): Baseline performance
  - Action: Experiment with content types and posting times
- **Good** (2.5-5.0%): Solid performance, content connects with audience
  - Action: Maintain consistency, analyze what's working
- **Excellent** (> 5.0%): Exceptional performance
  - Action: Analyze these posts and replicate the approach

**Category Benchmarks**:
- Fashion & Apparel: 1.8-3.5%
- Beauty & Cosmetics: 2.5-4.5%
- Home & Garden: 2.0-3.8%
- Food & Beverage: 2.8-5.0%

**SQL Expression**:
```sql
((i.likes + i.comments + i.saved + i.shares) / NULLIF(i.reach, 0)) * 100
```

**Why it matters**: Instagram's algorithm heavily favors engagement. Higher engagement = more reach.

---

### Frequency

**Formula**: `impressions / reach`

**What it measures**: Average number of times each user saw the content.

**Interpretation Guidelines**:
- **Too Low** (< 1.5): Content shown only once per user
  - Problem: Missing opportunity for repetition
  - Action: Increase posting frequency or boost top-performing content
- **Optimal** (1.5-3.0): Ideal balance of reach and repetition
  - Users see content multiple times without fatigue
  - Action: Maintain current strategy
- **Too High** (> 3.0): Risk of audience fatigue
  - Problem: Wasting ad spend showing same content repeatedly
  - Action: Reduce frequency caps or expand target audience

**SQL Expression**:
```sql
CAST(i.impressions AS DOUBLE) / NULLIF(i.reach, 0)
```

**Why it matters**: Balances brand awareness (need repetition) with audience fatigue (too much = annoying).

**Important Context**:
- **Always true**: `impressions >= reach`
- Frequency of 1.0 means each person saw content exactly once
- For paid ads, frequency above 3.0 typically shows diminishing returns

---

### Save Rate

**Formula**: `saved / reach × 100`

**What it measures**: Percentage of viewers who saved the content for later reference.

**Column Name** (CRITICAL):
- ✅ Use: `i.saved` (NOT `i.saves` - this is a common error!)

**Interpretation Guidelines**:
- **Low** (< 0.5%): Content not valuable for future reference
  - Action: Create more educational, tutorial, or reference content
- **Good** (0.5-2.0%): Content has lasting value
  - Typical for tips, how-tos, guides
- **Excellent** (> 2.0%): Highly valuable content
  - Action: Create more of this type of content

**SQL Expression**:
```sql
(CAST(i.saved AS DOUBLE) / NULLIF(i.reach, 0)) * 100
```

**Why it's CRITICAL**:
- Instagram algorithm heavily weights saves
- Saves signal "valuable content worth revisiting"
- High save rate = dramatically better organic reach

**Content Types with High Save Rates**:
- Tutorials and how-tos
- Product recommendations and reviews
- Educational infographics
- Tips and hacks
- Before/after transformations

---

### Reach Rate

**Formula**: `reach / followers × 100`

**What it measures**: Percentage of followers who actually saw the content.

**Note**: Requires joining with account/profile data to get follower count.

**Interpretation Guidelines**:
- **Poor** (< 5%): Algorithm not favoring your content
  - Problem: Low engagement signals to algorithm
  - Action: Improve post quality, better hashtags, optimal posting times
- **Good** (10-25%): Solid organic performance
  - Content reaching significant portion of followers
- **Excellent** (> 25%): Viral potential or strong engagement
  - Algorithm is amplifying your content

**Why it matters**: Measures how well Instagram's algorithm is distributing your content to your followers.

---

## E-commerce Metrics

### Conversion Rate

**Formula**: `orders / sessions × 100`

**What it measures**: Percentage of website visitors who made a purchase.

**Interpretation Guidelines**:
- **Poor** (< 1.0%): Serious UX issues, pricing problems, or poor traffic quality
  - Action: Conduct UX audit, review pricing, assess traffic sources
- **Average** (1.0-2.0%): Room for improvement
  - Action: A/B test checkout flow, improve product pages
- **Good** (2.0-3.5%): Solid performance for most categories
  - Action: Focus on incremental improvements, scaling traffic
- **Excellent** (> 3.5%): Exceptional performance
  - Action: Scale traffic while maintaining quality

**Category Benchmarks**:
- Fashion & Apparel: 1.8-2.5%
- Beauty & Cosmetics: 2.5-3.5%
- Home & Garden: 2.0-2.8%
- Food & Beverage: 2.8-3.5%
- Electronics: 1.5-2.2%

**Factors Affecting Conversion**:
- Product page quality
- Checkout friction
- Shipping costs and speed
- Trust signals (reviews, guarantees)
- Mobile experience
- Traffic source quality

---

### Cart Abandonment Rate

**Formula**: `(carts_created - orders) / carts_created × 100`

**What it measures**: Percentage of shoppers who added items to cart but didn't complete purchase.

**Interpretation Guidelines**:
- **Industry Average**: 69.8% (this is normal!)
- **Good** (60-70%): At industry standard
  - Action: Implement cart recovery emails, exit-intent popups
- **Excellent** (40-60%): Below industry average
  - Smooth checkout flow, good pricing transparency
- **Poor** (> 80%): Serious checkout issues
  - Action: Review shipping costs, simplify checkout, add trust signals

**Common Causes of Abandonment**:
1. **Unexpected costs** (48%): Shipping, taxes revealed late
2. **Account creation required** (24%): Forcing registration
3. **Complex checkout** (21%): Too many steps/forms
4. **Payment concerns** (19%): Security worries
5. **Slow delivery** (18%): Shipping time too long

**Recovery Strategies**:
- Send cart abandonment emails (1 hour, 24 hours, 72 hours)
- Offer exit-intent discounts
- Show free shipping thresholds
- Simplify checkout to 1-2 steps
- Enable guest checkout

---

### Return on Ad Spend (ROAS)

**Formula**: `revenue_from_ads / ad_spend`

**What it measures**: Revenue generated for every dollar spent on advertising.

**Interpretation Guidelines**:
- **Unprofitable** (< 1.5x): Losing money on ads
  - Action: PAUSE campaigns immediately, optimize targeting/creative
- **Break-even** (1.5-2.0x): Barely profitable
  - Action: Careful optimization needed
- **Profitable** (2.0-4.0x): Good performance for most businesses
  - Action: Scale winning campaigns gradually
- **Excellent** (> 4.0x): Exceptional performance
  - Action: Aggressively scale while monitoring for degradation

**Calculating Minimum Profitable ROAS**:
```
Minimum ROAS = 1 / Gross Margin

Examples:
- 40% margin → Need 2.5x ROAS minimum
- 50% margin → Need 2.0x ROAS minimum
- 60% margin → Need 1.67x ROAS minimum
```

**Category Benchmarks**:
- Fashion & Apparel: 2.0-4.0x
- Beauty & Cosmetics: 2.5-5.0x
- Home & Garden: 2.0-4.0x

**Important Context**:
- ROAS varies by funnel stage (TOF typically lower than BOF)
- New customer acquisition ROAS should be lower than retargeting
- Account for full customer LTV, not just first purchase

---

### Customer Acquisition Cost (CAC)

**Formula**: `total_marketing_spend / new_customers`

**What it measures**: Cost to acquire one new customer.

**The Golden Rule**: **CAC should be less than 1/3 of LTV**

**Optimal LTV:CAC Ratios**:
- **3:1** - Minimum for sustainable growth
- **4:1 to 5:1** - Ideal for healthy unit economics
- **> 5:1** - Excellent, room to scale aggressively

**Category Benchmarks**:
- Fashion & Apparel: $20-50
- Beauty & Cosmetics: $15-40
- Home & Garden: $30-70

**Why 1/3 Rule**:
- Need margin to cover: COGS, operating expenses, profit
- Example: If LTV = $150, CAC should be ≤ $50

**Factors Affecting CAC**:
- Marketing channel efficiency
- Creative quality
- Targeting precision
- Seasonality
- Competition

---

## SQL Query Best Practices

### Critical Column Names
**Common Mistakes to Avoid**:
- ❌ `i.saves` → ✅ `i.saved`
- ❌ `saved` without table alias → ✅ `i.saved`

### Division Safety
Always use `NULLIF` to prevent division by zero:
```sql
-- ❌ Wrong (will error if reach = 0)
i.likes / i.reach

-- ✅ Correct
CAST(i.likes AS DOUBLE) / NULLIF(i.reach, 0)
```

### Type Casting for Precision
Cast to DOUBLE before division for accurate percentages:
```sql
-- ❌ Integer division (truncates)
(i.likes + i.comments) / i.reach * 100

-- ✅ Float division (precise)
((i.likes + i.comments) / NULLIF(CAST(i.reach AS DOUBLE), 0)) * 100
```

### Table Joins
Always join Instagram tables on **BOTH** id AND user_id:
```sql
FROM instagram_media m
JOIN instagram_media_insights i
  ON m.id = i.id AND m.user_id = i.user_id  -- Both columns!
WHERE m.user_id = '{user_id}'
```

---

## Interpretation Framework

### Always Provide Context
1. **Compare to benchmarks**: "Your 2.8% is above industry avg of 2.0%"
2. **Show the trend**: "Up 15% from last month"
3. **Explain what it means**: "This means your content is resonating better"
4. **Give actionable advice**: "Double down on Reels which are driving this"

### Good vs Bad Interpretation

**❌ Bad**:
"Your engagement rate is 3.2%"

**✅ Good**:
"Your engagement rate is 3.2%, which is **18% above the industry average** of 2.7% for fashion brands. This excellent performance is driven by your Reels (5.1% engagement) significantly outperforming static posts (2.1%). **Recommendation**: Increase Reels frequency from 2x/week to 4x/week to capitalize on this momentum."

---

## Quick Reference: Metric Calculations

| Metric | Formula | SQL Expression |
|--------|---------|----------------|
| Engagement Rate | (likes + comments + saved + shares) / reach × 100 | `((i.likes + i.comments + i.saved + i.shares) / NULLIF(i.reach, 0)) * 100` |
| Frequency | impressions / reach | `CAST(i.impressions AS DOUBLE) / NULLIF(i.reach, 0)` |
| Save Rate | saved / reach × 100 | `(CAST(i.saved AS DOUBLE) / NULLIF(i.reach, 0)) * 100` |
| Reach Rate | reach / followers × 100 | `(CAST(i.reach AS DOUBLE) / NULLIF(a.followers, 0)) * 100` |
| Conversion Rate | orders / sessions × 100 | `(CAST(orders AS DOUBLE) / NULLIF(sessions, 0)) * 100` |
| ROAS | revenue_from_ads / ad_spend | `CAST(revenue_from_ads AS DOUBLE) / NULLIF(ad_spend, 0)` |
| CAC | total_marketing_spend / new_customers | `CAST(total_marketing_spend AS DOUBLE) / NULLIF(new_customers, 0)` |

**Remember**: Column is `saved` not `saves`! 🔴
