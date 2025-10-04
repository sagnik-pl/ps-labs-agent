"""
Simple test script for the agent system.
"""
from agents.supervisor_agent import SupervisorAgent
import uuid

def main():
    print("=" * 60)
    print("Testing Photosphere Labs Agent System")
    print("=" * 60)

    # Initialize supervisor
    print("\n1. Initializing supervisor agent...")
    try:
        supervisor = SupervisorAgent(use_anthropic=False)  # Use OpenAI
        print("✅ Supervisor initialized")
    except Exception as e:
        print(f"❌ Error initializing supervisor: {e}")
        return

    # Test data analytics routing
    print("\n2. Testing query routing...")
    test_query = "What tables are available in my database?"
    user_id = "test_user"
    conversation_id = str(uuid.uuid4())

    try:
        result = supervisor.process_query(test_query, user_id, "")
        print(f"✅ Query processed")
        print(f"   Agent used: {result.get('agent_used')}")
        print(f"   Response preview: {result['response'][:200]}...")
    except Exception as e:
        print(f"❌ Error processing query: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
