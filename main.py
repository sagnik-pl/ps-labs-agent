"""
Main entry point for the Photosphere Labs Agent System.
Simple CLI interface for testing.
"""
from agents.supervisor_agent import SupervisorAgent
from utils.firebase_client import firebase_client
import uuid


def main():
    """Main CLI interface for testing the agent system."""
    print("=" * 60)
    print("Photosphere Labs Agent System")
    print("=" * 60)
    print("\nInitializing agent system...")

    # Initialize supervisor agent (using Claude by default)
    supervisor = SupervisorAgent(use_anthropic=True)
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

            # Process query with supervisor agent
            print("\n[Agent] Processing...")
            result = supervisor.process_query(query, user_id, context)

            # Display response
            print(f"\n[Agent] {result['response']}")

            # Show metadata in verbose mode
            if result.get("agent_used"):
                print(f"\n[Metadata] Agent used: {result['agent_used']}")
                print(f"[Metadata] Routing: {result['routing_decision']['reasoning']}")

            # Save agent response to Firestore
            try:
                firebase_client.save_message(
                    user_id,
                    conversation_id,
                    "assistant",
                    result["response"],
                    metadata=result.get("routing_decision"),
                )
            except Exception as e:
                print(f"Warning: Could not save response to Firestore: {e}")

        except KeyboardInterrupt:
            print("\n\nExiting chat...")
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}")

    print("\nGoodbye!")


if __name__ == "__main__":
    main()
