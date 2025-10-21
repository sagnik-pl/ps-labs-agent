# Financial Metrics & Unit Economics for E-commerce

## Overview
Financial metrics, profitability calculations, and healthy margin ranges for e-commerce businesses. Use this to assess business health and provide financial recommendations.

## Core Financial Metrics

### Revenue Metrics

**Gross Merchandise Value (GMV)**:
- **Definition**: Total sales value before any deductions
- **Formula**: GMV = Sum of all order values
- **Use**: Top-line growth indicator
- **Note**: Not the same as revenue (includes discounts, returns)

**Net Revenue**:
- **Definition**: Actual revenue after deductions
- **Formula**: GMV - Returns - Discounts - Canceled Orders
- **Typical Reduction**: 10-20% from GMV
- **Components**:
  - Return rate: 5-15% (category dependent)
  - Discount rate: 10-25% (promotional strategy)
  - Cancellation rate: 1-3%

**Average Order Value (AOV)**:
- **Definition**: Average amount spent per order
- **Formula**: Total Revenue / Number of Orders
- **Healthy by Category**:
  - Fashion: $65-120
  - Beauty: $45-90
  - Home: $80-180
  - Food: $35-75
  - Electronics: $150-400

**Customer Lifetime Value (LTV)**:
- **Definition**: Total revenue expected from a customer over their lifetime
- **Simple Formula**: AOV × Purchase Frequency × Average Customer Lifespan
- **Example**: $80 AOV × 3 purchases/year × 2 years = $480 LTV
- **Advanced Formula**: Includes margins - AOV × Purchase Frequency × Customer Lifespan × Gross Margin

### Profitability Metrics

**Gross Margin**:
- **Definition**: Revenue minus direct costs of goods
- **Formula**: (Revenue - COGS) / Revenue × 100
- **Healthy Ranges**:
  - Fashion & Apparel: 50-60%
  - Beauty & Cosmetics: 60-70%
  - Home & Garden: 45-55%
  - Food & Beverage: 35-45%
  - Electronics: 30-40%
  - Jewelry: 60-75%
- **Interpretation**:
  - Below 35%: Very tight margins, scaling difficult
  - 35-50%: Workable, need high volume
  - 50-65%: Healthy, room for marketing investment
  - Above 65%: Excellent, strong pricing power

**Contribution Margin**:
- **Definition**: Revenue minus all variable costs
- **Formula**: Revenue - (COGS + Marketing + Shipping + Transaction Fees)
- **Also Called**: Contribution Margin I (CM1)
- **Healthy Range**: 20-40%
- **Interpretation**:
  - Negative: Losing money on every order
  - 0-15%: Barely profitable, need efficiency gains
  - 15-30%: Profitable, can invest in growth
  - Above 30%: Strong unit economics

**Contribution Margin II (CM2)**:
- **Definition**: CM1 minus variable overhead (packaging, pick/pack, support)
- **Formula**: CM1 - Variable Overhead
- **Healthy Range**: 15-35%
- **Use**: True per-order profitability after all variable costs

**Operating Margin**:
- **Definition**: Profit after all operating expenses
- **Formula**: (Revenue - COGS - Marketing - Operating Expenses) / Revenue × 100
- **Healthy Range**: 10-25%
- **Components**: Salaries, rent, software, admin costs

**Net Profit Margin**:
- **Definition**: Bottom-line profitability
- **Formula**: Net Profit / Revenue × 100
- **Healthy Ranges**:
  - Startup (0-2 years): -20% to 0% (investment phase)
  - Growth (2-5 years): 5-15%
  - Mature (5+ years): 15-25%
- **Benchmark**: 10%+ is profitable, 20%+ is excellent

## Unit Economics Analysis

### Customer Acquisition Cost (CAC)

**Full CAC Calculation**:
```
CAC = (Total Marketing Spend + Sales Team Costs + Marketing Tools) / New Customers Acquired
```

**Channel-Specific CAC**:
| Channel | Typical CAC | Good CAC | Excellent CAC |
|---------|------------|----------|---------------|
| Meta Ads | $35-55 | $25-35 | <$25 |
| Google Ads | $40-65 | $30-40 | <$30 |
| TikTok Ads | $25-45 | $18-25 | <$18 |
| Email Marketing | $3-8 | $1-3 | <$1 |
| Influencer | $50-100 | $30-50 | <$30 |
| Organic Social | $10-25 | $5-10 | <$5 |
| SEO/Content | $8-20 | $4-8 | <$4 |

