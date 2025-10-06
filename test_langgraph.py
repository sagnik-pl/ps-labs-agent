"""
Test script for LangGraph workflow.
"""
from workflow import create_agent_workflow
from langchain_core.messages import HumanMessage
import uuid

def test_workflow():
    """Test the LangGraph workflow with a simple query."""
    print("=" * 60)
    print("Testing LangGraph Workflow")
    print("=" * 60)

    # Create workflow (without Firestore for simple testing)
    print("\n1. Creating workflow...")
    workflow = create_agent_workflow()
    print("✓ Workflow created")

    # Prepare test state
    print("\n2. Preparing test state...")
    test_state = {
        "user_id": "45up1lHMF2N4SwAJc6iMEOdLg9y1",
        "conversation_id": str(uuid.uuid4()),
        "query": "What are my top 5 Instagram posts by engagement?",
        "context": "Testing the new LangGraph system with e-commerce interpretation",
        "messages": [HumanMessage(content="What are my top 5 Instagram posts by engagement?")],
        "agent_results": {},
        "metadata": {},
        "needs_retry": False,
        "retry_count": 0,
        "interpretation_retry_count": 0,
    }
    print("✓ Test state prepared")

    # Run workflow
    print("\n3. Running workflow...")
    print("-" * 60)
    try:
        # Configure for checkpointing
        config = {
            "configurable": {
                "thread_id": test_state["conversation_id"]
            }
        }
        result = workflow.invoke(test_state, config=config)
        print("-" * 60)
        print("\n✓ Workflow completed successfully!")

        # Display results
        print("\n4. Results:")
        print(f"   Final Response: {result.get('final_response', 'N/A')[:200]}...")
        print(f"   Agent Used: {result.get('current_agent', 'N/A')}")
        print(f"   Plan: {result.get('plan', {}).get('reasoning', 'N/A')}")

        return True
    except Exception as e:
        print("-" * 60)
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_workflow()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Tests failed")
    print("=" * 60)
