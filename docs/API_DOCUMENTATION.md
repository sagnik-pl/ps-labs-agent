# WebSocket API Documentation

## Base URL

```
WebSocket: ws://localhost:8000/ws/{user_id}/{session_id}
REST API: http://localhost:8000
```

For production, replace `localhost:8000` with your deployed backend URL.

---

## WebSocket Connection

### Connect to Chat

**Endpoint:** `ws://localhost:8000/ws/{user_id}/{session_id}`

**Path Parameters:**
- `user_id` (string): Authenticated user's ID
- `session_id` (string): Unique session/conversation ID (generate with UUID)

**Example (JavaScript):**
```javascript
const userId = "user123";
const sessionId = "conv-" + crypto.randomUUID();
const ws = new WebSocket(`ws://localhost:8000/ws/${userId}/${sessionId}`);

ws.onopen = () => {
  console.log("Connected to chat");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleMessage(data);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from chat");
};
```

---

## WebSocket Message Types

### Client → Server Messages

#### 1. Send Query

Send a user query to the agent system.

**Message Format:**
```json
{
  "type": "query",
  "query": "Show me my top Instagram posts by engagement",
  "conversation_id": "conv-uuid-here"
}
```

**Fields:**
- `type`: Always `"query"`
- `query`: The user's natural language question
- `conversation_id`: Conversation ID (same as WebSocket path param)

**Example (JavaScript):**
```javascript
ws.send(JSON.stringify({
  type: "query",
  query: "Show me my top Instagram posts by engagement",
  conversation_id: sessionId
}));
```

#### 2. Ping (Keep-Alive)

Send periodic pings to keep the connection alive.

**Message Format:**
```json
{
  "type": "ping"
}
```

**Example:**
```javascript
// Send ping every 30 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
}, 30000);
```

---

### Server → Client Messages

All server messages follow this structure:

```json
{
  "type": "event_type",
  "timestamp": "2025-10-06T12:34:56.789Z",
  "data": {
    // Event-specific data
  }
}
```

#### 1. Started Event

Sent when query processing begins.

**Message Format:**
```json
{
  "type": "started",
  "timestamp": "2025-10-06T12:34:56.789Z",
  "data": {
    "message": "Planning Task...",
    "query": "Show me my top Instagram posts",
    "progress": 0
  }
}
```

**Usage:**
```javascript
if (data.type === "started") {
  showStatus(data.data.message);
  setProgress(data.data.progress);
}
```

#### 2. Progress Event

Sent as the workflow moves through different stages.

**Message Format:**
```json
{
  "type": "progress",
  "timestamp": "2025-10-06T12:34:58.123Z",
  "data": {
    "message": "Fetching Data...",
    "description": "Retrieving your data",
    "progress": 50,
    "stage": "sql_executor"
  }
}
```

**Fields:**
- `message`: User-friendly status message
- `description`: Detailed description of current stage
- `progress`: Percentage (0-100)
- `stage`: Internal node name (for debugging)

**Progress Messages:**
- "Planning Task..." (0-15%)
- "Fetching Data..." (30-50%)
- "Validating Data..." (40%)
- "Interpreting Data..." (75-85%)
- "Finalizing Response..." (95%)

**Usage:**
```javascript
if (data.type === "progress") {
  updateProgressBar(data.data.progress);
  showStatus(data.data.message);
}
```

#### 3. Completed Event

Sent when processing is complete.

**Message Format:**
```json
{
  "type": "completed",
  "timestamp": "2025-10-06T12:35:02.456Z",
  "data": {
    "message": "Complete!",
    "response": "Here are your top Instagram posts...",
    "progress": 100,
    "metadata": {
      "routing": {
        "primary_agent": "data_analytics",
        "reasoning": "..."
      },
      "sql_retry_count": 0,
      "interpretation_retry_count": 0
    }
  }
}
```

**Fields:**
- `response`: The final agent response (display this to user)
- `metadata`: Additional information about processing

**Usage:**
```javascript
if (data.type === "completed") {
  hideProgressBar();
  displayResponse(data.data.response);
  saveToConversation(data.data.response);
}
```

#### 4. Error Event

Sent when an error occurs.

**Message Format:**
```json
{
  "type": "error",
  "timestamp": "2025-10-06T12:35:00.789Z",
  "data": {
    "message": "Error occurred",
    "error": "Database connection failed",
    "details": "Full error traceback..."
  }
}
```

**Usage:**
```javascript
if (data.type === "error") {
  showError(data.data.error);
  console.error("Error details:", data.data.details);
}
```

#### 5. Pong Event

Response to ping.

**Message Format:**
```json
{
  "type": "pong"
}
```

---

## REST API Endpoints

### 1. Health Check

**Endpoint:** `GET /`

**Description:** Check if API is running

**Response:**
```json
{
  "status": "ok",
  "service": "Photosphere Labs Agent API",
  "version": "1.0.0"
}
```

**Example:**
```javascript
const response = await fetch("http://localhost:8000/");
const health = await response.json();
console.log(health.status); // "ok"
```

---

### 2. Get User Conversations

**Endpoint:** `GET /conversations/{user_id}`

**Description:** Get all conversations for a user

**Path Parameters:**
- `user_id` (string): User ID

**Response:**
```json
{
  "user_id": "user123",
  "conversations": [
    {
      "conversation_id": "conv-uuid-1",
      "created_at": "2025-10-01T10:00:00Z",
      "last_updated": "2025-10-06T12:00:00Z",
      "message_count": 15,
      "preview": "Show me my top Instagram posts by engagement..."
    },
    {
      "conversation_id": "conv-uuid-2",
      "created_at": "2025-09-25T14:30:00Z",
      "last_updated": "2025-09-25T15:00:00Z",
      "message_count": 8,
      "preview": "What is my Instagram engagement rate..."
    }
  ],
  "count": 2
}
```

**Example:**
```javascript
const response = await fetch(`http://localhost:8000/conversations/${userId}`);
const data = await response.json();

