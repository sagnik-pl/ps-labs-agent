"""
Base classes and utilities for metric definitions.

Provides abstract base class for metrics that can be calculated in both:
- Python (for testing, validation, non-SQL contexts)
- SQL (for database queries)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class MetricDefinition(ABC):
    """
    Abstract base class for all metric definitions.

    Each metric must implement:
    1. calculate() - Python implementation for testing/validation
    2. to_sql() - SQL expression generation for database queries

    Example:
        class EngagementRate(MetricDefinition):
            def calculate(self, likes, comments, saved, shares, reach):
                if reach == 0:
                    return 0.0
                return ((likes + comments + saved + shares) / reach) * 100

            def to_sql(self, table_alias='i'):
                return "((i.likes + i.comments + ...) / NULLIF(i.reach, 0)) * 100"
    """

    # Metric metadata (override in subclasses)
    name: str = ""
    category: str = ""  # social_media, ecommerce, advertising
    data_type: str = ""  # percentage, ratio, currency
    required_fields: List[str] = []

    @abstractmethod
    def calculate(self, **kwargs) -> float:
        """
        Calculate metric in Python (for testing/validation).

        Args:
            **kwargs: Named arguments for metric fields (e.g., likes, reach)

        Returns:
            Calculated metric value

        Raises:
            ValueError: If required fields are missing
        """
        pass

    @abstractmethod
    def to_sql(self, table_alias: str = '', **overrides) -> str:
        """
        Generate SQL expression for this metric.

        Args:
            table_alias: Table alias to prepend to column names (e.g., 'i' for 'i.likes')
            **overrides: Override field references (e.g., reach='m.total_reach')

        Returns:
            SQL expression string

        Example:
            to_sql('i') → "((i.likes + i.comments) / NULLIF(i.reach, 0)) * 100"
            to_sql('insights') → "((insights.likes + ...) / NULLIF(insights.reach, 0)) * 100"
        """
        pass

    def validate_inputs(self, **kwargs) -> bool:
        """
        Validate that all required fields are present.

        Args:
            **kwargs: Fields to validate

        Returns:
            True if all required fields present, False otherwise
        """
        return all(field in kwargs for field in self.required_fields)

    def safe_calculate(self, **kwargs) -> Optional[float]:
        """
        Calculate metric with validation and error handling.

        Args:
            **kwargs: Metric field values

        Returns:
            Calculated value or None if calculation fails
        """
        if not self.validate_inputs(**kwargs):
            missing = set(self.required_fields) - set(kwargs.keys())
            print(f"Warning: Missing required fields for {self.name}: {missing}")
            return None

        try:
            return self.calculate(**kwargs)
        except Exception as e:
            print(f"Error calculating {self.name}: {e}")
            return None


class SQLBuilder:
    """
    Helper utilities for building safe SQL expressions.

    Handles common SQL patterns like:
    - Division with zero protection (NULLIF)
    - Type casting
    - Table aliasing
    """

    @staticmethod
    def safe_divide(numerator: str, denominator: str, cast_type: str = 'DOUBLE') -> str:
        """
        Generate division expression with zero protection.

        Args:
            numerator: SQL expression for numerator
            denominator: SQL expression for denominator
            cast_type: Type to cast denominator to (default: DOUBLE)

        Returns:
            SQL division expression with NULLIF protection

        Example:
            safe_divide("sales", "visits") → "(sales / NULLIF(CAST(visits AS DOUBLE), 0))"
        """
        return f"({numerator} / NULLIF(CAST({denominator} AS {cast_type}), 0))"

    @staticmethod
    def field(table_alias: str, column: str) -> str:
        """
        Generate table.column reference.

        Args:
            table_alias: Table alias (empty string for no alias)
            column: Column name

        Returns:
            Qualified column reference

        Example:
            field('i', 'likes') → "i.likes"
            field('', 'likes') → "likes"
        """
        return f"{table_alias}.{column}" if table_alias else column

    @staticmethod
    def cast(expression: str, cast_type: str = 'DOUBLE') -> str:
        """
        Generate CAST expression.

        Args:
            expression: SQL expression to cast
            cast_type: Target type (default: DOUBLE)

        Returns:
            CAST expression

        Example:
            cast("revenue", "DOUBLE") → "CAST(revenue AS DOUBLE)"
        """
        return f"CAST({expression} AS {cast_type})"

    @staticmethod
    def sum_fields(table_alias: str, *fields: str) -> str:
        """
        Generate sum of multiple fields.

        Args:
            table_alias: Table alias
            *fields: Field names to sum

        Returns:
            Sum expression

        Example:
            sum_fields('i', 'likes', 'comments', 'shares')
            → "(i.likes + i.comments + i.shares)"
        """
        qualified_fields = [SQLBuilder.field(table_alias, f) for f in fields]
        return f"({' + '.join(qualified_fields)})"