**CAC Payback Period**:
- **Definition**: Time to recover customer acquisition cost
- **Formula**: CAC / (AOV × Gross Margin × Purchase Frequency per Month)
- **Healthy Ranges**:
  - Under 6 months: Excellent
  - 6-12 months: Good
  - 12-18 months: Acceptable
  - Over 18 months: Risky

### LTV:CAC Ratio

**Calculation**:
```
LTV:CAC = Customer Lifetime Value / Customer Acquisition Cost
```

**Benchmarks by Stage**:
| Business Stage | Minimum | Healthy | Excellent |
|----------------|---------|---------|-----------|
| Startup (0-2 years) | 2:1 | 3:1 | 4:1+ |
| Growth (2-5 years) | 3:1 | 4:1 | 5:1+ |
| Scaling (5+ years) | 4:1 | 5:1 | 6:1+ |

**Interpretation**:
- **Below 1:1**: Losing money on every customer (unsustainable)
- **1:1 to 2:1**: Break-even to barely profitable (risky)
- **2:1 to 3:1**: Minimum viable (can grow cautiously)
- **3:1 to 5:1**: Healthy (can invest in growth)
- **Above 5:1**: Excellent (scale aggressively)

**Warning**: Very high ratios (>10:1) may indicate underinvestment in growth

### Return on Ad Spend (ROAS)

**Definition**: Revenue generated per dollar spent on advertising
**Formula**: Revenue from Ads / Ad Spend

**Benchmarks**:
| ROAS | Interpretation | Action |
|------|----------------|--------|
| <1.0x | Losing money | Stop/optimize immediately |
| 1.0-2.0x | Break-even to slight profit | Optimize before scaling |
| 2.0-3.0x | Profitable | Good to scale cautiously |
| 3.0-5.0x | Strong performance | Scale aggressively |
| >5.0x | Exceptional | Scale, expand channels |

**ROAS Requirements by Margin**:
| Gross Margin | Min Break-even ROAS | Target ROAS |
|--------------|-------------------|-------------|
| 30% | 3.3x | 4.5x+ |
| 40% | 2.5x | 3.5x+ |
| 50% | 2.0x | 3.0x+ |
| 60% | 1.7x | 2.5x+ |
| 70% | 1.4x | 2.0x+ |

## Cost Structure Breakdown

### Typical E-commerce Cost Stack

**For $100 in Revenue**:
```
Revenue: $100.00
├─ COGS: -$45.00 (45%)
├─ Gross Profit: $55.00

Variable Costs:
├─ Marketing/CAC: -$20.00 (20%)
├─ Shipping: -$5.00 (5%)
├─ Payment Processing: -$3.00 (3%)
├─ Packaging: -$2.00 (2%)
├─ Pick/Pack/Fulfillment: -$3.00 (3%)
├─ Contribution Margin: $22.00 (22%)

Fixed Costs:
├─ Salaries: -$8.00 (8%)
├─ Software/Tools: -$2.00 (2%)
├─ Rent/Warehouse: -$2.00 (2%)
├─ Other Overhead: -$3.00 (3%)
├─ Operating Profit: $7.00 (7%)

Other:
├─ Taxes: -$2.00 (2%)
└─ Net Profit: $5.00 (5%)
```

### Cost Optimization Targets

**COGS Reduction**:
- Negotiate with suppliers (>$10K/month orders)
- Increase order quantities (10-20% discount for 2x volume)
- Source direct from manufacturers (eliminate middlemen)
- Expected improvement: 5-15% reduction

**Shipping Optimization**:
- Negotiate carrier rates (>500 shipments/month)
- Multi-carrier strategy (USPS, UPS, FedEx)
- Dimensional weight optimization (smaller boxes)
- Expected improvement: 10-25% reduction

**Marketing Efficiency**:
- Improve targeting (reduce wasted spend)
- Creative optimization (higher CTR/conversion)
- Retention focus (lower CAC than acquisition)
- Expected improvement: 15-30% better ROAS

## Financial Health Indicators

### Cash Conversion Cycle

**Definition**: Time between paying suppliers and receiving customer payments
**Formula**: Days Inventory Outstanding + Days Sales Outstanding - Days Payable Outstanding

**Components**:
- **Days Inventory Outstanding**: How long inventory sits
  - Formula: (Inventory / COGS) × 365
  - Target: 30-60 days

- **Days Sales Outstanding**: How long to collect payment
  - Formula: (Accounts Receivable / Revenue) × 365
  - E-commerce: 0-2 days (immediate payment)

