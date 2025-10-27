"""
Social media metric definitions.

Implements metrics for social media performance analysis:
- Engagement Rate
- Frequency
- Reach Rate
- Save Rate
"""

from .base import MetricDefinition, SQLBuilder


class EngagementRate(MetricDefinition):
    """
    Engagement Rate = (likes + comments + saved + shares) / reach * 100

    Measures the percentage of people who engaged with content after seeing it.
    """

    name = "Engagement Rate"
    category = "social_media"
    data_type = "percentage"
    required_fields = ["likes", "comments", "saved", "shares", "reach"]

    def calculate(self, likes: float, comments: float, saved: float,
                  shares: float, reach: float) -> float:
        """
        Calculate engagement rate in Python.

        Args:
            likes: Number of likes
            comments: Number of comments
            saved: Number of saves
            shares: Number of shares
            reach: Number of unique accounts reached

        Returns:
            Engagement rate as percentage
        """
        if reach == 0:
            return 0.0
        total_engagement = likes + comments + saved + shares
        return (total_engagement / reach) * 100

    def to_sql(self, table_alias: str = 'i', **overrides) -> str:
        """
        Generate SQL expression for engagement rate.

        Args:
            table_alias: Table alias (default: 'i' for insights)
            **overrides: Override specific field references

        Returns:
            SQL expression with NULLIF protection

        Example:
            to_sql('i') → "((i.likes + i.comments + i.saved + i.shares) / NULLIF(i.reach, 0)) * 100"
        """
        f = SQLBuilder.field

        # Allow field name overrides for flexibility
        likes = overrides.get('likes', f(table_alias, 'likes'))
        comments = overrides.get('comments', f(table_alias, 'comments'))
        saved = overrides.get('saved', f(table_alias, 'saved'))
        shares = overrides.get('shares', f(table_alias, 'shares'))
        reach = overrides.get('reach', f(table_alias, 'reach'))

        numerator = f"({likes} + {comments} + {saved} + {shares})"
        return f"({SQLBuilder.safe_divide(numerator, reach)}) * 100"


class Frequency(MetricDefinition):
    """
    Frequency = impressions / reach

    Measures average number of times each user saw the content.
    """

    name = "Frequency"
    category = "social_media"
    data_type = "ratio"
    required_fields = ["impressions", "reach"]

    def calculate(self, impressions: float, reach: float) -> float:
        """
        Calculate frequency in Python.

        Args:
            impressions: Total number of times content was displayed
            reach: Number of unique accounts reached

        Returns:
            Frequency ratio
        """
        if reach == 0:
            return 0.0
        return impressions / reach

    def to_sql(self, table_alias: str = 'i', **overrides) -> str:
        """
        Generate SQL expression for frequency.

        Args:
            table_alias: Table alias (default: 'i')
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql('i') → "CAST(i.impressions AS DOUBLE) / NULLIF(i.reach, 0)"
        """
        f = SQLBuilder.field
        impressions = overrides.get('impressions', f(table_alias, 'impressions'))
        reach = overrides.get('reach', f(table_alias, 'reach'))
        return SQLBuilder.safe_divide(impressions, reach)


class ReachRate(MetricDefinition):
    """
    Reach Rate = reach / followers * 100

    Measures percentage of followers who saw the content.
    """

    name = "Reach Rate"
    category = "social_media"
    data_type = "percentage"
    required_fields = ["reach", "followers"]

    def calculate(self, reach: float, followers: float) -> float:
        """
        Calculate reach rate in Python.

        Args:
            reach: Number of unique accounts reached
            followers: Total follower count

        Returns:
            Reach rate as percentage
        """
        if followers == 0:
            return 0.0
        return (reach / followers) * 100

    def to_sql(self, table_alias: str = 'i', followers_alias: str = 'a', **overrides) -> str:
        """
        Generate SQL expression for reach rate.

        Note: Typically reach is in insights table (i) and followers in account table (a).

        Args:
            table_alias: Table alias for reach (default: 'i' for insights)
            followers_alias: Table alias for followers (default: 'a' for account)
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql('i', 'a') → "(CAST(i.reach AS DOUBLE) / NULLIF(a.followers, 0)) * 100"
        """
        f = SQLBuilder.field
        reach = overrides.get('reach', f(table_alias, 'reach'))
        followers = overrides.get('followers', f(followers_alias, 'followers'))
        return f"({SQLBuilder.safe_divide(reach, followers)}) * 100"


class SaveRate(MetricDefinition):
    """
    Save Rate = saved / reach * 100

    Measures percentage of viewers who saved the content.
    """

    name = "Save Rate"
    category = "social_media"
    data_type = "percentage"
    required_fields = ["saved", "reach"]

    def calculate(self, saved: float, reach: float) -> float:
        """
        Calculate save rate in Python.

        Args:
            saved: Number of saves
            reach: Number of unique accounts reached

        Returns:
            Save rate as percentage
        """
        if reach == 0:
            return 0.0
        return (saved / reach) * 100

    def to_sql(self, table_alias: str = 'i', **overrides) -> str:
        """
        Generate SQL expression for save rate.

        Args:
            table_alias: Table alias (default: 'i')
            **overrides: Override specific field references

        Returns:
            SQL expression with zero protection

        Example:
            to_sql('i') → "(CAST(i.saved AS DOUBLE) / NULLIF(i.reach, 0)) * 100"
        """
        f = SQLBuilder.field
        saved = overrides.get('saved', f(table_alias, 'saved'))
        reach = overrides.get('reach', f(table_alias, 'reach'))
        return f"({SQLBuilder.safe_divide(saved, reach)}) * 100"
