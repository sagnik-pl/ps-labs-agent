#!/usr/bin/env python3
"""
Test script to directly query Firestore and check message persistence.
This will show us exactly what messages are stored and their conversation grouping.
"""
import os
import sys

# Set environment to production BEFORE importing anything
os.environ['ENVIRONMENT'] = 'production'

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Query Firestore and display all conversations and messages for the test user."""

    # Import Firebase client - this will initialize the app
    from utils.firebase_client import FirebaseClient

    # Get Firebase client instance
    fb_client = FirebaseClient()
    db = fb_client.db

    # Test user ID from the logs
    user_id = "45up1lHMF2N4SwAJc6iMEOdLg9y1"

    print(f"\n{'='*80}")
    print(f"FIRESTORE MESSAGE PERSISTENCE TEST")
    print(f"{'='*80}\n")
    print(f"User ID: {user_id}\n")

    try:
        # Get the user document
        user_ref = db.collection("conversations").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            print(f"❌ No user document found for {user_id}")
            return

        print(f"✅ User document exists\n")

        # Get all conversations (sub-collections under chats)
        chats_ref = user_ref.collection("chats")
        conversations = chats_ref.stream()

        conv_count = 0
        total_messages = 0

        for conv_doc in conversations:
            conv_count += 1
            conv_id = conv_doc.id
            conv_data = conv_doc.to_dict()

            print(f"\n{'-'*80}")
            print(f"CONVERSATION #{conv_count}")
            print(f"{'-'*80}")
            print(f"Conv ID: {conv_id}")
            print(f"Title: {conv_data.get('title', 'N/A')}")
            print(f"Date: {conv_data.get('date', 'N/A')}")
            print(f"Created: {conv_data.get('created_at', 'N/A')}")
            print(f"Updated: {conv_data.get('updated_at', 'N/A')}")

            # Get messages for this conversation
            messages_ref = chats_ref.document(conv_id).collection("messages")
            messages = messages_ref.order_by("timestamp").stream()

            msg_count = 0
            print(f"\nMESSAGES:")
            print(f"{'-'*80}")

            for msg_doc in messages:
                msg_count += 1
                total_messages += 1
                msg_data = msg_doc.to_dict()

                role = msg_data.get('role', 'unknown')
                # Check if message is encrypted
                is_encrypted = msg_data.get('encrypted', False)

                if is_encrypted:
                    content = f"[ENCRYPTED - {len(msg_data.get('content', ''))} bytes]"
                else:
                    content = msg_data.get('content', 'N/A')

                timestamp = msg_data.get('timestamp', 'N/A')

                print(f"\n  Message {msg_count}:")
                print(f"  - Role: {role}")
                print(f"  - Content: {content[:100]}..." if len(str(content)) > 100 else f"  - Content: {content}")
                print(f"  - Encrypted: {is_encrypted}")
                print(f"  - Timestamp: {timestamp}")
                print(f"  - Metadata: {msg_data.get('metadata', {})}")

            print(f"\n  Total messages in this conversation: {msg_count}")

        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total conversations: {conv_count}")
        print(f"Total messages: {total_messages}")
        print(f"{'='*80}\n")

        if conv_count == 0:
            print("⚠️  WARNING: No conversations found!")
            print("This means either:")
            print("  1. Messages are not being saved to Firestore")
            print("  2. User ID is incorrect")
            print("  3. Firestore structure is different than expected")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
