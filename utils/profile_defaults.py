"""
Default values and validation schemas for user business profiles.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class BusinessCategory(str, Enum):
    """Business category options."""
    FASHION_APPAREL = "Fashion & Apparel"
    BEAUTY_COSMETICS = "Beauty & Cosmetics"
    HOME_GARDEN = "Home & Garden"
    FOOD_BEVERAGE = "Food & Beverage"
    ELECTRONICS = "Electronics"
    JEWELRY_ACCESSORIES = "Jewelry & Accessories"
    SPORTS_FITNESS = "Sports & Fitness"
    PET_SUPPLIES = "Pet Supplies"
    TOYS_GAMES = "Toys & Games"
    HEALTH_WELLNESS = "Health & Wellness"
    OTHER = "Other"


class PricePoint(str, Enum):
    """Price point positioning."""
    BUDGET = "Budget"  # <$30 AOV
    MID_RANGE = "Mid-range"  # $30-100 AOV
    PREMIUM = "Premium"  # $100-300 AOV
    LUXURY = "Luxury"  # $300+ AOV


class BusinessStage(str, Enum):
    """Business maturity stage."""
    STARTUP = "Startup"  # 0-$50K/month revenue
    GROWTH = "Growth"  # $50K-$500K/month
    SCALING = "Scaling"  # $500K-$2M/month
    ESTABLISHED = "Established"  # $2M+/month


class PrimaryKPI(str, Enum):
    """Primary business goal/KPI."""
    REVENUE = "revenue"
    PROFIT = "profit"
    CUSTOMER_COUNT = "customer_count"
    BRAND_AWARENESS = "brand_awareness"
    MARKET_SHARE = "market_share"


class AnalysisDepth(str, Enum):
    """Preferred analysis depth."""
    QUICK = "quick"  # High-level summary, 2-3 key insights
    DETAILED = "detailed"  # Comprehensive analysis, 5-7 insights
    COMPREHENSIVE = "comprehensive"  # Deep dive, 10+ insights with context


class RecommendationStyle(str, Enum):
    """Recommendation approach preference."""
    CONSERVATIVE = "conservative"  # Safe, proven tactics
    BALANCED = "balanced"  # Mix of safe and growth-oriented
    AGGRESSIVE = "aggressive"  # Growth-focused, higher risk


# Default profile values
DEFAULT_BUSINESS_PROFILE = {
    "brand": None,
    "category": None,
    "target_audience": None,
    "price_point": None,
    "monthly_revenue": None,
    "business_stage": None,
    "created_at": None,
    "updated_at": None,
}

DEFAULT_GOALS = {
    "primary_kpi": PrimaryKPI.REVENUE.value,
    "target_roas": 3.0,
    "target_margin": 50.0,
    "growth_target": 10.0,  # % monthly growth goal
    "created_at": None,
    "updated_at": None,
}

DEFAULT_PREFERENCES = {
    "analysis_depth": AnalysisDepth.DETAILED.value,
    "recommendation_style": RecommendationStyle.BALANCED.value,
    "visual_preferences": {
        "use_emojis": True,
        "use_tables": True,
        "use_charts": False,  # Future: generate charts
    },
    "created_at": None,
    "updated_at": None,
}

DEFAULT_LEARNED_CONTEXT = {
    "common_questions": [],
    "pain_points": [],
    "successful_actions": [],
    "channel_focus": {},  # e.g., {"instagram": 70, "facebook": 20, "email": 10}
    "created_at": None,
    "updated_at": None,
}


def get_default_profile() -> Dict[str, Any]:
    """
    Get complete default profile structure.

    Returns:
        Dictionary with all profile sections
    """
    now = datetime.now(timezone.utc)

    return {
        "business_profile": {
            **DEFAULT_BUSINESS_PROFILE,
            "created_at": now,
            "updated_at": now,
        },
        "goals": {
            **DEFAULT_GOALS,
            "created_at": now,
            "updated_at": now,
        },
        "preferences": {
            **DEFAULT_PREFERENCES,
            "created_at": now,
            "updated_at": now,
        },
        "learned_context": {
            **DEFAULT_LEARNED_CONTEXT,
            "created_at": now,
            "updated_at": now,
        },
    }


def validate_business_profile(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate business profile data.

    Args:
        data: Business profile data to validate

    Returns:
        Validated profile data with defaults filled in

    Raises:
        ValueError: If validation fails
    """
    validated = DEFAULT_BUSINESS_PROFILE.copy()

    # Optional fields
    validated["brand"] = data.get("brand")
    validated["target_audience"] = data.get("target_audience")
    validated["monthly_revenue"] = data.get("monthly_revenue")

    # Enum validation
    if "category" in data and data["category"]:
        if data["category"] not in [e.value for e in BusinessCategory]:
            raise ValueError(f"Invalid category: {data['category']}")
        validated["category"] = data["category"]

    if "price_point" in data and data["price_point"]:
        if data["price_point"] not in [e.value for e in PricePoint]:
            raise ValueError(f"Invalid price_point: {data['price_point']}")
        validated["price_point"] = data["price_point"]

    if "business_stage" in data and data["business_stage"]:
        if data["business_stage"] not in [e.value for e in BusinessStage]:
            raise ValueError(f"Invalid business_stage: {data['business_stage']}")
        validated["business_stage"] = data["business_stage"]

    # Timestamps
    validated["created_at"] = data.get("created_at", datetime.now(timezone.utc))
    validated["updated_at"] = datetime.now(timezone.utc)

    return validated


