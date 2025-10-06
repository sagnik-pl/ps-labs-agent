"""
Debug script to test a specific query with full error details.
"""
from workflow import create_agent_workflow
from langchain_core.messages import HumanMessage
import uuid
import traceback

def debug_query():
    """Test a specific query with detailed error reporting."""

    # Your query
    user_id = "Go3lWhYL9mYYf3ghVl4HEj5uSK42"
    query = "In the last 30 days look at the content with good reach. For those content - look at their captions. See if there is any commonality between their captions. I want to figure out if there is any correlation with captions and high reach"

    print("=" * 80)
    print("DEBUG MODE: Testing Query")
    print("=" * 80)
    print(f"\nUser ID: {user_id}")
    print(f"Query: {query}")
    print("\n" + "=" * 80)

    try:
        # Create workflow
        print("\n1. Creating workflow...")
        workflow = create_agent_workflow()
        print("✓ Workflow created")

        # Prepare state
        print("\n2. Preparing state...")
        test_state = {
            "user_id": user_id,
            "conversation_id": str(uuid.uuid4()),
            "query": query,
            "context": "Debug test",
            "messages": [HumanMessage(content=query)],
            "agent_results": {},
            "metadata": {},
            "needs_retry": False,
            "retry_count": 0,
            "interpretation_retry_count": 0,
            "sql_retry_count": 0,
        }
        print("✓ State prepared")

        # Run workflow
        print("\n3. Running workflow...\n")
        config = {"configurable": {"thread_id": test_state["conversation_id"]}}

        result = workflow.invoke(test_state, config=config)

        print("\n" + "=" * 80)
        print("✓ WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)

        # Show results
        print("\n📝 Generated SQL:")
        print(result.get("generated_sql", "N/A"))

        print("\n✅ SQL Validation:")
        sql_val = result.get("sql_validation", {})
        print(f"   Valid: {sql_val.get('is_valid', 'N/A')}")
        print(f"   Score: {sql_val.get('validation_score', 'N/A')}")
        if sql_val.get("feedback"):
            print(f"   Feedback: {sql_val.get('feedback')[:200]}")

        print("\n📊 SQL Retry Count:", result.get("sql_retry_count", 0))

        print("\n📈 Interpretation Retry Count:", result.get("interpretation_retry_count", 0))

        print("\n📝 Final Response (first 500 chars):")
        final_response = result.get("final_response", "N/A")
        print(final_response[:500] + "...")

        return True

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ ERROR OCCURRED")
        print("=" * 80)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("\nFull Traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)

        return False

if __name__ == "__main__":
    success = debug_query()

    print("\n" + "=" * 80)
    if success:
        print("✅ Query completed successfully")
    else:
        print("❌ Query failed - see error details above")
    print("=" * 80)
