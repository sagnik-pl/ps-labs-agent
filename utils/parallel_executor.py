"""
Parallel Query Executor

Executes multiple SQL queries concurrently using asyncio for significant speedup.
Used primarily for comparison queries that can be split into independent sub-queries.

Example:
    Compare Jan vs Feb → Run 2 queries in parallel instead of sequentially

Usage:
    from utils.parallel_executor import execute_queries_parallel

    results = await execute_queries_parallel(
        queries=[sql1, sql2, sql3],
        user_id="user123"
    )
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


async def execute_queries_parallel(
    queries: List[str],
    user_id: str,
    labels: Optional[List[str]] = None,
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """
    Execute multiple SQL queries in parallel using asyncio.

    Args:
        queries: List of SQL query strings to execute
        user_id: User ID for all queries (for data isolation)
        labels: Optional labels for each query (for result identification)
        max_concurrent: Maximum number of concurrent queries (default: 5)

    Returns:
        Dictionary with:
        - success: bool (True if all queries succeeded)
        - results: list[dict] (each with 'query', 'label', 'data', 'error', 'duration')
        - total_duration: float (total time in seconds)
        - speedup: float (sequential_time / parallel_time)
        - errors: list[str] (error messages if any failed)

    Example:
        >>> results = await execute_queries_parallel(
        ...     queries=[sql1, sql2],
        ...     user_id="user123",
        ...     labels=["January", "February"]
        ... )
        >>> results['speedup']
        2.3  # 2.3x faster than sequential
    """
    if not queries:
        return {
            'success': False,
            'results': [],
            'total_duration': 0,
            'speedup': 1.0,
            'errors': ['No queries provided']
        }

    # Default labels if not provided
    if labels is None:
        labels = [f"Query {i+1}" for i in range(len(queries))]

    if len(labels) != len(queries):
        logger.warning(f"Label count ({len(labels)}) != query count ({len(queries)}). Using defaults.")
        labels = [f"Query {i+1}" for i in range(len(queries))]

    start_time = time.time()

    # Import athena client
    from utils.aws_client import aws_client

    # Create tasks for parallel execution
    tasks = []
    for i, (query, label) in enumerate(zip(queries, labels)):
        task = _execute_single_query_async(
            query=query,
            user_id=user_id,
            label=label,
            query_index=i
        )
        tasks.append(task)

    # Execute all queries concurrently with semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(task):
        async with semaphore:
            return await task

    bounded_tasks = [bounded_task(task) for task in tasks]
    query_results = await asyncio.gather(*bounded_tasks, return_exceptions=True)

    total_duration = time.time() - start_time

    # Process results
    results = []
    errors = []
    all_succeeded = True

    for i, result in enumerate(query_results):
        if isinstance(result, Exception):
            # Query failed with exception
            error_msg = f"{labels[i]}: {str(result)}"
            errors.append(error_msg)
            all_succeeded = False

            results.append({
                'query': queries[i],
                'label': labels[i],
                'data': None,
                'error': str(result),
                'duration': 0,
                'success': False
            })
        elif result.get('error'):
            # Query failed
            errors.append(f"{labels[i]}: {result['error']}")
            all_succeeded = False
            results.append(result)
        else:
            # Query succeeded
            results.append(result)

    # Estimate sequential time (sum of individual durations)
    sequential_time = sum(r.get('duration', 0) for r in results if r.get('duration'))
    speedup = sequential_time / total_duration if total_duration > 0 else 1.0

    logger.info(f"✅ Parallel execution complete: {len(queries)} queries in {total_duration:.2f}s (speedup: {speedup:.1f}x)")

    return {
        'success': all_succeeded,
        'results': results,
        'total_duration': total_duration,
        'speedup': round(speedup, 2),
        'errors': errors,
        'query_count': len(queries),
        'successful_queries': sum(1 for r in results if r.get('success', False))
    }


async def _execute_single_query_async(
    query: str,
    user_id: str,
    label: str,
    query_index: int
) -> Dict[str, Any]:
    """
    Execute a single SQL query asynchronously.

    Wraps synchronous Athena execution in async executor to enable parallelism.

    Args:
        query: SQL query string
        user_id: User ID for data isolation
        label: Label for this query
        query_index: Index of this query in the batch

    Returns:
        Dictionary with query results and metadata
    """
    start_time = time.time()

    try:
        # Import here to avoid circular dependencies
        from utils.aws_client import aws_client

        # Run synchronous Athena query in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            df = await loop.run_in_executor(
                pool,
                aws_client.execute_query,
                query,
                user_id
            )

        duration = time.time() - start_time

        # Convert DataFrame to dict for JSON serialization
        if df is not None and not df.empty:
            data = df.to_dict('records')
            row_count = len(data)
        else:
            data = []
            row_count = 0

        logger.info(f"✓ {label}: {row_count} rows in {duration:.2f}s")

        return {
            'query': query,
            'label': label,
            'data': data,
            'row_count': row_count,
            'error': None,
            'duration': duration,
            'success': True,
            'index': query_index
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"✗ {label} failed after {duration:.2f}s: {str(e)}")

        return {
            'query': query,
            'label': label,
            'data': None,
            'row_count': 0,
            'error': str(e),
            'duration': duration,
            'success': False,
            'index': query_index
        }


def merge_comparison_results(
    parallel_results: Dict[str, Any],
    comparison_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge results from parallel comparison queries into a unified comparison report.

    Args:
        parallel_results: Results from execute_queries_parallel()
        comparison_data: Original comparison detection data

    Returns:
        Dictionary with:
        - comparison_type: str
        - items_compared: list[str]
        - comparison_table: dict (side-by-side comparison)
        - deltas: dict (differences between items)
        - summary: str (text summary)

    Example:
        >>> merge_comparison_results(parallel_results, comparison_data)
        {
            'comparison_type': 'time_period',
            'items_compared': ['January', 'February'],
            'comparison_table': {...},
            'deltas': {'engagement': '+15%'},
            'summary': 'February outperformed January by 15% in engagement'
        }
    """
    if not parallel_results.get('success'):
        return {
            'comparison_type': comparison_data.get('comparison_type'),
            'items_compared': [],
            'comparison_table': {},
            'deltas': {},
            'summary': f"Comparison failed: {', '.join(parallel_results.get('errors', []))}",
            'error': True
        }

    results = parallel_results['results']
    comparison_type = comparison_data.get('comparison_type', 'generic')
    dimension = comparison_data.get('comparison_dimension', 'performance')

    # Extract labels and data
    items_compared = [r['label'] for r in results if r.get('success')]

    # Build side-by-side comparison table
    comparison_table = _build_comparison_table(results)

    # Calculate deltas (differences/changes)
    deltas = _calculate_deltas(results, dimension)

    # Generate summary
    summary = _generate_comparison_summary(
        items_compared, deltas, comparison_type, dimension
    )

    return {
        'comparison_type': comparison_type,
        'comparison_dimension': dimension,
        'items_compared': items_compared,
        'comparison_table': comparison_table,
        'deltas': deltas,
        'summary': summary,
        'speedup': parallel_results.get('speedup', 1.0),
        'total_duration': parallel_results.get('total_duration', 0),
        'error': False
    }