def validate_goals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate goals data.

    Args:
        data: Goals data to validate

    Returns:
        Validated goals data

    Raises:
        ValueError: If validation fails
    """
    validated = DEFAULT_GOALS.copy()

    # Primary KPI
    if "primary_kpi" in data:
        if data["primary_kpi"] not in [e.value for e in PrimaryKPI]:
            raise ValueError(f"Invalid primary_kpi: {data['primary_kpi']}")
        validated["primary_kpi"] = data["primary_kpi"]

    # Numeric targets
    if "target_roas" in data:
        target_roas = float(data["target_roas"])
        if target_roas < 0:
            raise ValueError("target_roas must be positive")
        validated["target_roas"] = target_roas

    if "target_margin" in data:
        target_margin = float(data["target_margin"])
        if not 0 <= target_margin <= 100:
            raise ValueError("target_margin must be between 0 and 100")
        validated["target_margin"] = target_margin

    if "growth_target" in data:
        growth_target = float(data["growth_target"])
        validated["growth_target"] = growth_target

    # Timestamps
    validated["created_at"] = data.get("created_at", datetime.now(timezone.utc))
    validated["updated_at"] = datetime.now(timezone.utc)

    return validated


def validate_preferences(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate preferences data.

    Args:
        data: Preferences data to validate

    Returns:
        Validated preferences data

    Raises:
        ValueError: If validation fails
    """
    validated = DEFAULT_PREFERENCES.copy()

    # Analysis depth
    if "analysis_depth" in data:
        if data["analysis_depth"] not in [e.value for e in AnalysisDepth]:
            raise ValueError(f"Invalid analysis_depth: {data['analysis_depth']}")
        validated["analysis_depth"] = data["analysis_depth"]

    # Recommendation style
    if "recommendation_style" in data:
        if data["recommendation_style"] not in [e.value for e in RecommendationStyle]:
            raise ValueError(f"Invalid recommendation_style: {data['recommendation_style']}")
        validated["recommendation_style"] = data["recommendation_style"]

    # Visual preferences
    if "visual_preferences" in data:
        visual_prefs = validated["visual_preferences"].copy()
        visual_prefs.update(data["visual_preferences"])
        validated["visual_preferences"] = visual_prefs

    # Timestamps
    validated["created_at"] = data.get("created_at", datetime.now(timezone.utc))
    validated["updated_at"] = datetime.now(timezone.utc)

    return validated


