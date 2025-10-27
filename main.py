"""
Main entry point for the Photosphere Labs Agent System.
Simple CLI interface for testing.
"""
from workflow import create_agent_workflow
from langchain_core.messages import HumanMessage
from utils.firebase_client import firebase_client
import uuid


def main():
    """Main CLI interface for testing the agent system."""
    print("=" * 60)
    print("Photosphere Labs Agent System (LangGraph)")
    print("=" * 60)
    print("\nInitializing agent system...")

    # Initialize LangGraph workflow (using MemorySaver for now)
    # Note: FirestoreCheckpointer needs more methods implemented
    workflow = create_agent_workflow(checkpointer=None)  # Uses MemorySaver by default
    print("✓ Agent system initialized")

    # Get user ID
    user_id = input("\nEnter User ID (or press Enter for test_user): ").strip()
    if not user_id:
        user_id = "test_user"

    # Generate conversation ID
    conversation_id = str(uuid.uuid4())
    print(f"✓ Conversation ID: {conversation_id}")

    print("\n" + "=" * 60)
    print("Chat Interface (type 'exit' or 'quit' to end)")
    print("=" * 60 + "\n")

    # Chat loop
    while True:
        try:
            # Get user input
            query = input(f"\n[{user_id}] You: ").strip()

            if not query:
                continue

            if query.lower() in ["exit", "quit", "q"]:
                print("\nExiting chat...")
                break

            # Get conversation context from Firestore
            try:
                context = firebase_client.get_context_summary(user_id, conversation_id)
            except Exception as e:
                print(f"Warning: Could not load context from Firestore: {e}")
                context = ""

            # Save user message to Firestore
            try:
                firebase_client.save_message(
                    user_id, conversation_id, "user", query
                )
            except Exception as e:
                print(f"Warning: Could not save message to Firestore: {e}")

            # Prepare state for LangGraph workflow
            initial_state = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "query": query,
                "context": context,
                "messages": [HumanMessage(content=query)],
                "agent_results": {},
                "metadata": {},
                "needs_retry": False,
                "retry_count": 0,
                "interpretation_retry_count": 0,
                "sql_retry_count": 0,
            }

            # Process query with LangGraph workflow
            print("\n[Agent] 🤔 Planning Task...")

            # Configure for checkpointing
            config = {
                "configurable": {
                    "thread_id": conversation_id
                }
            }

            try:
                result = workflow.invoke(initial_state, config=config)
            except Exception as workflow_error:
                print(f"\n[Workflow Error] {str(workflow_error)}")
                print("\nFull traceback:")
                import traceback
                traceback.print_exc()
                continue

            # Extract final response
            final_response = result.get("final_response", "No response generated")

            # Display response
            print(f"\n[Agent] {final_response}")

            # Show metadata in verbose mode
            metadata = result.get("metadata", {})
            if metadata:
                routing = metadata.get("routing")
                if routing:
                    print(f"\n[Metadata] Query Type: {routing.get('query_type', 'data_analytics')}")
                    print(f"[Metadata] Workflow Path: {routing.get('workflow_path', 'sql_pipeline')}")
                    print(f"[Metadata] Reasoning: {routing.get('reasoning')}")

            # Save agent response to Firestore
            try:
                firebase_client.save_message(
                    user_id,
                    conversation_id,
                    "assistant",
                    final_response,
                    metadata=metadata,
                )
            except Exception as e:
                print(f"Warning: Could not save response to Firestore: {e}")

        except KeyboardInterrupt:
            print("\n\nExiting chat...")
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")
            print("\n[Error Details]")
            import traceback
            traceback.print_exc()

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
