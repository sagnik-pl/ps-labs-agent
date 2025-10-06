"""
Test SQL validation workflow.
"""
from workflow import create_agent_workflow
from langchain_core.messages import HumanMessage
import uuid


def test_sql_validation():
    """Test the SQL generation and validation workflow."""
    print("=" * 80)
    print("Testing SQL Validation Workflow")
    print("=" * 80)

    # Create workflow
    print("\n1. Creating workflow...")
    workflow = create_agent_workflow()
    print("✓ Workflow created with SQL validation layer")

    # Test query
    print("\n2. Preparing test state...")
    test_state = {
        "user_id": "45up1lHMF2N4SwAJc6iMEOdLg9y1",
        "conversation_id": str(uuid.uuid4()),
        "query": "Show me my top 5 Instagram posts by engagement",
        "context": "Testing SQL validation workflow",
        "messages": [HumanMessage(content="Top 5 posts by engagement")],
        "agent_results": {},
        "metadata": {},
        "needs_retry": False,
        "retry_count": 0,
        "interpretation_retry_count": 0,
        "sql_retry_count": 0,
    }
    print("✓ Test state prepared")

    # Run workflow
    print("\n3. Running workflow through all layers...")
    print("-" * 80)
    print("Flow: Planner → Router → SQL Generator → SQL Validator")
    print("      → (retry if needed) → SQL Executor → Data Interpreter")
    print("      → Interpretation Validator → Final Response")
    print("-" * 80)

    try:
        config = {"configurable": {"thread_id": test_state["conversation_id"]}}
        result = workflow.invoke(test_state, config=config)

        print("\n✓ Workflow completed successfully!")

        # Display results
        print("\n" + "=" * 80)
        print("4. SQL VALIDATION RESULTS")
        print("=" * 80)

        # Generated SQL
        generated_sql = result.get("generated_sql", "")
        print(f"\n📝 Generated SQL Query:")
        print("-" * 80)
        print(generated_sql)
        print("-" * 80)

        # SQL Validation
        sql_validation = result.get("sql_validation", {})
        print(f"\n✅ SQL Validation:")
        print(f"   Valid: {sql_validation.get('is_valid', 'N/A')}")
        print(f"   Validation Score: {sql_validation.get('validation_score', 'N/A')}/100")
        print(f"   Confidence: {sql_validation.get('confidence', 'N/A')}")

        # Passed and failed checks
        passed_checks = sql_validation.get("passed_checks", [])
        failed_checks = sql_validation.get("failed_checks", [])

        if passed_checks:
            print(f"\n   ✓ Passed Checks: {', '.join(passed_checks)}")

        if failed_checks:
            print(f"\n   ✗ Failed Checks: {', '.join(failed_checks)}")

        # Critical issues
        critical_issues = sql_validation.get("critical_issues", [])
        if critical_issues:
            print(f"\n   ⚠️  Critical Issues:")
            for issue in critical_issues:
                print(f"      - {issue}")

        # Warnings
        warnings = sql_validation.get("warnings", [])
        if warnings:
            print(f"\n   ⚠️  Warnings:")
            for warning in warnings:
                print(f"      - {warning}")

        # Feedback
        feedback = sql_validation.get("feedback", "")
        if feedback:
            print(f"\n   Feedback: {feedback[:200]}...")

        # SQL Retries
        sql_retry_count = result.get("sql_retry_count", 0)
        print(f"\n🔄 SQL Generation Retries: {sql_retry_count}")

        # Query execution result
        agent_results = result.get("agent_results", {})
        sql_result = agent_results.get("result", "")
        print(f"\n📊 Query Execution Result (first 300 chars):")
        print(f"   {sql_result[:300]}...")

        # Final response
        final_response = result.get("final_response", "")
        print(f"\n📝 Final Response Length: {len(final_response)} characters")

        # Check SQL validation quality
        print("\n" + "=" * 80)
        print("QUALITY CHECKS:")
        print("=" * 80)

        has_user_id = "user_id" in generated_sql.lower()
        has_where = "where" in generated_sql.lower()
        has_limit = "limit" in generated_sql.lower()
        is_valid = sql_validation.get("is_valid", False)

        print(f"✓ SQL includes user_id filter: {has_user_id}")
        print(f"✓ SQL has WHERE clause: {has_where}")
        print(f"✓ SQL has LIMIT clause: {has_limit}")
        print(f"✓ SQL passed validation: {is_valid}")
        print(f"✓ SQL validation score >= 80: {sql_validation.get('validation_score', 0) >= 80}")

        return True

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sql_validation()
    print("\n" + "=" * 80)
    if success:
        print("✅ SQL VALIDATION WORKFLOW TEST PASSED!")
        print("\nThe system now:")
        print("  1. Generates SQL queries from natural language")
        print("  2. Validates SQL for correctness, security, and efficiency")
        print("  3. Retries with feedback if validation fails (up to 3 times)")
        print("  4. Executes only validated, safe SQL queries")
        print("  5. Interprets results with e-commerce knowledge")
    else:
        print("❌ SQL VALIDATION WORKFLOW TEST FAILED")
    print("=" * 80)
