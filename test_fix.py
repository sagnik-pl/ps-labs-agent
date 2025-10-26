#!/usr/bin/env python3
"""Quick test for the false positive fix."""
import asyncio
import websockets
import json
import uuid
import ssl

BACKEND_URL = "ps-labs-agent-backend-production.up.railway.app"
WS_URL = f"wss://{BACKEND_URL}"
TEST_USER_ID = "45up1lHMF2N4SwAJc6iMEOdLg9y1"

async def test_query(query):
    conversation_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    ws_url = f"{WS_URL}/ws/{TEST_USER_ID}/{session_id}"

    print(f"\n{'='*80}")
    print(f"Testing query: '{query}'")
    print(f"{'='*80}\n")

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps({
            "type": "query",
            "query": query,
            "conversation_id": conversation_id
        }))

        completed = False
        while not completed:
            message = await asyncio.wait_for(websocket.recv(), timeout=60)
            data = json.loads(message)

            msg_type = data.get("type")
            print(f"[{msg_type}]", end=" ")

            if msg_type == "completed":
                completed_data = data.get("data", {})
                final_response = completed_data.get("response", "")
                metadata = completed_data.get("metadata", {})

                print(f"\n\n{'='*80}")
                print("FINAL RESPONSE:")
                print(f"{'='*80}")
                print(final_response)
                print(f"{'='*80}\n")

                # Check execution plan
                if metadata and "execution_plan" in metadata:
                    plan_type = metadata["execution_plan"].get("type")
                    print(f"Execution Plan Type: {plan_type}")

                    # Verify it's NOT a data_inquiry (which would be wrong for actual data requests)
                    if plan_type == "data_inquiry":
                        print("❌ FAIL: Query was incorrectly treated as data inquiry!")
                    elif plan_type == "data_analytics":
                        print("✅ PASS: Query was correctly treated as data analytics request!")
                    else:
                        print(f"⚠️  Unexpected plan type: {plan_type}")

                completed = True

async def main():
    # Test cases
    test_cases = [
        ("What are my follower demographics?", "Should execute SQL query"),
        ("hi", "Should return greeting"),
        ("what data do you have on Instagram?", "Should list available data"),
        ("do you have demographic data?", "Should ask for platform clarification")
    ]

    for query, expected in test_cases:
        print(f"\n\nTest: {expected}")
        await test_query(query)
        await asyncio.sleep(2)  # Small delay between tests

if __name__ == "__main__":
    asyncio.run(main())