def format_profile_for_prompt(profile: Dict[str, Any]) -> str:
    """
    Format user profile for injection into agent prompts.

    Args:
        profile: Complete user profile dictionary

    Returns:
        Formatted string for prompt context
    """
    business = profile.get("business_profile", {})
    goals = profile.get("goals", {})
    preferences = profile.get("preferences", {})
    learned = profile.get("learned_context", {})

    # Build context string
    context_parts = []

    # Business info
    if business.get("brand"):
        context_parts.append(f"Business: {business['brand']}")

    if business.get("category"):
        context_parts.append(f"Category: {business['category']}")

    if business.get("business_stage"):
        context_parts.append(f"Stage: {business['business_stage']}")

    if business.get("price_point"):
        context_parts.append(f"Price Point: {business['price_point']}")

    # Goals
    if goals.get("primary_kpi"):
        context_parts.append(f"Primary Goal: {goals['primary_kpi']}")

    if goals.get("target_roas"):
        context_parts.append(f"Target ROAS: {goals['target_roas']}x")

    # Preferences
    if preferences.get("analysis_depth"):
        context_parts.append(f"Analysis Depth: {preferences['analysis_depth']}")

    if preferences.get("recommendation_style"):
        context_parts.append(f"Recommendation Style: {preferences['recommendation_style']}")

    # Learned context
    if learned.get("common_questions"):
        common_q = learned["common_questions"][:3]  # Top 3
        context_parts.append(f"Common Questions: {', '.join(common_q)}")

    if learned.get("channel_focus"):
        channels = learned["channel_focus"]
        if channels:
            top_channel = max(channels, key=channels.get)
            context_parts.append(f"Primary Channel: {top_channel} ({channels[top_channel]}%)")

    # Join all parts
    if not context_parts:
        return "No profile information available."

    return "User Profile: " + " | ".join(context_parts)


def get_category_benchmarks(category: str) -> Dict[str, Any]:
    """
    Get relevant benchmarks for a business category.

    Args:
        category: Business category

    Returns:
        Dictionary of category-specific benchmarks
    """
    # Reference data from industry_benchmarks.md
    benchmarks = {
        "Fashion & Apparel": {
            "conversion_rate": {"avg": 2.1, "good": 2.5, "excellent": 3.5},
            "aov": {"avg": 75, "good": 100, "excellent": 120},
            "gross_margin": {"avg": 50, "good": 55, "excellent": 60},
            "roas": {"avg": 2.5, "good": 3.0, "excellent": 4.0},
        },
        "Beauty & Cosmetics": {
            "conversion_rate": {"avg": 3.0, "good": 3.5, "excellent": 4.5},
            "aov": {"avg": 55, "good": 70, "excellent": 90},
            "gross_margin": {"avg": 60, "good": 65, "excellent": 70},
            "roas": {"avg": 3.0, "good": 3.5, "excellent": 5.0},
        },
        "Home & Garden": {
            "conversion_rate": {"avg": 2.4, "good": 2.8, "excellent": 3.8},
            "aov": {"avg": 100, "good": 140, "excellent": 180},
            "gross_margin": {"avg": 45, "good": 50, "excellent": 55},
            "roas": {"avg": 2.2, "good": 2.8, "excellent": 3.5},
        },
        "Food & Beverage": {
            "conversion_rate": {"avg": 3.1, "good": 3.5, "excellent": 5.0},
            "aov": {"avg": 45, "good": 60, "excellent": 75},
            "gross_margin": {"avg": 35, "good": 40, "excellent": 45},
            "roas": {"avg": 2.8, "good": 3.5, "excellent": 4.5},
        },
        "Electronics": {
            "conversion_rate": {"avg": 1.8, "good": 2.2, "excellent": 3.0},
            "aov": {"avg": 200, "good": 300, "excellent": 400},
            "gross_margin": {"avg": 30, "good": 35, "excellent": 40},
            "roas": {"avg": 2.0, "good": 2.5, "excellent": 3.0},
        },
    }

    return benchmarks.get(category, {})
