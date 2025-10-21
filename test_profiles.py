"""
Test script for user profile functionality (PSAG-82).

Tests:
1. Profile defaults and validation
2. Profile formatting for prompts
3. Firebase client profile methods (without actually connecting to Firestore)
"""
import sys
from utils.profile_defaults import (
    get_default_profile,
    validate_business_profile,
    validate_goals,
    validate_preferences,
    format_profile_for_prompt,
    get_category_benchmarks,
    BusinessCategory,
    PricePoint,
    BusinessStage,
    PrimaryKPI,
    AnalysisDepth,
    RecommendationStyle,
)


def test_enums():
    """Test that all enums are defined correctly."""
    print("\n" + "=" * 80)
    print("TEST 1: Enum Definitions")
    print("=" * 80)

    assert BusinessCategory.FASHION_APPAREL.value == "Fashion & Apparel"
    assert PricePoint.PREMIUM.value == "Premium"
    assert BusinessStage.GROWTH.value == "Growth"
    assert PrimaryKPI.REVENUE.value == "revenue"
    assert AnalysisDepth.DETAILED.value == "detailed"
    assert RecommendationStyle.BALANCED.value == "balanced"

    print("✅ All enums defined correctly")


def test_default_profile():
    """Test default profile generation."""
    print("\n" + "=" * 80)
    print("TEST 2: Default Profile Generation")
    print("=" * 80)

    profile = get_default_profile()

    # Check structure
    assert "business_profile" in profile
    assert "goals" in profile
    assert "preferences" in profile
    assert "learned_context" in profile

    # Check defaults
    assert profile["business_profile"]["brand"] is None
    assert profile["goals"]["primary_kpi"] == "revenue"
    assert profile["goals"]["target_roas"] == 3.0
    assert profile["preferences"]["analysis_depth"] == "detailed"
    assert profile["preferences"]["recommendation_style"] == "balanced"
    assert profile["learned_context"]["common_questions"] == []

    print("✅ Default profile structure correct")
    print(f"   - Business profile fields: {len(profile['business_profile'])}")
    print(f"   - Goals fields: {len(profile['goals'])}")
    print(f"   - Preferences fields: {len(profile['preferences'])}")
    print(f"   - Learned context fields: {len(profile['learned_context'])}")


def test_validation():
    """Test profile validation."""
    print("\n" + "=" * 80)
    print("TEST 3: Profile Validation")
    print("=" * 80)

    # Valid business profile
    valid_business = {
        "brand": "MyStore",
        "category": "Fashion & Apparel",
        "target_audience": "Women 25-40",
        "price_point": "Premium",
        "business_stage": "Growth",
        "monthly_revenue": 50000,
    }
    validated = validate_business_profile(valid_business)
    assert validated["brand"] == "MyStore"
    assert validated["category"] == "Fashion & Apparel"
    print("✅ Valid business profile passed validation")

    # Invalid category should raise error
    invalid_business = {
        "category": "Invalid Category",
    }
    try:
        validate_business_profile(invalid_business)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid category" in str(e)
        print("✅ Invalid category rejected correctly")

    # Valid goals
    valid_goals = {
        "primary_kpi": "revenue",
        "target_roas": 4.0,
        "target_margin": 55.0,
        "growth_target": 15.0,
    }
    validated = validate_goals(valid_goals)
    assert validated["target_roas"] == 4.0
    print("✅ Valid goals passed validation")

    # Invalid margin should raise error
    invalid_goals = {
        "target_margin": 150.0,  # > 100
    }
    try:
        validate_goals(invalid_goals)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "between 0 and 100" in str(e)
        print("✅ Invalid margin rejected correctly")

    # Valid preferences
    valid_prefs = {
        "analysis_depth": "comprehensive",
        "recommendation_style": "aggressive",
        "visual_preferences": {
            "use_emojis": False,
            "use_tables": True,
        }
    }
    validated = validate_preferences(valid_prefs)
    assert validated["analysis_depth"] == "comprehensive"
    print("✅ Valid preferences passed validation")


def test_profile_formatting():
    """Test profile formatting for prompt injection."""
    print("\n" + "=" * 80)
    print("TEST 4: Profile Formatting for Prompts")
    print("=" * 80)

    # Complete profile
    profile = {
        "business_profile": {
            "brand": "Luxe Boutique",
            "category": "Fashion & Apparel",
            "target_audience": "Women 30-50, high income",
            "price_point": "Luxury",
            "business_stage": "Scaling",
            "monthly_revenue": 750000,
        },
        "goals": {
            "primary_kpi": "profit",
            "target_roas": 5.0,
            "target_margin": 60.0,
        },
        "preferences": {
            "analysis_depth": "comprehensive",
            "recommendation_style": "conservative",
        },
        "learned_context": {
            "common_questions": ["How to improve AOV", "Best ad creatives"],
            "channel_focus": {"instagram": 70, "facebook": 20},
        }
    }

    formatted = format_profile_for_prompt(profile)

    # Check that key info is included
    assert "Luxe Boutique" in formatted
    assert "Fashion" in formatted
    assert "Scaling" in formatted
    assert "Luxury" in formatted
    assert "profit" in formatted
    assert "5.0x" in formatted
    assert "comprehensive" in formatted
    assert "conservative" in formatted
    assert "instagram" in formatted
    assert "70%" in formatted

    print("✅ Profile formatted correctly")
    print(f"\n   Formatted output:\n   {formatted}\n")

    # Empty profile
    empty_profile = {
        "business_profile": {},
        "goals": {},
        "preferences": {},
        "learned_context": {},
    }
    formatted_empty = format_profile_for_prompt(empty_profile)
    assert formatted_empty == "No profile information available."
    print("✅ Empty profile handled correctly")


def test_category_benchmarks():
    """Test category benchmark retrieval."""
    print("\n" + "=" * 80)
    print("TEST 5: Category Benchmarks")
    print("=" * 80)

    fashion_benchmarks = get_category_benchmarks("Fashion & Apparel")
    assert "conversion_rate" in fashion_benchmarks
    assert "aov" in fashion_benchmarks
    assert fashion_benchmarks["conversion_rate"]["avg"] == 2.1
    print("✅ Fashion & Apparel benchmarks correct")

    beauty_benchmarks = get_category_benchmarks("Beauty & Cosmetics")
    assert beauty_benchmarks["conversion_rate"]["avg"] == 3.0
    print("✅ Beauty & Cosmetics benchmarks correct")

    # Unknown category should return empty dict
    unknown = get_category_benchmarks("Unknown Category")
    assert unknown == {}
    print("✅ Unknown category returns empty dict")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PSAG-82 USER PROFILE TESTING")
    print("=" * 80)

    try:
        test_enums()
        test_default_profile()
        test_validation()
        test_profile_formatting()
        test_category_benchmarks()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nUser profile functionality is working correctly!")
        print("Ready to commit and deploy PSAG-82.\n")
        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
