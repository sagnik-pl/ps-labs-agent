"""
SQL Query Analysis Utilities

Provides complexity scoring and optimization suggestions for SQL queries.
Helps identify potentially slow queries and suggest improvements.

Usage:
    from utils.sql_analyzer import calculate_complexity, get_optimization_hints

    complexity = calculate_complexity(sql_query)
    hints = get_optimization_hints(sql_query, complexity)
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_complexity(sql_query: str) -> Dict[str, any]:
    """
    Calculate SQL query complexity on a 1-10 scale.

    Complexity factors:
    - Number of JOINs (+2 points each)
    - Subqueries (+3 points each)
    - Aggregations (+1 point each)
    - DISTINCT (+1 point)
    - UNION/INTERSECT/EXCEPT (+2 points each)
    - Window functions (+2 points each)
    - GROUP BY with multiple columns (+1 point)
    - ORDER BY (+0.5 points)
    - Large IN clauses (>5 items) (+1 point)

    Args:
        sql_query: SQL query string to analyze

    Returns:
        Dictionary with:
        - score: Complexity score (1-10)
        - level: "low", "medium", or "high"
        - factors: List of complexity contributors
        - warnings: List of potential performance issues

    Example:
        >>> sql = "SELECT * FROM users WHERE user_id = 'abc123'"
        >>> result = calculate_complexity(sql)
        >>> result['level']
        'low'
    """
    query_lower = sql_query.lower()
    score = 1.0  # Base score
    factors = []
    warnings = []

    # Count JOINs (all types)
    join_patterns = [
        r'\bjoin\b',
        r'\binner join\b',
        r'\bleft join\b',
        r'\bright join\b',
        r'\bfull outer join\b',
        r'\bcross join\b'
    ]
    join_count = sum(len(re.findall(pattern, query_lower)) for pattern in join_patterns)
    if join_count > 0:
        join_score = join_count * 2
        score += join_score
        factors.append(f"{join_count} JOIN{'s' if join_count > 1 else ''} (+{join_score})")

        if join_count > 3:
            warnings.append(f"High number of JOINs ({join_count}) may impact performance")

    # Count subqueries
    subquery_count = query_lower.count('select') - 1  # Subtract main SELECT
    if subquery_count > 0:
        subquery_score = subquery_count * 3
        score += subquery_score
        factors.append(f"{subquery_count} subquer{'ies' if subquery_count > 1 else 'y'} (+{subquery_score})")

        if subquery_count > 2:
            warnings.append(f"Multiple subqueries ({subquery_count}) - consider CTEs or JOIN optimization")

    # Count aggregations
    agg_functions = ['count(', 'sum(', 'avg(', 'min(', 'max(', 'stddev(', 'variance(']
    agg_count = sum(query_lower.count(func) for func in agg_functions)
    if agg_count > 0:
        score += agg_count
        factors.append(f"{agg_count} aggregation{'s' if agg_count > 1 else ''} (+{agg_count})")

    # Check for DISTINCT
    if 'distinct' in query_lower:
        score += 1
        factors.append("DISTINCT (+1)")
        warnings.append("DISTINCT can be expensive - ensure it's necessary")

    # Check for set operations
    set_ops = ['union', 'intersect', 'except']
    for op in set_ops:
        if op in query_lower:
            score += 2
            factors.append(f"{op.upper()} (+2)")

    # Check for window functions
    window_functions = ['row_number(', 'rank(', 'dense_rank(', 'lag(', 'lead(',
                       'first_value(', 'last_value(', 'ntile(']
    window_count = sum(query_lower.count(func) for func in window_functions)
    if window_count > 0:
        score += window_count * 2
        factors.append(f"{window_count} window function{'s' if window_count > 1 else ''} (+{window_count * 2})")

    # Check for GROUP BY
    if 'group by' in query_lower:
        # Count columns in GROUP BY
        group_by_match = re.search(r'group by\s+(.*?)(?:having|order by|limit|$)', query_lower, re.IGNORECASE | re.DOTALL)
        if group_by_match:
            group_cols = len([col.strip() for col in group_by_match.group(1).split(',') if col.strip()])
            if group_cols > 1:
                score += 1
                factors.append(f"GROUP BY {group_cols} columns (+1)")

    # Check for ORDER BY
    if 'order by' in query_lower:
        score += 0.5
        factors.append("ORDER BY (+0.5)")

    # Check for large IN clauses
    in_matches = re.findall(r'in\s*\((.*?)\)', query_lower, re.DOTALL)
    for match in in_matches:
        items = [item.strip() for item in match.split(',') if item.strip()]
        if len(items) > 5:
            score += 1
            factors.append(f"Large IN clause ({len(items)} items) (+1)")
            if len(items) > 20:
                warnings.append(f"Very large IN clause ({len(items)} items) - consider using a temp table or JOIN")

    # Cap score at 10
    score = min(score, 10.0)

    # Determine complexity level
    if score <= 3:
        level = "low"
    elif score <= 6:
        level = "medium"
    else:
        level = "high"

    return {
        "score": round(score, 1),
        "level": level,
        "factors": factors,
        "warnings": warnings
    }


def check_required_filters(sql_query: str, table_name: str) -> List[str]:
    """
    Check if required filters are present in the SQL query.

    For certain tables, specific filters are mandatory:
    - instagram_media_insights: Must filter by user_id
    - Time-series tables: Should have date range filters

    Args:
        sql_query: SQL query to check
        table_name: Primary table being queried

    Returns:
        List of missing required filters

    Example:
        >>> sql = "SELECT * FROM instagram_media_insights"
        >>> missing = check_required_filters(sql, "instagram_media_insights")
        >>> "user_id" in missing
        True
    """
    query_lower = sql_query.lower()
    missing_filters = []

    # Check for user_id filter (CRITICAL for data isolation)
    if 'user_id' in query_lower and 'where' in query_lower:
        # Check if user_id is in WHERE clause
        where_match = re.search(r'where\s+(.*?)(?:group by|order by|limit|$)', query_lower, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            if 'user_id' not in where_clause:
                missing_filters.append("user_id filter in WHERE clause (required for data isolation)")
    else:
        # No user_id filter at all
        if table_name in ['instagram_media', 'instagram_media_insights', 'meta_ads', 'google_analytics']:
            missing_filters.append("user_id filter (CRITICAL: required for data isolation)")

    # Check for date filters on time-series tables
    time_series_tables = ['instagram_media_insights', 'meta_ads_insights', 'google_analytics_sessions']
    if table_name in time_series_tables:
        date_columns = ['timestamp', 'date', 'created_at', 'end_time', 'day']
        has_date_filter = any(col in query_lower for col in date_columns)

        if not has_date_filter:
            missing_filters.append("date range filter (recommended for time-series data)")

    return missing_filters


def get_optimization_hints(sql_query: str, complexity: Dict[str, any] = None) -> List[str]:
    """
    Generate optimization hints for a SQL query.

    Args:
        sql_query: SQL query to analyze
        complexity: Pre-calculated complexity (optional, will calculate if not provided)

    Returns:
        List of optimization suggestions

    Example:
        >>> sql = "SELECT DISTINCT * FROM large_table ORDER BY column"
        >>> hints = get_optimization_hints(sql)
        >>> any("DISTINCT" in hint for hint in hints)
        True
    """
    if complexity is None:
        complexity = calculate_complexity(sql_query)

    hints = []
    query_lower = sql_query.lower()

    # Start with warnings from complexity calculation
    hints.extend(complexity['warnings'])

    # Check for SELECT *
    if re.search(r'select\s+\*', query_lower):
        hints.append("Using SELECT * - specify only needed columns for better performance")

    # Check for missing LIMIT on exploratory queries
    if 'limit' not in query_lower and 'count(' not in query_lower:
        if complexity['score'] < 3:  # Simple queries
            hints.append("Consider adding LIMIT clause for faster exploratory queries")

    # Check for inefficient LIKE patterns
    if re.search(r"like\s+['\"]%", query_lower):
        hints.append("LIKE patterns starting with % can't use indexes - consider alternative approaches")

    # Check for NOT IN (better to use NOT EXISTS or LEFT JOIN)
    if 'not in' in query_lower:
        hints.append("NOT IN can be slow with NULLs - consider using NOT EXISTS or LEFT JOIN instead")

    # Check for OR in WHERE (can prevent index usage)
    where_match = re.search(r'where\s+(.*?)(?:group by|order by|limit|$)', query_lower, re.IGNORECASE | re.DOTALL)
    if where_match:
        where_clause = where_match.group(1)
        or_count = where_clause.count(' or ')
        if or_count > 2:
            hints.append(f"Multiple OR conditions ({or_count}) - consider UNION ALL or IN clause instead")

    # Suggest indexed columns for JOIN conditions
    if 'join' in query_lower and 'user_id' in query_lower:
        hints.append("Ensure JOIN columns (like user_id) are indexed for optimal performance")

    return hints


def validate_syntax_basic(sql_query: str) -> Tuple[bool, str]:
    """
    Basic SQL syntax validation.

    This is a lightweight check, not a full parser. Catches common mistakes:
    - Unclosed quotes
    - Mismatched parentheses
    - Invalid keywords placement

    Args:
        sql_query: SQL query to validate

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> is_valid, error = validate_syntax_basic("SELECT * FROM users WHERE name = 'test")
        >>> is_valid
        False
        >>> "quote" in error.lower()
        True
    """
    # Check for balanced parentheses
    open_paren = sql_query.count('(')
    close_paren = sql_query.count(')')
    if open_paren != close_paren:
        return False, f"Mismatched parentheses: {open_paren} opening, {close_paren} closing"

    # Check for unclosed quotes
    single_quotes = sql_query.count("'")
    if single_quotes % 2 != 0:
        return False, "Unclosed single quote"

    double_quotes = sql_query.count('"')
    if double_quotes % 2 != 0:
        return False, "Unclosed double quote"

    # Check for required SELECT statement
    if not re.search(r'\bselect\b', sql_query, re.IGNORECASE):
        return False, "Query must contain SELECT statement"

    # Check for FROM clause
    if not re.search(r'\bfrom\b', sql_query, re.IGNORECASE):
        return False, "Query must contain FROM clause"

    return True, ""


def format_complexity_report(complexity: Dict[str, any], hints: List[str] = None) -> str:
    """
    Format complexity analysis into human-readable report.

    Args:
        complexity: Complexity analysis result
        hints: Optional optimization hints

    Returns:
        Formatted string report
    """
    report_lines = []

    # Header
    report_lines.append(f"**Complexity Score**: {complexity['score']}/10 ({complexity['level']})")

    # Factors
    if complexity['factors']:
        report_lines.append("\n**Complexity Factors**:")
        for factor in complexity['factors']:
            report_lines.append(f"  - {factor}")

    # Warnings
    if complexity['warnings']:
        report_lines.append("\n⚠️ **Performance Warnings**:")
        for warning in complexity['warnings']:
            report_lines.append(f"  - {warning}")

    # Optimization hints
    if hints:
        report_lines.append("\n💡 **Optimization Hints**:")
        for hint in hints:
            report_lines.append(f"  - {hint}")

    return "\n".join(report_lines)
