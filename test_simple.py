#!/usr/bin/env python3
import asyncio
import websockets
import json
import uuid
import ssl

BACKEND_URL = "ps-labs-agent-backend-production.up.railway.app"
WS_URL = f"wss://{BACKEND_URL}"
TEST_USER_ID = "45up1lHMF2N4SwAJc6iMEOdLg9y1"

async def test_query():
    conversation_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    ws_url = f"{WS_URL}/ws/{TEST_USER_ID}/{session_id}"
    
    print(f"Testing query: 'Hows snap?'")
    print(f"Connecting to: {ws_url}\n")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
        print("✅ Connected!\n")
        
        await websocket.send(json.dumps({
            "type": "query",
            "query": "Hows snap?",
            "conversation_id": conversation_id
        }))
        print("Sent query\n")
        
        completed = False
        while not completed:
            message = await asyncio.wait_for(websocket.recv(), timeout=60)
            data = json.loads(message)
            
            msg_type = data.get("type")
            print(f"Received: {msg_type}")
            
            if msg_type == "completed":
                # Parse using the fixed structure (data.data.response)
                completed_data = data.get("data", {})
                final_response = completed_data.get("response", "")
                metadata = completed_data.get("metadata", {})
                
                print(f"\n{'='*80}")
                print(f"FINAL RESPONSE ({len(final_response)} chars):")
                print(f"{'='*80}")
                print(final_response)
                print(f"{'='*80}\n")
                
                if metadata:
                    print(f"Metadata: {json.dumps(metadata, indent=2)}\n")
                
                completed = True

if __name__ == "__main__":
    asyncio.run(test_query())
