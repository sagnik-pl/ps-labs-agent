"""
Semantic Layer for E-commerce Analytics

Provides structured access to metric definitions, schema information,
and query patterns. Acts as a knowledge layer between user questions
and SQL generation, ensuring correct formulas, column names, and interpretations.

Usage:
    from utils.semantic_layer import semantic_layer

    # Get metric definition
    metric = semantic_layer.get_metric("engagement_rate")
    sql_expr = metric["sql_expression"]

    # Get schema information
    column_info = semantic_layer.get_column("instagram_media_insights", "saved")

    # Find matching query pattern
    pattern = semantic_layer.match_query_pattern("what content performed best?")
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class SemanticLayer:
    """
    Semantic layer providing structured access to metrics, schemas, and query patterns.

    Loads configuration from YAML files and provides methods to:
    - Get metric definitions and SQL expressions
    - Validate column names against schema
    - Match user queries to optimized query patterns
    - Provide interpretation guidelines for metrics
    """

    def __init__(self, config_dir: str = "config/semantic_layer"):
        """
        Initialize semantic layer by loading configuration files.

        Args:
            config_dir: Directory containing YAML configuration files
        """
        self.config_dir = Path(config_dir)
        self._metrics: Optional[Dict] = None
        self._schemas: Optional[Dict] = None
        self._query_patterns: Optional[Dict] = None

        # Load configurations
        self._load_configs()

        logger.info(f"✅ Semantic layer initialized with {len(self.metrics)} metrics, "
                   f"{len(self.schemas)} tables, {len(self.query_patterns)} query patterns")

    def _load_configs(self):
        """Load all configuration files."""
        try:
            # Load metrics
            metrics_path = self.config_dir / "metrics.yaml"
            with open(metrics_path, 'r') as f:
                self._metrics = yaml.safe_load(f).get('metrics', {})

            # Load schemas
            schemas_path = self.config_dir / "schemas.yaml"
            with open(schemas_path, 'r') as f:
                self._schemas = yaml.safe_load(f).get('tables', {})

            # Load query patterns
            patterns_path = self.config_dir / "query_patterns.yaml"
            with open(patterns_path, 'r') as f:
                self._query_patterns = yaml.safe_load(f).get('patterns', {})

        except Exception as e:
            logger.error(f"Error loading semantic layer configs: {e}")
            # Initialize empty dicts to prevent crashes
            self._metrics = self._metrics or {}
            self._schemas = self._schemas or {}
            self._query_patterns = self._query_patterns or {}

    @property
    def metrics(self) -> Dict:
        """Get all metric definitions."""
        return self._metrics

    @property
    def schemas(self) -> Dict:
        """Get all schema definitions."""
        return self._schemas

    @property
    def query_patterns(self) -> Dict:
        """Get all query pattern definitions."""
        return self._query_patterns

    # ========== Metric Methods ==========

    def get_metric(self, metric_name: str) -> Optional[Dict]:
        """
        Get metric definition by name.

        Args:
            metric_name: Name of the metric (e.g., "engagement_rate")

        Returns:
            Metric definition dict or None if not found
        """
        return self.metrics.get(metric_name)

    def get_metric_formula(self, metric_name: str) -> Optional[str]:
        """Get human-readable formula for a metric."""
        metric = self.get_metric(metric_name)
        return metric.get('formula') if metric else None

    def get_metric_sql(self, metric_name: str) -> Optional[str]:
        """Get SQL expression for calculating a metric."""
        metric = self.get_metric(metric_name)
        return metric.get('sql_expression') if metric else None

    def get_metric_interpretation(self, metric_name: str) -> Optional[Dict]:
        """Get interpretation guidelines for a metric."""
        metric = self.get_metric(metric_name)
        return metric.get('interpretation') if metric else None

    def list_metrics_by_category(self, category: str) -> List[str]:
        """
        List all metrics in a category.

        Args:
            category: Category name (e.g., "social_media", "ecommerce", "advertising")

        Returns:
            List of metric names in the category
        """
        return [
            name for name, defn in self.metrics.items()
            if defn.get('category') == category
        ]

    def get_related_metrics(self, metric_name: str) -> List[str]:
        """Get list of related metrics for a given metric."""
        metric = self.get_metric(metric_name)
        return metric.get('related_metrics', []) if metric else []

    # ========== Schema Methods ==========

    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        """
        Get complete schema for a table.

        Args:
            table_name: Name of the table

        Returns:
            Table schema dict or None if not found
        """
        return self.schemas.get(table_name)

    def get_column(self, table_name: str, column_name: str) -> Optional[Dict]:
        """
        Get column definition.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            Column definition dict or None if not found
        """
        table = self.get_table_schema(table_name)
        if not table:
            return None
        return table.get('columns', {}).get(column_name)

    def validate_column(self, table_name: str, column_name: str) -> bool:
        """
        Check if a column exists in a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            True if column exists, False otherwise
        """
        return self.get_column(table_name, column_name) is not None

    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """Get data type of a column."""
        column = self.get_column(table_name, column_name)
        return column.get('type') if column else None

    def list_table_columns(self, table_name: str) -> List[str]:
        """List all column names in a table."""
        table = self.get_table_schema(table_name)
        if not table:
            return []
        return list(table.get('columns', {}).keys())

    def get_aggregatable_columns(self, table_name: str) -> List[str]:
        """Get list of columns that can be aggregated (SUM, AVG, etc.)."""
        table = self.get_table_schema(table_name)
        if not table:
            return []
        return [
            col_name for col_name, col_def in table.get('columns', {}).items()
            if col_def.get('aggregatable', False)
        ]

    def get_join_pattern(self, table1: str, table2: str) -> Optional[Dict]:
        """
        Get recommended join pattern between two tables.

        Args:
            table1: First table name
            table2: Second table name

        Returns:
            Join pattern dict with 'type', 'on', and 'description'
        """
        table1_schema = self.get_table_schema(table1)
        if not table1_schema:
            return None

        common_joins = table1_schema.get('common_joins', [])
        for join in common_joins:
            if join.get('table') == table2:
                return join
        return None

    # ========== Query Pattern Methods ==========

    def get_query_pattern(self, pattern_name: str) -> Optional[Dict]:
        """Get query pattern definition by name."""
        return self.query_patterns.get(pattern_name)

    def match_query_pattern(self, user_query: str) -> Optional[str]:
        """
        Match user query to a query pattern using keywords and regex.

        Args:
            user_query: Natural language query from user

        Returns:
            Name of matching pattern or None
        """
        query_lower = user_query.lower()

        # Try keyword matching first
        patterns_config = self._load_patterns_config()
        keywords = patterns_config.get('pattern_matching', {}).get('keywords', {})

        for keyword, pattern_names in keywords.items():
            if keyword in query_lower:
                # Return first matching pattern
                return pattern_names[0] if pattern_names else None

        # Try regex pattern matching
        question_patterns = patterns_config.get('pattern_matching', {}).get('question_patterns', [])
        for pattern_def in question_patterns:
            regex = pattern_def.get('pattern')
            if regex and re.search(regex, query_lower):
                suggested = pattern_def.get('suggested_patterns', [])
                return suggested[0] if suggested else None

        return None

    def get_pattern_template(self, pattern_name: str, **params) -> Optional[str]:
        """
        Get query template with parameters filled in.

        Args:
            pattern_name: Name of the pattern
            **params: Parameters to fill in the template

        Returns:
            SQL query string with parameters filled in
        """
        pattern = self.get_query_pattern(pattern_name)
        if not pattern:
            return None

        template = pattern.get('template', '')

        # Get default parameters
        pattern_params = pattern.get('parameters', {})
        final_params = {}

        for param_name, param_def in pattern_params.items():
            if param_name in params:
                final_params[param_name] = params[param_name]
            elif 'default' in param_def:
                final_params[param_name] = param_def['default']

        # Fill in template
        try:
            return template.format(**final_params)
        except KeyError as e:
            logger.warning(f"Missing required parameter for pattern '{pattern_name}': {e}")
            return None

    def list_patterns_for_use_case(self, use_case_keyword: str) -> List[str]:
        """
        Find patterns that match a use case.

        Args:
            use_case_keyword: Keyword to search in use cases

        Returns:
            List of matching pattern names
        """
        keyword_lower = use_case_keyword.lower()
        matching = []

        for pattern_name, pattern_def in self.query_patterns.items():
            use_cases = pattern_def.get('use_cases', [])
            for use_case in use_cases:
                if keyword_lower in use_case.lower():
                    matching.append(pattern_name)
                    break

        return matching

    # ========== Helper Methods ==========

    def _load_patterns_config(self) -> Dict:
        """Load full query patterns config including pattern matching rules."""
        try:
            patterns_path = self.config_dir / "query_patterns.yaml"
            with open(patterns_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading query patterns config: {e}")
            return {}

    def get_schema_for_sql_gen(self, table_name: str) -> str:
        """
        Format schema information for SQL generation prompt.

        Args:
            table_name: Name of the table

        Returns:
            Formatted schema string for prompt
        """
        table = self.get_table_schema(table_name)
        if not table:
            return f"Table '{table_name}' not found in schema catalog"

        lines = [
            f"**{table_name}**",
            f"Description: {table.get('description', 'No description')}",
            "",
            "Columns:"
        ]

        columns = table.get('columns', {})
        for col_name, col_def in columns.items():
            col_type = col_def.get('type', 'unknown')
            col_desc = col_def.get('description', '')

            line = f"  - {col_name} ({col_type})"
            if col_desc:
                line += f": {col_desc}"

            # Add important notes
            if col_def.get('filter_required'):
                line += " [REQUIRED: Must filter by this column]"
            if col_def.get('important'):
                line += " [IMPORTANT]"

            lines.append(line)

        # Add notes
        notes = table.get('important_notes', [])
        if notes:
            lines.append("")
            lines.append("Important Notes:")
            for note in notes:
                lines.append(f"  - {note}")

        return "\n".join(lines)

    def validate_sql_columns(self, sql_query: str, table_name: str) -> Dict[str, List[str]]:
        """
        Validate that column names in SQL query exist in schema.

        Args:
            sql_query: SQL query string
            table_name: Primary table being queried

        Returns:
            Dict with 'valid' and 'invalid' column lists
        """
        table = self.get_table_schema(table_name)
        if not table:
            return {'valid': [], 'invalid': [], 'error': f"Table '{table_name}' not found"}

        valid_columns = set(self.list_table_columns(table_name))

        # Extract column references from SQL (simple regex approach)
        # Matches patterns like "i.column_name" or "table.column_name"
        column_pattern = r'\b[a-z_]+\.(saved|likes|comments|reach|shares|impressions|[a-z_]+)\b'
        found_columns = re.findall(column_pattern, sql_query.lower())

        valid = []
        invalid = []

        for col in set(found_columns):
            if col in valid_columns:
                valid.append(col)
            else:
                invalid.append(col)

        return {
            'valid': valid,
            'invalid': invalid
        }


# Global singleton instance
semantic_layer = SemanticLayer()


# ========== Convenience Functions ==========

def get_metric_sql(metric_name: str) -> Optional[str]:
    """Get SQL expression for a metric."""
    return semantic_layer.get_metric_sql(metric_name)


def validate_column(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    return semantic_layer.validate_column(table_name, column_name)


def get_schema_info(table_name: str) -> str:
    """Get formatted schema information for prompts."""
    return semantic_layer.get_schema_for_sql_gen(table_name)


def match_query_pattern(user_query: str) -> Optional[str]:
    """Match user query to an optimized query pattern."""
    return semantic_layer.match_query_pattern(user_query)
