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

            # Add column-specific notes (e.g., "Column name is 'saved' not 'saves'")
            if col_def.get('notes'):
                line += f" [NOTE: {col_def['notes']}]"

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
            Dict with 'valid' and 'invalid' column lists, plus 'suggestions' for common mistakes
        """
        table = self.get_table_schema(table_name)
        if not table:
            return {'valid': [], 'invalid': [], 'error': f"Table '{table_name}' not found"}

        valid_columns = set(self.list_table_columns(table_name))

        # Extract column references from SQL (improved regex)
        # Matches patterns like "i.column_name" or "table.column_name"
        column_pattern = r'\b[a-z_]+\.([a-z_]+)\b'
        matches = re.findall(column_pattern, sql_query.lower())

        valid = []
        invalid = []
        suggestions = {}

        # Common column name mistakes
        common_mistakes = {
            'saves': 'saved',  # Most common mistake!
            'save': 'saved',
            'like': 'likes',
            'comment': 'comments',
            'share': 'shares',
            'impression': 'impressions',
        }

        for col in set(matches):
            if col in valid_columns:
                valid.append(col)
            else:
                invalid.append(col)
                # Check if it's a common mistake
                if col in common_mistakes:
                    correct_col = common_mistakes[col]
                    if correct_col in valid_columns:
                        suggestions[col] = correct_col

        return {
            'valid': valid,
            'invalid': invalid,
            'suggestions': suggestions
        }

    def check_data_availability(self, user_query: str) -> Dict[str, Any]:
        """
        Check if the user is asking for data from platforms we don't have.

        This prevents the agent from trying to query unavailable data sources
        and provides helpful alternatives to the user.

        Args:
            user_query: Natural language query from user

        Returns:
            Dict with:
                - available: bool (True if we have the data)
                - missing_platforms: list (platforms mentioned but not available)
                - available_platforms: list (platforms we DO have)
                - suggestion: str (helpful message for user)
        """
        query_lower = user_query.lower()

        # Define platform keywords and their variations
        UNAVAILABLE_PLATFORMS = {
            'snapchat': ['snapchat', 'snap chat', 'snap'],
            'tiktok': ['tiktok', 'tik tok'],
            'pinterest': ['pinterest', 'pin'],
            'linkedin': ['linkedin', 'linked in'],
            'twitter': ['twitter', 'x.com', 'tweet'],
            'youtube': ['youtube', 'yt'],
            'google_analytics': ['google analytics', 'ga4', 'ga'],
            'shopify': ['shopify'],
            'amazon': ['amazon seller', 'amazon ads'],
        }

        # Get list of available platforms from schemas
        available_tables = list(self.schemas.keys())
        AVAILABLE_PLATFORMS = []

        # Detect available platforms from table names
        if any('instagram' in table for table in available_tables):
            AVAILABLE_PLATFORMS.append('Instagram')
        if any('meta' in table or 'facebook' in table for table in available_tables):
            AVAILABLE_PLATFORMS.append('Meta Ads (Facebook/Instagram Ads)')

        # Check for unavailable platform mentions
        # IMPORTANT: Use word boundary matching to avoid false positives
        # (e.g., "again" should NOT match "ga" for Google Analytics)
        missing_platforms = []
        for platform, keywords in UNAVAILABLE_PLATFORMS.items():
            for keyword in keywords:
                # Use word boundary matching for better precision
                if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                    missing_platforms.append(platform.replace('_', ' ').title())
                    break

        # If we found unavailable platforms, return guidance
        if missing_platforms:
            platforms_str = ', '.join(missing_platforms)
            available_str = '\n- '.join(AVAILABLE_PLATFORMS)

            return {
                'available': False,
                'missing_platforms': missing_platforms,
                'available_platforms': AVAILABLE_PLATFORMS,
                'suggestion': f"I don't have access to {platforms_str} data yet.\n\n"
                             f"Currently I can analyze:\n- {available_str}\n\n"
                             f"Would you like me to analyze one of these instead?"
            }

        # Data is available (or no specific platform mentioned)
        return {
            'available': True,
            'missing_platforms': [],
            'available_platforms': AVAILABLE_PLATFORMS,
            'suggestion': None
        }

    def detect_data_inquiry_query(self, user_query: str) -> Dict[str, Any]:
        """
        Detect if user is asking ABOUT data availability rather than requesting data.

        Identifies three types of meta-queries:
        1. Greeting messages (hi, hello, thanks, etc.)
        2. General platform data inquiries (what data do you have on Instagram?)
        3. Specific data type inquiries (do you have demographic data?)

        Args:
            user_query: Natural language query from user

        Returns:
            Dict with:
                - is_inquiry: bool (True if asking about data availability or greeting)
                - data_topic: str (what kind of inquiry: 'greeting', 'platform_data', 'demographics')
                - response: str (informative response)
        """
        query_lower = user_query.lower().strip()
        words = query_lower.split()

        # ========== CHECK 1: Detect Actual Data Requests (to avoid false positives) ==========
        # Patterns that indicate user wants actual data, not meta-information
        DATA_REQUEST_VERBS = [
            'show', 'get', 'fetch', 'give me', 'tell me', 'find',
            'display', 'list', 'see', 'view', 'what are', 'what is',
            'how many', 'how much', 'calculate', 'compute'
        ]

        # Check if query starts with or contains data request verbs
        is_data_request = any(query_lower.startswith(verb) or f" {verb} " in f" {query_lower} "
                             for verb in DATA_REQUEST_VERBS)

        # Also check for specific data requests about metrics/demographics
        requests_specific_data = any(term in query_lower for term in [
            'my followers', 'my engagement', 'my reach', 'my performance',
            'follower demographics', 'follower breakdown', 'audience demographics',
            'top posts', 'recent posts', 'post performance'
        ])

        # If it's clearly a data request, skip inquiry detection entirely
        if is_data_request or requests_specific_data:
            return {
                'is_inquiry': False,
                'data_topic': None,
                'response': None
            }

        # ========== CHECK 2: Greeting Detection ==========
        GREETING_PATTERNS = [
            'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening',
            'how are you', 'how r you', 'whats up', "what's up", 'wassup'
        ]
        THANKS_PATTERNS = ['thanks', 'thank you', 'thank u', 'thx', 'ty']
        PLEASE_PATTERNS = ['please', 'pls', 'plz']

        # Check if it's ONLY a greeting/thanks/please without meaningful content
        is_greeting = any(pattern in query_lower for pattern in GREETING_PATTERNS)
        is_thanks_only = any(pattern in query_lower for pattern in THANKS_PATTERNS) and len(words) <= 3
        is_please_only = any(pattern in query_lower for pattern in PLEASE_PATTERNS) and len(words) <= 2

        if (is_greeting or is_thanks_only or is_please_only) and len(words) <= 5:
            return {
                'is_inquiry': True,
                'data_topic': 'greeting',
                'response': (
                    "Hello! I'm your e-commerce data analytics assistant. "
                    "I can help you analyze your Instagram performance, demographics, and more.\n\n"
                    "Feel free to ask me things like:\n"
                    "- \"Show me my Instagram reach for the last 30 days\"\n"
                    "- \"What are my follower demographics?\"\n"
                    "- \"How is my engagement trending?\""
                )
            }

        # ========== CHECK 3: General Platform Data Inquiry ==========
        INQUIRY_PATTERNS = [
            'what data', 'what information', 'what metrics', 'what info',
            'available data', 'data available', 'what do you have'
        ]
        PLATFORM_KEYWORDS = [
            r'\binstagram\b', r'\binsta\b', r'\big\b',
            'social media', 'platform'
        ]

        has_inquiry_pattern = any(pattern in query_lower for pattern in INQUIRY_PATTERNS)
        mentions_platform = any(re.search(pattern, query_lower) for pattern in PLATFORM_KEYWORDS)

        if has_inquiry_pattern and mentions_platform:
            # General platform data inquiry - list all available data types from schema
            return {
                'is_inquiry': True,
                'data_topic': 'platform_data',
                'response': (
                    "I have access to comprehensive Instagram data for your account, including:\n\n"
                    "**Post & Content Data:**\n"
                    "- Media insights (likes, comments, saves, shares, reach, impressions)\n"
                    "- Engagement rates and performance metrics\n"
                    "- Post timing and content type analysis\n\n"
                    "**Audience Demographics:**\n"
                    "- Follower breakdown by age and gender\n"
                    "- Geographic distribution (countries and cities)\n"
                    "- Audience growth trends\n\n"
                    "**Account Performance:**\n"
                    "- Profile views and website clicks\n"
                    "- Follower counts and growth\n"
                    "- Overall reach and impressions\n\n"
                    "What would you like to explore? For example:\n"
                    "- \"Show me my top performing posts\"\n"
                    "- \"What are my follower demographics?\"\n"
                    "- \"Analyze my engagement trends\""
                )
            }

        # ========== CHECK 3: Specific Demographic Data Inquiry ==========
        DEMOGRAPHIC_KEYWORDS = [
            'demographic', 'demographics', 'demograph',
            'audience breakdown', 'audience data', 'audience details',
            'follower breakdown', 'follower demographics', 'follower data'
        ]

        specific_inquiry_patterns = ['do you have', 'do u have', 'd you have', 'is there', 'are there']
        has_specific_inquiry = any(pattern in query_lower for pattern in specific_inquiry_patterns)
        is_demographic_inquiry = any(keyword in query_lower for keyword in DEMOGRAPHIC_KEYWORDS)

        if has_specific_inquiry and is_demographic_inquiry:
            # Check if platform is mentioned, otherwise ask for clarification
            if mentions_platform:
                return {
                    'is_inquiry': True,
                    'data_topic': 'demographics_instagram',
                    'response': (
                        "Yes! I have access to Instagram follower demographic data, including:\n\n"
                        "**Available Demographic Breakdowns:**\n"
                        "- **Age & Gender**: Distribution of followers by age groups and gender\n"
                        "- **Country**: Top countries where your followers are located\n"
                        "- **City**: Top cities where your followers are located\n\n"
                        "Would you like me to show you any of these breakdowns? For example:\n"
                        "- \"Show me follower demographics by age and gender\"\n"
                        "- \"What countries are my followers from?\"\n"
                        "- \"Show me follower breakdown by city\""
                    )
                }
            else:
                # No platform specified - ask for clarification
                return {
                    'is_inquiry': True,
                    'data_topic': 'demographics_platform_clarification',
                    'response': (
                        "I have demographic data available for **Instagram** (currently the only platform with demographic insights).\n\n"
                        "Would you like to see your Instagram follower demographics? This includes:\n"
                        "- Age and gender breakdown\n"
                        "- Geographic distribution by country and city\n\n"
                        "Just let me know if you'd like to see this data!"
                    )
                }

        # Default: not a recognized data inquiry
        return {
            'is_inquiry': False,
            'data_topic': None,
            'response': None
        }

    def detect_comparison_query(self, user_query: str) -> Dict[str, Any]:
        """
        Detect if a user query is asking for a comparison.

        Identifies comparison keywords and extracts what's being compared:
        - Time periods (Jan vs Feb, this week vs last week, 2024 vs 2023)
        - Content types (Reels vs Posts, Images vs Videos)
        - Campaigns (Campaign A vs Campaign B)
        - Metrics (Engagement vs Reach)

        Args:
            user_query: Natural language query from user

        Returns:
            Dict with:
                - is_comparison: bool (True if query requests comparison)
                - comparison_type: str ("time_period", "content_type", "campaign", "metric")
                - comparison_items: list[str] (things being compared)
                - comparison_dimension: str (what aspect: "performance", "cost", "engagement")
                - original_query: str (preserved for context)
        """
        query_lower = user_query.lower()

        # Comparison keywords
        COMPARISON_KEYWORDS = [
            'compare', 'comparison', 'versus', 'vs', 'vs.',
            'compared to', 'compared with', 'difference between',
            'better than', 'worse than', 'against'
        ]

        # Check if query contains comparison keywords
        has_comparison_keyword = any(keyword in query_lower for keyword in COMPARISON_KEYWORDS)

        if not has_comparison_keyword:
            return {
                'is_comparison': False,
                'comparison_type': None,
                'comparison_items': [],
                'comparison_dimension': None,
                'original_query': user_query
            }

        # ========== Detect Comparison Type ==========

        # 1. Time Period Comparisons
        TIME_PATTERNS = [
            # Month comparisons
            (r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(?:vs|versus|compared to)\s+(january|february|march|april|may|june|july|august|september|october|november|december)', 'time_period'),
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(?:vs|versus|compared to)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', 'time_period'),

            # Week/Month/Year comparisons
            (r'this\s+(week|month|quarter|year)\s+(?:vs|versus|compared to)\s+last\s+(week|month|quarter|year)', 'time_period'),
            (r'last\s+(week|month|quarter|year)\s+(?:vs|versus|compared to)\s+this\s+(week|month|quarter|year)', 'time_period'),

            # Specific time ranges
            (r'(\d{4})\s+(?:vs|versus|compared to)\s+(\d{4})', 'time_period'),  # 2024 vs 2023
            (r'last\s+(\d+)\s+days?\s+(?:vs|versus|compared to)\s+previous\s+(\d+)\s+days?', 'time_period'),
        ]

        # 2. Content Type Comparisons
        CONTENT_TYPE_PATTERNS = [
            (r'(reels?|videos?)\s+(?:vs|versus|compared to)\s+(posts?|images?|photos?)', 'content_type'),
            (r'(posts?|images?|photos?)\s+(?:vs|versus|compared to)\s+(reels?|videos?)', 'content_type'),
            (r'(carousel|carousels)\s+(?:vs|versus|compared to)\s+(single|static)\s+(image|post)', 'content_type'),
            (r'(stories)\s+(?:vs|versus|compared to)\s+(feed\s+posts?|reels?)', 'content_type'),
        ]

        # 3. Campaign/Ad Set Comparisons
        CAMPAIGN_PATTERNS = [
            (r'campaign\s+([a-zA-Z0-9_-]+)\s+(?:vs|versus|compared to)\s+campaign\s+([a-zA-Z0-9_-]+)', 'campaign'),
            (r'ad\s+set\s+([a-zA-Z0-9_-]+)\s+(?:vs|versus|compared to)\s+ad\s+set\s+([a-zA-Z0-9_-]+)', 'campaign'),
        ]

        # Try to match patterns
        comparison_type = None
        comparison_items = []

        # Check time patterns
        for pattern, ctype in TIME_PATTERNS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                comparison_type = ctype
                comparison_items = [match.group(1), match.group(2) if match.lastindex >= 2 else None]
                comparison_items = [item for item in comparison_items if item]  # Remove None
                break

        # Check content type patterns if no time match
        if not comparison_type:
            for pattern, ctype in CONTENT_TYPE_PATTERNS:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    comparison_type = ctype
                    comparison_items = [match.group(1), match.group(2) if match.lastindex >= 2 else None]
                    comparison_items = [item for item in comparison_items if item]
                    break

        # Check campaign patterns if no other match
        if not comparison_type:
            for pattern, ctype in CAMPAIGN_PATTERNS:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    comparison_type = ctype
                    comparison_items = [match.group(1), match.group(2) if match.lastindex >= 2 else None]
                    comparison_items = [item for item in comparison_items if item]
                    break

        # Default to generic comparison if we found keyword but no specific pattern
        if not comparison_type and has_comparison_keyword:
            comparison_type = 'generic'
            # Try to extract two items around 'vs' or 'versus'
            vs_match = re.search(r'(\w+(?:\s+\w+)?)\s+(?:vs|versus)\s+(\w+(?:\s+\w+)?)', query_lower)
            if vs_match:
                comparison_items = [vs_match.group(1), vs_match.group(2)]

        # ========== Detect Comparison Dimension ==========
        # What aspect are we comparing? (performance, cost, engagement, etc.)

        DIMENSION_KEYWORDS = {
            'performance': ['perform', 'performance', 'doing', 'results'],
            'engagement': ['engagement', 'likes', 'comments', 'shares', 'interaction'],
            'reach': ['reach', 'impressions', 'views', 'audience'],
            'cost': ['cost', 'spend', 'budget', 'roas', 'roi', 'cpa', 'cpc'],
            'sales': ['sales', 'revenue', 'conversions', 'purchases'],
        }

        comparison_dimension = None
        for dimension, keywords in DIMENSION_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                comparison_dimension = dimension
                break

        # Default to 'performance' if no specific dimension found
        if not comparison_dimension:
            comparison_dimension = 'performance'

        return {
            'is_comparison': True,
            'comparison_type': comparison_type,
            'comparison_items': comparison_items,
            'comparison_dimension': comparison_dimension,
            'original_query': user_query
        }

    def detect_ambiguous_query(self, user_query: str) -> Dict[str, Any]:
        """
        Detect if a user query is too ambiguous and needs clarification.

        Identifies vague terms that could mean multiple things in an e-commerce context
        and suggests specific follow-up questions to ask the user.

        Args:
            user_query: Natural language query from user

        Returns:
            Dict with:
                - is_ambiguous: bool (True if query needs clarification)
                - ambiguous_terms: list (vague terms found in query)
                - clarification_question: str (polite question to ask user)
                - options: list[dict] (multiple choice options for user)
                    Each option: {"label": str, "description": str, "focus": str}
        """
        query_lower = user_query.lower()

        # Define ambiguous terms and their possible interpretations
        AMBIGUOUS_TERMS = {
            "business": {
                "question": "I can help analyze your business! What aspect would you like to focus on?",
                "options": [
                    {
                        "label": "Revenue & Sales",
                        "description": "Overall revenue trends, sales performance, and growth rates",
                        "focus": "revenue"
                    },
                    {
                        "label": "Ad Performance & ROI",
                        "description": "Advertising spend efficiency, ROAS, and campaign effectiveness",
                        "focus": "advertising"
                    },
                    {
                        "label": "Customer Acquisition",
                        "description": "Customer acquisition cost, conversion rates, and funnel metrics",
                        "focus": "acquisition"
                    },
                    {
                        "label": "Profitability",
                        "description": "Profit margins, P&L analysis, and cost breakdowns",
                        "focus": "profit"
                    }
                ]
            },
            "performance": {
                "question": "I can analyze performance metrics! What type of performance are you interested in?",
                "options": [
                    {
                        "label": "Social Media Engagement",
                        "description": "Likes, comments, shares, saves, and engagement rates on Instagram",
                        "focus": "engagement"
                    },
                    {
                        "label": "Ad Campaign Performance",
                        "description": "Ad reach, impressions, CTR, conversions, and ROAS",
                        "focus": "ad_performance"
                    },
                    {
                        "label": "Content Performance",
                        "description": "Top-performing posts, reels, stories, and content types",
                        "focus": "content"
                    },
                    {
                        "label": "Sales & Conversions",
                        "description": "Conversion rates, sales growth, and revenue performance",
                        "focus": "sales"
                    }
                ]
            },
            "doing": {
                "question": "I can provide various insights! What would you like to know about?",
                "options": [
                    {
                        "label": "Growth Trends",
                        "description": "Are metrics growing, declining, or staying flat over time?",
                        "focus": "trends"
                    },
                    {
                        "label": "Profitability",
                        "description": "Are we making money? What are the profit margins?",
                        "focus": "profit"
                    },
                    {
                        "label": "Efficiency",
                        "description": "How efficiently are we using our marketing budget and resources?",
                        "focus": "efficiency"
                    },
                    {
                        "label": "Overall Health",
                        "description": "High-level summary of key business metrics and indicators",
                        "focus": "summary"
                    }
                ]
            },
            "content": {
                "question": "I can analyze different types of content! Which content are you referring to?",
                "options": [
                    {
                        "label": "Instagram Posts",
                        "description": "Feed posts (single images, carousels)",
                        "focus": "posts"
                    },
                    {
                        "label": "Instagram Reels",
                        "description": "Short-form video content",
                        "focus": "reels"
                    },
                    {
                        "label": "Instagram Stories",
                        "description": "24-hour ephemeral content",
                        "focus": "stories"
                    },
                    {
                        "label": "All Content Types",
                        "description": "Compare performance across all content formats",
                        "focus": "all_content"
                    }
                ]
            },
            "trending": {
                "question": "I can show you what's trending! What specifically are you looking for?",
                "options": [
                    {
                        "label": "Trending Posts",
                        "description": "Your best-performing recent content",
                        "focus": "trending_posts"
                    },
                    {
                        "label": "Trending Topics",
                        "description": "Popular themes and subjects in your niche",
                        "focus": "trending_topics"
                    },
                    {
                        "label": "Trending Products",
                        "description": "Products driving the most engagement or sales",
                        "focus": "trending_products"
                    }
                ]
            }
        }

        # Check if query is very short and vague (high likelihood of ambiguity)
        words = query_lower.split()
        is_very_short = len(words) <= 5

        # Detect ambiguous terms
        found_ambiguous_terms = []
        clarification_data = None

        for term, term_data in AMBIGUOUS_TERMS.items():
            # Check if term appears in query
            # Use word boundary matching to avoid false positives (e.g., "busy" shouldn't match "business")
            if re.search(rf'\b{term}\b', query_lower):
                found_ambiguous_terms.append(term)
                # Use the first matching ambiguous term for clarification
                if not clarification_data:
                    clarification_data = term_data

        # Additional heuristics for ambiguous queries
        vague_phrases = [
            "how is", "how are", "how's", "hows",
            "what about", "tell me about",
            "show me", "give me",
            "analyze", "check"
        ]

        has_vague_phrase = any(phrase in query_lower for phrase in vague_phrases)

        # ========== Check for vague platform status queries ==========
        # Queries like "how's insta?", "how's instagram?", "how's meta ads?"
        platform_keywords = [
            'instagram', 'insta', 'ig',
            'meta ads', 'meta', 'facebook ads', 'fb ads',
            'social media', 'social'
        ]

        mentions_platform = any(platform in query_lower for platform in platform_keywords)

        # If it's a vague status query about a platform (e.g., "how's insta?", "how is instagram?", "hows insta doing again?")
        # Trigger if: vague phrase + platform mention + reasonably short (≤8 words) + no specific metrics mentioned
        is_reasonably_short = len(words) <= 8

        # Check if specific metrics are mentioned (if so, it's not ambiguous)
        specific_metrics = ['engagement', 'reach', 'impressions', 'followers', 'likes', 'comments', 'saves', 'shares', 'revenue', 'sales', 'conversions']
        has_specific_metric = any(metric in query_lower for metric in specific_metrics)

        if has_vague_phrase and mentions_platform and is_reasonably_short and not has_specific_metric:
            # User is asking "how's [platform]?" without specifying what they want to know
            clarification_data = {
                "question": "I can help analyze your Instagram performance! What would you like to know specifically?",
                "options": [
                    {
                        "label": "Recent Posts Performance",
                        "description": "Engagement, reach, and saves for your latest posts",
                        "focus": "recent_posts"
                    },
                    {
                        "label": "Overall Reach & Engagement",
                        "description": "Total reach, impressions, and engagement rates over last 30 days",
                        "focus": "reach_engagement_30d"
                    },
                    {
                        "label": "Top Performing Content",
                        "description": "Best-performing posts and content types",
                        "focus": "top_content"
                    },
                    {
                        "label": "Growth Trends",
                        "description": "How metrics are changing over time (growing or declining)",
                        "focus": "trends"
                    }
                ]
            }

            return {
                'is_ambiguous': True,
                'ambiguous_terms': ['platform_status'],
                'clarification_question': clarification_data['question'],
                'options': clarification_data['options']
            }

        # Query is ambiguous if:
        # 1. Contains ambiguous term AND is short/vague, OR
        # 2. Is very short (≤3 words) and contains vague phrases
        is_ambiguous = (
            (found_ambiguous_terms and is_very_short) or
            (len(words) <= 3 and has_vague_phrase)
        )

        if is_ambiguous and clarification_data:
            return {
                'is_ambiguous': True,
                'ambiguous_terms': found_ambiguous_terms,
                'clarification_question': clarification_data['question'],
                'options': clarification_data['options']
            }

        return {
            'is_ambiguous': False,
            'ambiguous_terms': [],
            'clarification_question': None,
            'options': []
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


def check_data_availability(user_query: str) -> Dict[str, Any]:
    """Check if user is asking for data we don't have."""
    return semantic_layer.check_data_availability(user_query)


def detect_ambiguous_query(user_query: str) -> Dict[str, Any]:
    """Detect if query is ambiguous and needs clarification."""
    return semantic_layer.detect_ambiguous_query(user_query)


def detect_comparison_query(user_query: str) -> Dict[str, Any]:
    """Detect if query is asking for a comparison between two things."""
    return semantic_layer.detect_comparison_query(user_query)


def detect_data_inquiry_query(user_query: str) -> Dict[str, Any]:
    """Detect if user is asking ABOUT data availability rather than requesting data."""
    return semantic_layer.detect_data_inquiry_query(user_query)
