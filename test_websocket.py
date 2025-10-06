"""
Test WebSocket API client.
"""
import asyncio
import websockets
import json


async def test_websocket():
    """Test the WebSocket connection and query processing."""

    user_id = "test_user"
    session_id = "test_session_123"
    uri = f"ws://localhost:8000/ws/{user_id}/{session_id}"

    print("=" * 60)
    print("WebSocket Test Client")
    print("=" * 60)
    print(f"\nConnecting to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully")

            # Send a test query
            query = "Show me my top 5 Instagram posts by engagement in the last 30 days"

            message = {
                "type": "query",
                "query": query,
                "conversation_id": session_id
            }

            print(f"\n📤 Sending query: {query}")
            await websocket.send(json.dumps(message))
            print("✓ Query sent")

            print("\n📥 Receiving messages...\n")
            print("-" * 60)

            # Receive messages
            while True:
                try:
                    response = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=120.0  # 2 minute timeout
                    )

                    data = json.loads(response)
                    event_type = data.get("type")
                    timestamp = data.get("timestamp", "")
                    event_data = data.get("data", {})

                    if event_type == "started":
                        print(f"🚀 Started: {event_data.get('message')}")
                        print(f"   Query: {event_data.get('query')}")

                    elif event_type == "progress":
                        message = event_data.get("message")
                        progress = event_data.get("progress", 0)
                        print(f"⏳ Progress [{progress}%]: {message}")

                        description = event_data.get("description")
                        if description:
                            print(f"   {description}")

                    elif event_type == "data_chunk":
                        chunk = event_data.get("chunk", "")
                        print(f"📝 Chunk: {chunk[:100]}...")

                    elif event_type == "completed":
                        print(f"\n✅ Completed: {event_data.get('message')}")
                        response_text = event_data.get("response", "")
                        print(f"\n📊 Response:\n{response_text[:500]}...")

                        metadata = event_data.get("metadata", {})
                        if metadata:
                            print(f"\n📈 Metadata:")
                            for key, value in metadata.items():
                                print(f"   {key}: {value}")

                        # Done - exit loop
                        break

                    elif event_type == "error":
                        print(f"\n❌ Error: {event_data.get('error')}")
                        details = event_data.get("details")
                        if details:
                            print(f"\n   Details:\n{details}")
                        break

                    elif event_type == "pong":
                        print("🏓 Pong received")

                except asyncio.TimeoutError:
                    print("\n⏰ Timeout waiting for response")
                    break

            print("\n" + "-" * 60)
            print("✓ Test completed")

    except ConnectionRefusedError:
        print("\n❌ Connection refused. Is the server running?")
        print("\nStart the server with:")
        print("  python api_websocket.py")
        print("  or")
        print("  uvicorn api_websocket:app --reload --host 0.0.0.0 --port 8000")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_ping():
    """Test ping/pong keep-alive."""
    user_id = "test_user"
    session_id = "ping_test"
    uri = f"ws://localhost:8000/ws/{user_id}/{session_id}"

    print("\n" + "=" * 60)
    print("Testing Ping/Pong")
    print("=" * 60)

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected")

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent ping")

            # Wait for pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") == "pong":
                print("✓ Received pong - keep-alive working!")
            else:
                print(f"❌ Unexpected response: {data}")

    except Exception as e:
        print(f"❌ Ping test failed: {e}")


if __name__ == "__main__":
    print("\n🧪 WebSocket API Test Suite\n")

    # Test ping/pong first
    asyncio.run(test_ping())

    print("\n")

    # Test full query workflow
    asyncio.run(test_websocket())

    print("\n" + "=" * 60)
    print("All tests completed")
    print("=" * 60)