- **Days Payable Outstanding**: How long you take to pay suppliers
  - Formula: (Accounts Payable / COGS) × 365
  - Target: 30-60 days (negotiate terms)

**Healthy Cash Cycle**:
- Negative cycle (best): Get paid before paying suppliers
- 0-30 days: Excellent
- 30-60 days: Good
- 60-90 days: Manageable
- >90 days: Cash flow risk

### Inventory Turnover

**Definition**: How many times inventory is sold and replaced per year
**Formula**: COGS / Average Inventory Value

**Benchmarks**:
| Category | Healthy Turnover | Days to Sell |
|----------|------------------|--------------|
| Fashion | 4-6x/year | 60-90 days |
| Beauty | 6-8x/year | 45-60 days |
| Food | 12-20x/year | 18-30 days |
| Electronics | 5-7x/year | 50-70 days |
| Home | 3-5x/year | 70-120 days |

**Interpretation**:
- Low turnover (<2x): Excess inventory, cash tied up, risk of obsolescence
- Healthy turnover (4-8x): Good balance, fresh inventory
- High turnover (>10x): May indicate stockouts, lost sales

### Break-Even Analysis

**Fixed Costs Break-Even**:
```
Break-Even Revenue = Fixed Costs / Contribution Margin %
```

**Example**:
- Fixed Costs: $20,000/month
- Contribution Margin: 25%
- Break-Even: $20,000 / 0.25 = $80,000/month

**Full Break-Even (including growth investment)**:
```
Break-Even = (Fixed Costs + Growth Investment) / Contribution Margin %
```

## Pricing Strategy

### Cost-Plus Pricing

**Formula**: Price = COGS × Markup Multiple

**Markup Multiples by Category**:
| Category | Typical Markup | Healthy | Premium |
|----------|---------------|---------|---------|
| Fashion | 2.0-2.5x | 2.5-3.5x | 3.5x+ |
| Beauty | 2.5-3.0x | 3.0-4.0x | 4.0x+ |
| Home | 2.0-2.5x | 2.5-3.0x | 3.0x+ |
| Food | 1.5-2.0x | 2.0-2.5x | 2.5x+ |
| Electronics | 1.3-1.7x | 1.7-2.2x | 2.2x+ |

**Example**:
- COGS: $20
- Target Markup: 3x
- Retail Price: $60
- Gross Margin: 67%

### Value-Based Pricing

**Formula**: Price = Perceived Value (not cost-based)

**Factors**:
- Brand positioning
- Competitor pricing
- Customer willingness to pay
- Unique features/benefits

**Testing**: A/B test price points (e.g., $49 vs $59 vs $69)

### Psychological Pricing

**Charm Pricing**: $49.99 vs $50.00 (2-3% higher conversion)
**Prestige Pricing**: $100 vs $99.99 (round numbers for luxury)
**Anchor Pricing**: Show compare-at price ($120 $89.99)

## Monthly Financial Review Checklist

1. **Revenue Metrics**:
   - [ ] Month-over-month revenue growth
   - [ ] Year-over-year revenue growth
   - [ ] AOV trend

2. **Profitability**:
   - [ ] Gross margin %
   - [ ] Contribution margin %
   - [ ] Net profit margin %

3. **Unit Economics**:
   - [ ] CAC by channel
   - [ ] LTV:CAC ratio
   - [ ] CAC payback period

4. **Efficiency**:
   - [ ] ROAS by channel
   - [ ] Inventory turnover
   - [ ] Cash conversion cycle

5. **Health Indicators**:
   - [ ] Cash runway (months)
   - [ ] Customer retention rate
   - [ ] Repeat purchase rate

## Red Flags & Warning Signs

**Immediate Action Required**:
- Negative contribution margin (losing money per order)
- LTV:CAC ratio below 2:1
- Cash runway under 3 months
- Inventory turnover under 2x/year
- CAC increasing >30% MoM

**Monitor Closely**:
- Gross margin declining
- AOV declining
- CAC payback period >12 months
- Return rate >15%
- Customer retention declining

## Sources & Attribution

- **Stripe Atlas Guides**: https://stripe.com/atlas/guides (Updated: 2024)
- **a16z Marketplace KPIs**: https://a16z.com/marketplace-100/ (Updated: 2024)
- **ProfitWell Benchmarks**: SaaS/subscription metrics (Updated: 2024)
- **First Round Review**: Financial metrics for startups (Updated: 2024)
- **Wall Street Prep**: Financial modeling guides (Updated: 2024)

**Note**: Financial benchmarks vary significantly by business model, stage, and category. Use as directional guidance and always compare to historical performance.
