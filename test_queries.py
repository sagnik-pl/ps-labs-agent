"""
Test script with various query types.
"""
from agents.supervisor_agent import SupervisorAgent
import uuid

def test_query(supervisor, query, user_id):
    """Test a single query."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    try:
        result = supervisor.process_query(query, user_id, "")
        print(f"\nAgent Used: {result.get('agent_used')}")
        print(f"\nResponse:\n{result['response']}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Photosphere Labs Agent System - Testing Suite")
    print("="*60)

    # Initialize
    print("\n1. Initializing supervisor (using OpenAI)...")
    supervisor = SupervisorAgent(use_anthropic=False)
    print("✅ Initialized\n")

    user_id = "test_user_001"

    # Test queries
    test_queries = [
        "What tables are available in my database?",
        "Show me the schema for the instagram_media table",
        "Get the first 10 rows from instagram_media table",
    ]

    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n🔍 Test {i}/{len(test_queries)}")
        success = test_query(supervisor, query, user_id)
        results.append(success)

    # Summary
    print("\n\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠️ Some tests failed")

if __name__ == "__main__":
    main()