// Display conversation list
data.conversations.forEach(conv => {
  console.log(conv.preview);
  console.log(`Messages: ${conv.message_count}`);
});
```

---

### 3. Get Conversation Messages

**Endpoint:** `GET /conversations/{user_id}/{conversation_id}/messages`

**Description:** Get all messages from a specific conversation

**Path Parameters:**
- `user_id` (string): User ID
- `conversation_id` (string): Conversation ID

**Query Parameters:**
- `limit` (integer, optional): Max messages to return (default: 50)

**Response:**
```json
{
  "user_id": "user123",
  "conversation_id": "conv-uuid-1",
  "messages": [
    {
      "role": "user",
      "content": "Show me my top Instagram posts",
      "timestamp": "2025-10-06T12:00:00Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "Here are your top 5 Instagram posts by engagement...",
      "timestamp": "2025-10-06T12:00:15Z",
      "metadata": {
        "routing": {
          "primary_agent": "data_analytics"
        }
      }
    }
  ],
  "count": 2
}
```

**Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/conversations/${userId}/${conversationId}/messages?limit=50`
);
const data = await response.json();

// Display messages
data.messages.forEach(msg => {
  if (msg.role === "user") {
    displayUserMessage(msg.content);
  } else {
    displayAssistantMessage(msg.content);
  }
});
```

---

## Complete Integration Example

### React Component Example

```javascript
import { useEffect, useState, useRef } from 'react';

