"""
Query Splitter for Comparison Queries

Splits comparison queries into independent sub-queries that can be executed in parallel.

Example:
    Query: "Compare January vs February engagement"
    →
    Sub-query 1: "January engagement"
    Sub-query 2: "February engagement"

Both queries execute in parallel, results merged afterward.

Usage:
    from utils.query_splitter import split_comparison_query

    result = split_comparison_query(
        original_query="Compare Jan vs Feb engagement",
        comparison_data={...}  # from semantic_layer.detect_comparison_query
    )

    for sub_query in result['sub_queries']:
        # Execute each query in parallel
        ...
"""

import re
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def split_comparison_query(
    original_query: str,
    comparison_data: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Split a comparison query into independent sub-queries for parallel execution.

    Args:
        original_query: Original user query
        comparison_data: Comparison detection result from semantic_layer.detect_comparison_query()
        user_id: User ID for all queries

    Returns:
        Dictionary with:
        - can_split: bool (True if query can be split)
        - sub_queries: list[dict] (each with 'query', 'label', 'filters')
        - merge_strategy: str (how to merge results: "side_by_side", "delta", "percentage")
        - comparison_type: str (from comparison_data)
        - error: str (if can't split)

    Example:
        >>> split_comparison_query(
        ...     "Compare Jan vs Feb engagement",
        ...     {'is_comparison': True, 'comparison_type': 'time_period', ...},
        ...     "user123"
        ... )
        {
            'can_split': True,
            'sub_queries': [
                {'query': 'January engagement', 'label': 'January', 'filters': {...}},
                {'query': 'February engagement', 'label': 'February', 'filters': {...}}
            ],
            'merge_strategy': 'side_by_side',
            ...
        }
    """
    if not comparison_data.get('is_comparison'):
        return {
            'can_split': False,
            'sub_queries': [],
            'merge_strategy': None,
            'error': 'Query is not a comparison query'
        }

    comparison_type = comparison_data['comparison_type']
    comparison_items = comparison_data['comparison_items']
    comparison_dimension = comparison_data['comparison_dimension']

    if len(comparison_items) < 2:
        return {
            'can_split': False,
            'sub_queries': [],
            'merge_strategy': None,
            'error': f'Not enough comparison items detected (found {len(comparison_items)})'
        }

    # ========== Split Based on Comparison Type ==========

    if comparison_type == 'time_period':
        return _split_time_period_comparison(
            original_query, comparison_items, comparison_dimension, user_id
        )

    elif comparison_type == 'content_type':
        return _split_content_type_comparison(
            original_query, comparison_items, comparison_dimension, user_id
        )

    elif comparison_type == 'campaign':
        return _split_campaign_comparison(
            original_query, comparison_items, comparison_dimension, user_id
        )

    elif comparison_type == 'generic':
        # Generic comparison - create basic split
        return _split_generic_comparison(
            original_query, comparison_items, comparison_dimension, user_id
        )

    else:
        return {
            'can_split': False,
            'sub_queries': [],
            'merge_strategy': None,
            'error': f'Unknown comparison type: {comparison_type}'
        }


def _split_time_period_comparison(
    original_query: str,
    comparison_items: List[str],
    dimension: str,
    user_id: str
) -> Dict[str, Any]:
    """Split time period comparisons (e.g., Jan vs Feb, 2024 vs 2023)."""

    sub_queries = []

    for time_period in comparison_items:
        # Create query for this time period
        # Remove comparison keywords from original query
        clean_query = original_query
        for keyword in ['compare', 'vs', 'versus', 'compared to', 'compared with']:
            clean_query = re.sub(rf'\b{keyword}\b', '', clean_query, flags=re.IGNORECASE)

        # Remove both time periods, then add back just this one
        for item in comparison_items:
            clean_query = re.sub(rf'\b{item}\b', '', clean_query, flags=re.IGNORECASE)

        clean_query = clean_query.strip()

        # Add this specific time period
        sub_query_text = f"{time_period} {clean_query}"

        # Parse time period to date filters
        date_filters = _parse_time_period(time_period)

        sub_queries.append({
            'query': sub_query_text.strip(),
            'label': time_period.title(),
            'filters': {
                'user_id': user_id,
                'time_period': time_period,
                **date_filters
            },
            'original_comparison_item': time_period
        })

    return {
        'can_split': True,
        'sub_queries': sub_queries,
        'merge_strategy': 'side_by_side',
        'comparison_type': 'time_period',
        'comparison_dimension': dimension
    }


def _split_content_type_comparison(
    original_query: str,
    comparison_items: List[str],
    dimension: str,
    user_id: str
) -> Dict[str, Any]:
    """Split content type comparisons (e.g., Reels vs Posts)."""

    sub_queries = []

    for content_type in comparison_items:
        # Create query for this content type
        clean_query = original_query
        for keyword in ['compare', 'vs', 'versus', 'compared to']:
            clean_query = re.sub(rf'\b{keyword}\b', '', clean_query, flags=re.IGNORECASE)

        # Remove both content types, then add back just this one
        for item in comparison_items:
            clean_query = re.sub(rf'\b{item}\b', '', clean_query, flags=re.IGNORECASE)

        clean_query = clean_query.strip()

        # Add this specific content type
        sub_query_text = f"{content_type} {clean_query}"

        sub_queries.append({
            'query': sub_query_text.strip(),
            'label': content_type.title(),
            'filters': {
                'user_id': user_id,
                'media_type': content_type.lower()
            },
            'original_comparison_item': content_type
        })

    return {
        'can_split': True,
        'sub_queries': sub_queries,
        'merge_strategy': 'side_by_side',
        'comparison_type': 'content_type',
        'comparison_dimension': dimension
    }


def _split_campaign_comparison(
    original_query: str,
    comparison_items: List[str],
    dimension: str,
    user_id: str
) -> Dict[str, Any]:
    """Split campaign/ad set comparisons."""

    sub_queries = []

    for campaign in comparison_items:
        clean_query = original_query
        for keyword in ['compare', 'vs', 'versus', 'campaign', 'ad set']:
            clean_query = re.sub(rf'\b{keyword}\b', '', clean_query, flags=re.IGNORECASE)

        for item in comparison_items:
            clean_query = re.sub(rf'\b{item}\b', '', clean_query, flags=re.IGNORECASE)

        clean_query = clean_query.strip()

        sub_query_text = f"Campaign {campaign} {clean_query}"

        sub_queries.append({
            'query': sub_query_text.strip(),
            'label': f"Campaign {campaign}",
            'filters': {
                'user_id': user_id,
                'campaign_name': campaign
            },
            'original_comparison_item': campaign
        })

    return {
        'can_split': True,
        'sub_queries': sub_queries,
        'merge_strategy': 'side_by_side',
        'comparison_type': 'campaign',
        'comparison_dimension': dimension
    }


def _split_generic_comparison(
    original_query: str,
    comparison_items: List[str],
    dimension: str,
    user_id: str
) -> Dict[str, Any]:
    """Split generic comparisons when specific type not detected."""

    sub_queries = []

    for item in comparison_items:
        clean_query = original_query
        for keyword in ['compare', 'vs', 'versus', 'compared to']:
            clean_query = re.sub(rf'\b{keyword}\b', '', clean_query, flags=re.IGNORECASE)

        for comp_item in comparison_items:
            clean_query = re.sub(rf'\b{comp_item}\b', '', clean_query, flags=re.IGNORECASE)

        clean_query = clean_query.strip()

        sub_query_text = f"{item} {clean_query}"

        sub_queries.append({
            'query': sub_query_text.strip(),
            'label': item.title(),
            'filters': {
                'user_id': user_id
            },
            'original_comparison_item': item
        })

    return {
        'can_split': True,
        'sub_queries': sub_queries,
        'merge_strategy': 'side_by_side',
        'comparison_type': 'generic',
        'comparison_dimension': dimension
    }


def _parse_time_period(time_period_str: str) -> Dict[str, Any]:
    """
    Parse a time period string into date filter parameters.

    Args:
        time_period_str: Time period like "january", "last week", "2024", "last 30 days"

    Returns:
        Dictionary with date filter parameters (start_date, end_date, days, etc.)

    Example:
        >>> _parse_time_period("january")
        {'month': 1, 'start_date': '2025-01-01', 'end_date': '2025-01-31'}
    """
    time_lower = time_period_str.lower().strip()

    # Month names
    MONTHS = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    # Check for specific month
    for month_name, month_num in MONTHS.items():
        if month_name in time_lower:
            # Use current year by default
            year = datetime.now().year
            # Calculate start and end dates for the month
            from calendar import monthrange
            _, last_day = monthrange(year, month_num)

            return {
                'month': month_num,
                'year': year,
                'start_date': f"{year}-{month_num:02d}-01",
                'end_date': f"{year}-{month_num:02d}-{last_day:02d}",
                'days': last_day
            }

    # Check for year
    year_match = re.search(r'\b(20\d{2})\b', time_lower)
    if year_match:
        year = int(year_match.group(1))
        return {
            'year': year,
            'start_date': f"{year}-01-01",
            'end_date': f"{year}-12-31",
            'days': 365
        }

    # Check for relative periods
    if 'last week' in time_lower or 'previous week' in time_lower:
        return {'days': 7, 'offset': 7}  # Last 7 days, offset by 7 days

    if 'this week' in time_lower:
        return {'days': 7, 'offset': 0}

    if 'last month' in time_lower or 'previous month' in time_lower:
        return {'days': 30, 'offset': 30}

    if 'this month' in time_lower:
        return {'days': 30, 'offset': 0}

    # Check for "last N days"
    days_match = re.search(r'(?:last|previous)\s+(\d+)\s+days?', time_lower)
    if days_match:
        days = int(days_match.group(1))
        return {'days': days, 'offset': days}

    # Default: use as a general filter hint
    return {'period_hint': time_period_str}
