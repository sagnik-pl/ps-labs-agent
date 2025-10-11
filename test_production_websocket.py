"""
Test WebSocket connection and Firestore message saving in production.
"""
import asyncio
import websockets
import json
import uuid
import requests
import ssl
from datetime import datetime

# Production backend URL
BACKEND_URL = "ps-labs-agent-backend-production.up.railway.app"
WS_URL = f"wss://{BACKEND_URL}"
HTTP_URL = f"https://{BACKEND_URL}"

# Test user
TEST_USER_ID = "test_user_" + str(uuid.uuid4())[:8]
TEST_CONVERSATION_ID = str(uuid.uuid4())


async def test_websocket_and_firestore():
    """Test end-to-end WebSocket query and Firestore saving."""
    print("=" * 80)
    print(f"Testing WebSocket and Firestore Integration")
    print(f"User ID: {TEST_USER_ID}")
    print(f"Conversation ID: {TEST_CONVERSATION_ID}")
    print("=" * 80)

    # Step 1: Verify no conversations exist yet
    print(f"\n1. Checking initial conversations for user...")
    response = requests.get(f"{HTTP_URL}/conversations/{TEST_USER_ID}")
    initial_conversations = response.json()
    print(f"   Initial conversations: {initial_conversations['count']}")
    assert initial_conversations['count'] == 0, "User should have no conversations initially"

    # Step 2: Connect to WebSocket and send a query
    print(f"\n2. Connecting to WebSocket...")
    ws_url = f"{WS_URL}/ws/{TEST_USER_ID}/{TEST_CONVERSATION_ID}"
    print(f"   URL: {ws_url}")

    try:
        # Create SSL context that doesn't verify certificates (for testing only)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
            print(f"   ✅ Connected successfully")

            # Send test query
            test_query = "What is 2+2?"  # Simple test query
            print(f"\n3. Sending test query: '{test_query}'")

            await websocket.send(json.dumps({
                "type": "query",
                "query": test_query,
                "conversation_id": TEST_CONVERSATION_ID
            }))

            print(f"   ✅ Query sent")

            # Receive progress updates
            print(f"\n4. Receiving progress updates...")
            messages_received = 0
            completed = False

            while not completed and messages_received < 20:  # Max 20 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30)
                    data = json.loads(message)

                    msg_type = data.get("type")
                    messages_received += 1

                    if msg_type == "started":
                        print(f"   📝 Started processing query")
                    elif msg_type == "progress":
                        node = data.get("node", "unknown")
                        progress = data.get("progress", 0)
                        print(f"   ⏳ Progress: {progress}% - {node}")
                    elif msg_type == "completed":
                        print(f"   ✅ Completed!")
                        response_text = data.get("response", "")
                        print(f"   Response preview: {response_text[:100]}...")
                        completed = True
                    elif msg_type == "error":
                        print(f"   ❌ Error: {data.get('error')}")
                        break

                except asyncio.TimeoutError:
                    print(f"   ⚠️  Timeout waiting for message")
                    break

            print(f"\n   Total messages received: {messages_received}")

            if not completed:
                print(f"   ⚠️  Warning: Did not receive completion message")

    except Exception as e:
        print(f"   ❌ WebSocket connection failed: {e}")
        return False

    # Step 3: Wait for Firestore to save
    print(f"\n5. Waiting 2 seconds for Firestore to save...")
    await asyncio.sleep(2)

    # Step 4: Verify conversation was saved to Firestore
    print(f"\n6. Checking if conversation was saved to Firestore...")
    response = requests.get(f"{HTTP_URL}/conversations/{TEST_USER_ID}")
    final_conversations = response.json()
    print(f"   Conversations found: {final_conversations['count']}")

    if final_conversations['count'] > 0:
        print(f"   ✅ SUCCESS! Conversation was saved to Firestore")
        print(f"\n   Conversation details:")
        for conv in final_conversations['conversations']:
            print(f"      - Title: {conv.get('title')}")
            print(f"      - Message count: {conv.get('message_count')}")
            print(f"      - Created: {conv.get('created_at')}")

        # Step 5: Get messages
        print(f"\n7. Fetching messages from conversation...")
        response = requests.get(
            f"{HTTP_URL}/conversations/{TEST_USER_ID}/{TEST_CONVERSATION_ID}/messages"
        )
        messages = response.json()
        print(f"   Messages found: {messages['count']}")

        for msg in messages.get('messages', []):
            print(f"      - [{msg['role']}]: {msg['content'][:100]}...")

        return True
    else:
        print(f"   ❌ FAILURE! Conversation was NOT saved to Firestore")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_websocket_and_firestore())

    print("\n" + "=" * 80)
    if result:
        print("✅ TEST PASSED: WebSocket and Firestore are working correctly!")
    else:
        print("❌ TEST FAILED: Firestore is not saving messages")
    print("=" * 80)