function ChatInterface({ userId }) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const wsRef = useRef(null);
  const sessionId = useRef(`conv-${crypto.randomUUID()}`);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(
      `ws://localhost:8000/ws/${userId}/${sessionId.current}`
    );

    ws.onopen = () => {
      console.log("Connected to chat");
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleServerMessage(data);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("Disconnected");
      setIsConnected(false);
    };

    wsRef.current = ws;

    // Cleanup
    return () => {
      ws.close();
    };
  }, [userId]);

  const handleServerMessage = (data) => {
    switch (data.type) {
      case "started":
        setIsProcessing(true);
        setProgress(0);
        setStatusMessage(data.data.message);
        break;

      case "progress":
        setProgress(data.data.progress);
        setStatusMessage(data.data.message);
        break;

      case "completed":
        setIsProcessing(false);
        setProgress(100);
        setStatusMessage("");
        setMessages(prev => [...prev, {
          role: "assistant",
          content: data.data.response,
          timestamp: new Date()
        }]);
        break;

      case "error":
        setIsProcessing(false);
        setStatusMessage("");
        alert(`Error: ${data.data.error}`);
        break;
    }
  };

  const sendMessage = (query) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      alert("Not connected to chat");
      return;
    }

    // Add user message to UI
    setMessages(prev => [...prev, {
      role: "user",
      content: query,
      timestamp: new Date()
    }]);

    // Send to server
    wsRef.current.send(JSON.stringify({
      type: "query",
      query: query,
      conversation_id: sessionId.current
    }));
  };

  return (
    <div className="chat-interface">
      {/* Connection status */}
      <div className="status">
        {isConnected ? "🟢 Connected" : "🔴 Disconnected"}
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            <div className="timestamp">{msg.timestamp.toLocaleTimeString()}</div>
          </div>
        ))}
      </div>

      {/* Progress indicator */}
      {isProcessing && (
        <div className="progress-container">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
          <div className="status-message">{statusMessage}</div>
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={!isConnected || isProcessing} />
    </div>
  );
}
```

---

## Error Handling Best Practices

### 1. Connection Errors

```javascript
ws.onerror = (error) => {
  console.error("WebSocket error:", error);

  // Show user-friendly message
  showNotification("Connection error. Please check your internet connection.");
};

ws.onclose = (event) => {
  console.log("Connection closed:", event.code, event.reason);

  // Attempt reconnection
  if (!event.wasClean) {
    setTimeout(() => reconnect(), 3000);
  }
};
```

### 2. Message Validation

```javascript
ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);

    // Validate message structure
    if (!data.type) {
      console.warn("Invalid message format:", data);
      return;
    }

    handleServerMessage(data);
  } catch (error) {
    console.error("Failed to parse message:", error);
  }
};
```

### 3. Timeout Handling

```javascript
let timeoutId;

const sendQuery = (query) => {
  ws.send(JSON.stringify({ type: "query", query }));

  // Set timeout (2 minutes)
  timeoutId = setTimeout(() => {
    setIsProcessing(false);
    showError("Request timed out. Please try again.");
  }, 120000);
};

// Clear timeout on completion
const handleCompleted = (data) => {
  clearTimeout(timeoutId);
  // ... handle completion
};
```

---

## Environment Configuration

### Development

```javascript
const WS_URL = "ws://localhost:8000";
const API_URL = "http://localhost:8000";
```

### Production

```javascript
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "wss://api.yourdomain.com";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.yourdomain.com";
```

**Note:** Use `wss://` (WebSocket Secure) in production, not `ws://`

---

## Testing the API

### 1. Test WebSocket Backend

```bash
# Start the server
python api_websocket.py

# Or with uvicorn
uvicorn api_websocket:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test with Python Client

```bash
# Run the test client
python test_websocket.py
```

### 3. Test with Browser Console

```javascript
// Open browser console on any page
const ws = new WebSocket("ws://localhost:8000/ws/test_user/test_session");

ws.onopen = () => {
  console.log("Connected!");
  ws.send(JSON.stringify({
    type: "query",
    query: "Show me my top Instagram posts",
    conversation_id: "test_session"
  }));
};

ws.onmessage = (event) => {
  console.log("Received:", JSON.parse(event.data));
};
```

---

## Rate Limiting & Security

**Important:** This initial implementation does NOT include:
- Authentication/authorization
- Rate limiting
- Input validation/sanitization
- CORS restrictions

**TODO before production:**
1. Add authentication middleware (JWT tokens)
2. Implement rate limiting (per user/IP)
3. Add input validation
4. Configure CORS for your frontend domain
5. Use HTTPS/WSS only
6. Add API key validation

---

## Support & Questions

If you have questions about the API or need clarification on any endpoints, please:
1. Check this documentation first
2. Review the example code
3. Test with the provided test client
4. Reach out with specific questions about your frontend implementation
