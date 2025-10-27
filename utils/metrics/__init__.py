"""
Metric calculation system for e-commerce analytics.

Provides dual-mode metric definitions that work in both:
- Python (for testing, validation, non-SQL contexts)
- SQL (for database queries)

Usage:
    from utils.metrics import calculate_metric, get_sql_expression

    # Calculate in Python
    value = calculate_metric('engagement_rate',
                            likes=100, comments=20, saved=15, shares=5, reach=1000)
    # Returns: 14.0

    # Generate SQL expression
    sql = get_sql_expression('engagement_rate', table_alias='i')
    # Returns: "((i.likes + i.comments + i.saved + i.shares) / NULLIF(i.reach, 0)) * 100"
"""

from typing import Optional, Dict, List
from .base import MetricDefinition, SQLBuilder
from .social_media import EngagementRate, Frequency, ReachRate, SaveRate
from .ecommerce import ConversionRate, CartAbandonmentRate, AverageOrderValue
from .advertising import ROAS, CAC

# ========== Metric Registry ==========

# Instantiate all metric definitions
_METRICS = {
    'engagement_rate': EngagementRate(),
    'frequency': Frequency(),
    'reach_rate': ReachRate(),
    'save_rate': SaveRate(),
    'conversion_rate': ConversionRate(),
    'cart_abandonment_rate': CartAbandonmentRate(),
    'average_order_value': AverageOrderValue(),
    'roas': ROAS(),
    'customer_acquisition_cost': CAC(),
}


# ========== Public API ==========

def get_metric(metric_name: str) -> Optional[MetricDefinition]:
    """
    Get metric definition by name.

    Args:
        metric_name: Name of metric (e.g., 'engagement_rate')

    Returns:
        MetricDefinition instance or None if not found

    Example:
        metric = get_metric('engagement_rate')
        if metric:
            value = metric.calculate(likes=100, ...)
    """
    return _METRICS.get(metric_name)


def calculate_metric(metric_name: str, **data) -> Optional[float]:
    """
    Calculate metric value in Python.

    Args:
        metric_name: Name of metric (e.g., 'engagement_rate')
        **data: Field values for calculation (e.g., likes=100, reach=1000)

    Returns:
        Calculated metric value or None if metric not found

    Raises:
        ValueError: If metric doesn't exist

    Example:
        value = calculate_metric('engagement_rate',
                                likes=100, comments=20, saved=15,
                                shares=5, reach=1000)
        # Returns: 14.0
    """
    metric = get_metric(metric_name)
    if not metric:
        raise ValueError(f"Unknown metric: '{metric_name}'. Available metrics: {list_metrics()}")

    return metric.safe_calculate(**data)


def get_sql_expression(metric_name: str, table_alias: str = '', **overrides) -> Optional[str]:
    """
    Get SQL expression for metric.

    Args:
        metric_name: Name of metric (e.g., 'engagement_rate')
        table_alias: Table alias for column references (e.g., 'i')
        **overrides: Override specific field references (e.g., reach='m.total_reach')

    Returns:
        SQL expression string or None if metric not found

    Raises:
        ValueError: If metric doesn't exist

    Example:
        # Standard usage
        sql = get_sql_expression('engagement_rate', 'i')
        # Returns: "((i.likes + i.comments + ...) / NULLIF(i.reach, 0)) * 100"

        # With overrides
        sql = get_sql_expression('engagement_rate', 'i', reach='m.reach_total')
        # Returns: "((i.likes + i.comments + ...) / NULLIF(m.reach_total, 0)) * 100"
    """
    metric = get_metric(metric_name)
    if not metric:
        raise ValueError(f"Unknown metric: '{metric_name}'. Available metrics: {list_metrics()}")

    return metric.to_sql(table_alias, **overrides)


def list_metrics() -> List[str]:
    """
    Get list of all available metric names.

    Returns:
        List of metric names

    Example:
        metrics = list_metrics()
        # Returns: ['engagement_rate', 'frequency', 'reach_rate', ...]
    """
    return list(_METRICS.keys())


def list_metrics_by_category(category: str) -> List[str]:
    """
    Get list of metrics in a specific category.

    Args:
        category: Category name (social_media, ecommerce, advertising)

    Returns:
        List of metric names in that category

    Example:
        social_metrics = list_metrics_by_category('social_media')
        # Returns: ['engagement_rate', 'frequency', 'reach_rate', 'save_rate']
    """
    return [
        name for name, metric in _METRICS.items()
        if metric.category == category
    ]


def get_metric_info(metric_name: str) -> Optional[Dict[str, str]]:
    """
    Get metadata about a metric.

    Args:
        metric_name: Name of metric

    Returns:
        Dict with name, category, data_type, required_fields

    Example:
        info = get_metric_info('engagement_rate')
        # Returns: {
        #     'name': 'Engagement Rate',
        #     'category': 'social_media',
        #     'data_type': 'percentage',
        #     'required_fields': ['likes', 'comments', 'saved', 'shares', 'reach']
        # }
    """
    metric = get_metric(metric_name)
    if not metric:
        return None

    return {
        'name': metric.name,
        'category': metric.category,
        'data_type': metric.data_type,
        'required_fields': metric.required_fields,
    }


# ========== Exports ==========

__all__ = [
    # Base classes
    'MetricDefinition',
    'SQLBuilder',

    # Metric classes
    'EngagementRate',
    'Frequency',
    'ReachRate',
    'SaveRate',
    'ConversionRate',
    'CartAbandonmentRate',
    'AverageOrderValue',
    'ROAS',
    'CAC',

    # Public API functions
    'get_metric',
    'calculate_metric',
    'get_sql_expression',
    'list_metrics',
    'list_metrics_by_category',
    'get_metric_info',
]