def _build_comparison_table(results: List[Dict]) -> Dict[str, Any]:
    """Build side-by-side comparison table from query results."""

    # Extract column names from first successful result
    columns = []
    for result in results:
        if result.get('success') and result.get('data'):
            if len(result['data']) > 0:
                columns = list(result['data'][0].keys())
                break

    if not columns:
        return {}

    # Build table: {column: {label1: value1, label2: value2, ...}}
    table = {col: {} for col in columns}

    for result in results:
        if not result.get('success'):
            continue

        label = result['label']
        data = result.get('data', [])

        # For simplicity, use aggregated values (sum/avg)
        for col in columns:
            values = [row.get(col) for row in data if row.get(col) is not None]

            if not values:
                table[col][label] = None
                continue

            # Use average for numeric columns, first value for others
            if isinstance(values[0], (int, float)):
                table[col][label] = round(sum(values) / len(values), 2)
            else:
                table[col][label] = values[0]

    return table


def _calculate_deltas(results: List[Dict], dimension: str) -> Dict[str, Any]:
    """Calculate differences between comparison items."""

    if len(results) < 2:
        return {}

    # Get first two successful results for comparison
    successful_results = [r for r in results if r.get('success') and r.get('data')]

    if len(successful_results) < 2:
        return {}

    result1, result2 = successful_results[0], successful_results[1]
    label1, label2 = result1['label'], result2['label']

    deltas = {}

    # Extract numeric metrics from both results
    data1 = result1['data']
    data2 = result2['data']

    if not data1 or not data2:
        return {}

    # Calculate deltas for each numeric column
    for col in data1[0].keys():
        values1 = [row.get(col) for row in data1 if isinstance(row.get(col), (int, float))]
        values2 = [row.get(col) for row in data2 if isinstance(row.get(col), (int, float))]

        if values1 and values2:
            avg1 = sum(values1) / len(values1)
            avg2 = sum(values2) / len(values2)

            delta = avg2 - avg1
            delta_pct = (delta / avg1 * 100) if avg1 != 0 else 0

            deltas[col] = {
                'absolute': round(delta, 2),
                'percentage': round(delta_pct, 1),
                'formatted': f"{'+' if delta >= 0 else ''}{delta_pct:.1f}%",
                'comparison': f"{label2} vs {label1}"
            }

    return deltas


def _generate_comparison_summary(
    items: List[str],
    deltas: Dict[str, Any],
    comparison_type: str,
    dimension: str
) -> str:
    """Generate natural language summary of comparison."""

    if len(items) < 2:
        return f"Insufficient data to compare {dimension}"

    item1, item2 = items[0], items[1]

    # Find the most significant delta
    if deltas:
        # Get delta with largest absolute percentage change
        significant_metric = max(
            deltas.items(),
            key=lambda x: abs(x[1].get('percentage', 0))
        )

        metric_name = significant_metric[0]
        delta_info = significant_metric[1]

        direction = "outperformed" if delta_info['percentage'] > 0 else "underperformed"
        abs_pct = abs(delta_info['percentage'])

        return (
            f"{item2} {direction} {item1} by {abs_pct:.1f}% in {metric_name}. "
            f"Overall {dimension} comparison shows {len(deltas)} metrics analyzed."
        )
    else:
        return f"Compared {item1} vs {item2} for {dimension}"
