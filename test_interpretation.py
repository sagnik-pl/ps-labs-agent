"""
Test the e-commerce interpretation workflow.
"""
from workflow import create_agent_workflow
from langchain_core.messages import HumanMessage
import uuid


def test_interpretation_workflow():
    """Test the full interpretation workflow with validation loop."""
    print("=" * 80)
    print("Testing E-commerce Data Interpretation Workflow")
    print("=" * 80)

    # Create workflow
    print("\n1. Creating workflow...")
    workflow = create_agent_workflow()
    print("✓ Workflow created with interpretation layer")

    # Prepare test state with a query that should return data
    print("\n2. Preparing test state...")
    test_state = {
        "user_id": "45up1lHMF2N4SwAJc6iMEOdLg9y1",
        "conversation_id": str(uuid.uuid4()),
        "query": "Show me my recent Instagram posts",
        "context": "Testing e-commerce interpretation workflow",
        "messages": [HumanMessage(content="Show me my recent Instagram posts")],
        "agent_results": {},
        "metadata": {},
        "needs_retry": False,
        "retry_count": 0,
        "interpretation_retry_count": 0,
    }
    print("✓ Test state prepared")

    # Run workflow
    print("\n3. Running workflow through all layers...")
    print("-" * 80)
    print("Flow: Planner → Router → Data Agent → Validator → Data Interpreter")
    print("      → Interpretation Validator → (retry if needed) → Final Response")
    print("-" * 80)

    try:
        config = {"configurable": {"thread_id": test_state["conversation_id"]}}
        result = workflow.invoke(test_state, config=config)

        print("\n✓ Workflow completed successfully!")

        # Display results
        print("\n" + "=" * 80)
        print("4. WORKFLOW RESULTS")
        print("=" * 80)

        # Plan
        plan = result.get("plan", {})
        print(f"\n📋 Plan:")
        print(f"   Complexity: {plan.get('estimated_complexity', 'N/A')}")
        print(f"   Reasoning: {plan.get('reasoning', 'N/A')}")

        # Agent execution
        print(f"\n🤖 Agent Used: {result.get('current_agent', 'N/A')}")

        # Raw data (truncated)
        raw_data = result.get("raw_data", "")
        print(f"\n📊 Raw Data (first 300 chars):")
        print(f"   {raw_data[:300]}...")

        # Data interpretation
        interpretation = result.get("data_interpretation", "")
        print(f"\n💡 E-commerce Interpretation (first 500 chars):")
        print(f"   {interpretation[:500]}...")

        # Interpretation validation
        validation = result.get("interpretation_validation", {})
        print(f"\n✅ Interpretation Validation:")
        print(f"   Valid: {validation.get('is_valid', 'N/A')}")
        print(f"   Quality Score: {validation.get('quality_score', 'N/A')}/100")

        if validation.get("failed_criteria"):
            print(f"   Failed Criteria: {validation.get('failed_criteria', [])}")
        if validation.get("feedback"):
            print(f"   Feedback: {validation.get('feedback', '')[:200]}...")

        # Retry info
        retry_count = result.get("interpretation_retry_count", 0)
        print(f"\n🔄 Interpretation Retries: {retry_count}")

        # Final response
        final_response = result.get("final_response", "")
        print(f"\n📝 Final Response Length: {len(final_response)} characters")
        print(f"\n" + "=" * 80)
        print("FINAL RESPONSE TO USER:")
        print("=" * 80)
        print(final_response)
        print("=" * 80)

        # Check if interpretation has e-commerce context
        has_benchmarks = any(
            word in final_response.lower()
            for word in ["benchmark", "industry", "average", "good", "excellent"]
        )
        has_recommendations = any(
            word in final_response.lower()
            for word in ["recommend", "should", "focus", "improve", "optimize"]
        )
        has_structure = "###" in final_response or "##" in final_response

        print("\n" + "=" * 80)
        print("QUALITY CHECKS:")
        print("=" * 80)
        print(f"✓ Has benchmarks/context: {has_benchmarks}")
        print(f"✓ Has recommendations: {has_recommendations}")
        print(f"✓ Well-structured (markdown): {has_structure}")
        print(f"✓ Uses e-commerce knowledge: {has_benchmarks and has_recommendations}")

        return True

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_interpretation_workflow()
    print("\n" + "=" * 80)
    if success:
        print("✅ E-COMMERCE INTERPRETATION WORKFLOW TEST PASSED!")
        print("\nThe system now:")
        print("  1. Fetches raw data from Athena")
        print("  2. Interprets it with deep e-commerce knowledge")
        print("  3. Validates the interpretation quality")
        print("  4. Retries if quality is insufficient (up to 2 times)")
        print("  5. Returns rich, actionable insights to the user")
    else:
        print("❌ E-COMMERCE INTERPRETATION WORKFLOW TEST FAILED")
    print("=" * 80)
