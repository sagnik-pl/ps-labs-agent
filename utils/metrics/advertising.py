"""
Advertising metric definitions.

Implements metrics for advertising performance analysis:
- Return on Ad Spend (ROAS)
- Customer Acquisition Cost (CAC)
"""

from .base import MetricDefinition, SQLBuilder


class ROAS(MetricDefinition):
    """
    Return on Ad Spend (ROAS) = revenue_from_ads / ad_spend

    Measures revenue generated for every dollar spent on advertising.
    """

    name = "Return on Ad Spend (ROAS)"
    category = "advertising"
    data_type = "ratio"
    required_fields = ["revenue_from_ads", "ad_spend"]

    def calculate(self, revenue_from_ads: float, ad_spend: float) -> float:
        """
        Calculate ROAS in Python.

        Args:
            revenue_from_ads: Revenue attributed to ads
            ad_spend: Total advertising spend

        Returns:
            ROAS ratio (e.g., 3.0 means $3 revenue per $1 spend)
        """
        if ad_spend == 0:
            return 0.0
        return revenue_from_ads / ad_spend

    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for ROAS.

        Args:
            table_alias: Table alias (default: empty)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql() → "CAST(revenue_from_ads AS DOUBLE) / NULLIF(ad_spend, 0)"
        """
        f = SQLBuilder.field
        revenue = overrides.get('revenue_from_ads', f(table_alias, 'revenue_from_ads'))
        spend = overrides.get('ad_spend', f(table_alias, 'ad_spend'))
        return SQLBuilder.safe_divide(revenue, spend)


class CAC(MetricDefinition):
    """
    Customer Acquisition Cost (CAC) = total_marketing_spend / new_customers

    Measures cost to acquire one new customer.
    """

    name = "Customer Acquisition Cost (CAC)"
    category = "advertising"
    data_type = "currency"
    required_fields = ["total_marketing_spend", "new_customers"]

    def calculate(self, total_marketing_spend: float, new_customers: float) -> float:
        """
        Calculate CAC in Python.

        Args:
            total_marketing_spend: Total marketing expenditure
            new_customers: Number of new customers acquired

        Returns:
            CAC in currency units (cost per customer)
        """
        if new_customers == 0:
            return 0.0
        return total_marketing_spend / new_customers

    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for CAC.

        Args:
            table_alias: Table alias (default: empty)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql() → "CAST(total_marketing_spend AS DOUBLE) / NULLIF(new_customers, 0)"
        """
        f = SQLBuilder.field
        spend = overrides.get('total_marketing_spend', f(table_alias, 'total_marketing_spend'))
        customers = overrides.get('new_customers', f(table_alias, 'new_customers'))
        return SQLBuilder.safe_divide(spend, customers)
