#!/usr/bin/env python3
"""
Simple debug WebSocket script - shows ALL raw messages.
"""
import asyncio
import websockets
import json
import uuid
import ssl

# Production backend URLs
BACKEND_URL = "ps-labs-agent-backend-production.up.railway.app"
WS_URL = f"wss://{BACKEND_URL}"

# Test user ID
TEST_USER_ID = "45up1lHMF2N4SwAJc6iMEOdLg9y1"


async def test_query(query: str):
    """Send a query and print ALL raw messages."""

    conversation_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    ws_url = f"{WS_URL}/ws/{TEST_USER_ID}/{session_id}"

    print(f"=" * 80)
    print(f"Query: {query}")
    print(f"Conversation ID: {conversation_id[:12]}...")
    print(f"=" * 80)

    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
            print("✅ Connected!\n")

            # Send query
            await websocket.send(json.dumps({
                "type": "query",
                "query": query,
                "conversation_id": conversation_id
            }))
            print(f"Sent query\n")

            # Receive ALL messages
            message_count = 0
            completed = False

            while not completed and message_count < 50:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(message)
                    message_count += 1

                    print(f"\n--- MESSAGE {message_count} ---")
                    print(json.dumps(data, indent=2))

                    if data.get("type") == "completed":
                        completed = True
                        print("\n✅ COMPLETED EVENT RECEIVED")

                except asyncio.TimeoutError:
                    print("\n❌ Timeout")
                    break

            print(f"\n{'-'*80}")
            print(f"Total messages received: {message_count}")
            print(f"{'-'*80}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    query = input("Enter test query: ")
    asyncio.run(test_query(query))
