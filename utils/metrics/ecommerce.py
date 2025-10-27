"""
E-commerce metric definitions.

Implements metrics for e-commerce performance analysis:
- Conversion Rate
- Cart Abandonment Rate
- Average Order Value (AOV)
"""

from .base import MetricDefinition, SQLBuilder


class ConversionRate(MetricDefinition):
    """
    Conversion Rate = orders / sessions * 100

    Measures percentage of website visitors who made a purchase.
    """

    name = "Conversion Rate"
    category = "ecommerce"
    data_type = "percentage"
    required_fields = ["orders", "sessions"]

    def calculate(self, orders: float, sessions: float) -> float:
        """
        Calculate conversion rate in Python.

        Args:
            orders: Number of completed orders
            sessions: Number of website sessions/visits

        Returns:
            Conversion rate as percentage
        """
        if sessions == 0:
            return 0.0
        return (orders / sessions) * 100

    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for conversion rate.

        Args:
            table_alias: Table alias (default: empty for simple queries)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql() → "(CAST(orders AS DOUBLE) / NULLIF(sessions, 0)) * 100"
        """
        f = SQLBuilder.field
        orders = overrides.get('orders', f(table_alias, 'orders'))
        sessions = overrides.get('sessions', f(table_alias, 'sessions'))
        return f"({SQLBuilder.safe_divide(orders, sessions)}) * 100"


class CartAbandonmentRate(MetricDefinition):
    """
    Cart Abandonment Rate = (carts_created - orders) / carts_created * 100

    Measures percentage of shoppers who added to cart but didn't purchase.
    """

    name = "Cart Abandonment Rate"
    category = "ecommerce"
    data_type = "percentage"
    required_fields = ["carts_created", "orders"]

    def calculate(self, carts_created: float, orders: float) -> float:
        """
        Calculate cart abandonment rate in Python.

        Args:
            carts_created: Number of shopping carts created
            orders: Number of completed orders

        Returns:
            Cart abandonment rate as percentage
        """
        if carts_created == 0:
            return 0.0
        abandoned_carts = carts_created - orders
        return (abandoned_carts / carts_created) * 100

    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for cart abandonment rate.

        Args:
            table_alias: Table alias (default: empty)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql() → "((carts_created - orders) / NULLIF(CAST(carts_created AS DOUBLE), 0)) * 100"
        """
        f = SQLBuilder.field
        carts = overrides.get('carts_created', f(table_alias, 'carts_created'))
        orders = overrides.get('orders', f(table_alias, 'orders'))

        numerator = f"({carts} - {orders})"
        return f"({SQLBuilder.safe_divide(numerator, carts)}) * 100"


class AverageOrderValue(MetricDefinition):
    """
    Average Order Value (AOV) = total_revenue / orders

    Measures average amount customers spend per order.
    """

    name = "Average Order Value (AOV)"
    category = "ecommerce"
    data_type = "currency"
    required_fields = ["total_revenue", "orders"]

    def calculate(self, total_revenue: float, orders: float) -> float:
        """
        Calculate average order value in Python.

        Args:
            total_revenue: Total revenue amount
            orders: Number of completed orders

        Returns:
            Average order value in currency units
        """
        if orders == 0:
            return 0.0
        return total_revenue / orders

    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for AOV.

        Args:
            table_alias: Table alias (default: empty)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql() → "CAST(total_revenue AS DOUBLE) / NULLIF(orders, 0)"
        """
        f = SQLBuilder.field
        revenue = overrides.get('total_revenue', f(table_alias, 'total_revenue'))
        orders = overrides.get('orders', f(table_alias, 'orders'))
        return SQLBuilder.safe_divide(revenue, orders)
