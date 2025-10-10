# Chat Feature Implementation - Frontend Prompt
## For Claude in Frontend Repository

**IMPORTANT**: Copy this entire document to your frontend repository and provide it to Claude for implementation.

---

## Context & Overview

You are implementing a **real-time chat interface** for an AI-powered analytics platform. The backend WebSocket API is **already deployed and ready** on Railway. Your task is to build the frontend chat UI that connects to this backend.

### What You're Building

A chat interface where users can:
1. Ask natural language questions about their business data
2. See real-time progress updates as the AI processes their query
3. Receive detailed insights with charts, metrics, and recommendations
4. View conversation history
5. Switch between past conversations

### User Experience Flow

```
User types: "Show me my top Instagram posts by engagement"
           ↓
[Chat shows: "Planning Task..." with progress bar at 10%]
           ↓
[Chat shows: "Fetching Data..." with progress bar at 30%]
           ↓
[Chat shows: "Interpreting Data..." with progress bar at 75%]
           ↓
[Chat shows: Complete response with insights and metrics]
```

---

## Backend API Specification

### Base URLs

**Production (Railway):**
```
WebSocket: wss://[YOUR_RAILWAY_URL]
REST API: https://[YOUR_RAILWAY_URL]
```

**Development (Local):**
```
WebSocket: ws://localhost:8000
REST API: http://localhost:8000
```

### WebSocket Connection

**Endpoint:**
```
wss://[YOUR_RAILWAY_URL]/ws/{user_id}/{session_id}
```

**Parameters:**
- `user_id` - Unique user identifier (from your auth system)
- `session_id` - Unique session/conversation ID (generate with UUID)

**Connection Example:**
```typescript
const userId = "user_12345"; // From your auth
const conversationId = "conv_" + crypto.randomUUID();
const ws = new WebSocket(
  `wss://your-railway-url.railway.app/ws/${userId}/${conversationId}`
);
```

---

## Message Formats

### 1. Client → Server Messages

#### Send a Query

```typescript
interface QueryMessage {
  type: "query";
  query: string;              // User's question
  conversation_id: string;     // Same as session_id in URL
}

// Example:
{
  "type": "query",
  "query": "Show me my top 5 Instagram posts by engagement",
  "conversation_id": "conv_abc123"
}
```

#### Send Keep-Alive Ping

```typescript
interface PingMessage {
  type: "ping";
}

// Example:
{
  "type": "ping"
}
```

---

### 2. Server → Client Messages

#### Started Event

Sent when query processing begins.

```typescript
interface StartedEvent {
  type: "started";
  data: {
    message: string;    // "Planning Task..."
    progress: number;   // 0
  };
  timestamp: string;    // ISO 8601 format
}

// Example:
{
  "type": "started",
  "data": {
    "message": "Planning Task...",
    "progress": 0
  },
  "timestamp": "2025-10-06T12:00:00.000Z"
}
```

#### Progress Event

Sent as the workflow moves through stages. You'll receive multiple progress events.

```typescript
interface ProgressEvent {
  type: "progress";
  data: {
    message: string;        // Stage description
    progress: number;       // 0-100
    stage?: string;         // Optional: node name
    retry_count?: number;   // Optional: if retrying
  };
  timestamp: string;
}

// Examples:
{
  "type": "progress",
  "data": {
    "message": "Planning Task...",
    "progress": 15,
    "stage": "router_node"
  },
  "timestamp": "2025-10-06T12:00:01.000Z"
}

{
  "type": "progress",
  "data": {
    "message": "Fetching Data...",
    "progress": 30,
    "stage": "sql_generator_node"
  },
  "timestamp": "2025-10-06T12:00:03.000Z"
}

{
  "type": "progress",
  "data": {
    "message": "Interpreting Data...",
    "progress": 75,
    "stage": "data_interpreter_node"
  },
  "timestamp": "2025-10-06T12:00:08.000Z"
}
```

#### Conversation Metadata Event

Sent for new conversations with auto-generated title.

```typescript
interface ConversationMetadataEvent {
  type: "conversation_metadata";
  data: {
    title: string;          // Auto-generated 2-4 word title
    date: string;           // yyyy/mm/dd format
    conversation_id: string;
  };
  timestamp: string;
}

// Example:
{
  "type": "conversation_metadata",
  "data": {
    "title": "Instagram Engagement Analysis",
    "date": "2025/10/06",
    "conversation_id": "conv_abc123"
  },
  "timestamp": "2025-10-06T12:00:00.500Z"
}
```

#### Completed Event

Sent when the query is fully processed with the final response.

```typescript
interface CompletedEvent {
  type: "completed";
  data: {
    message: string;      // "Complete!"
    response: string;     // Full AI response (markdown formatted)
    progress: number;     // 100
    metadata?: {          // Optional metadata
      plan?: object;
      routing?: object;
      validation?: object;
    };
  };
  timestamp: string;
}

// Example:
{
  "type": "completed",
  "data": {
    "message": "Complete!",
    "response": "# Top 5 Instagram Posts by Engagement\n\n## Key Findings\n\n1. **Post #1234** - 15,234 engagements\n   - Posted: Oct 1, 2025\n   - Engagement Rate: 8.5%\n   - Peak interaction: 2-4pm\n\n...",
    "progress": 100
  },
  "timestamp": "2025-10-06T12:00:15.000Z"
}
```

#### Error Event

Sent if something goes wrong during processing.

```typescript
interface ErrorEvent {
  type: "error";
  data: {
    message: string;     // User-friendly error message
    error: string;       // Error details
    details?: string;    // Optional stack trace (dev only)
  };
  timestamp: string;
}

// Example:
{
  "type": "error",
  "data": {
    "message": "Unable to fetch data. Please try again.",
    "error": "Database connection timeout"
  },
  "timestamp": "2025-10-06T12:00:05.000Z"
}
```

#### Pong Response

Response to keep-alive ping.

```typescript
interface PongEvent {
  type: "pong";
}

// Example:
{
  "type": "pong"
}
```

---

## Progress Messages & Stages

The backend sends these progress messages in sequence:

| Progress % | Message | Description |
|-----------|---------|-------------|
| 0% | "Planning Task..." | Initial routing and planning |
| 15% | "Planning Task..." | Route determined |
| 30% | "Fetching Data..." | Generating data query |
| 40% | "Validating Data..." | Validating query |
| 50% | "Fetching Data..." | Executing query |
| 75% | "Interpreting Data..." | Analyzing results |
| 85% | "Interpreting Data..." | Validating insights |
| 95% | "Finalizing Response..." | Preparing final response |
| 100% | "Complete!" | Done |

**Note:** The backend may retry certain steps (SQL validation up to 3x, interpretation validation up to 2x). You'll see the same progress message multiple times if retrying.

---

## REST API Endpoints

### Get Conversations List

```http
GET /conversations/{user_id}
```

**Response:**
```typescript
interface ConversationsResponse {
  user_id: string;
  conversations: Array<{
    conversation_id: string;
    title: string;            // Auto-generated or first message
    created_at: string;       // yyyy/mm/dd format
    updated_at: string;       // yyyy/mm/dd format
    message_count: number;
    last_message: string;     // Preview (first 50 chars)
  }>;
  count: number;
}

// Example:
{
  "user_id": "user_123",
  "conversations": [
    {
      "conversation_id": "conv_abc",
      "title": "Instagram Engagement Report",
      "created_at": "2025/10/06",
      "updated_at": "2025/10/06",
      "message_count": 4,
      "last_message": "Your top posts show strong engagement..."
    }
  ],
  "count": 1
}
```

### Get Conversation Messages

```http
GET /conversations/{user_id}/{conversation_id}/messages?limit=50
```

**Query Parameters:**
- `limit` (optional) - Max messages to return (default: 50)

**Response:**
```typescript
interface MessagesResponse {
  user_id: string;
  conversation_id: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: string;        // ISO 8601 format
    metadata?: object;
  }>;
  count: number;
}

// Example:
{
  "user_id": "user_123",
  "conversation_id": "conv_abc",
  "messages": [
    {
      "role": "user",
      "content": "Show me my top Instagram posts",
      "timestamp": "2025-10-06T12:00:00.000Z",
      "metadata": {}
    },
    {
      "role": "assistant",
      "content": "# Top Instagram Posts\n\n...",
      "timestamp": "2025-10-06T12:00:15.000Z",
      "metadata": {
        "plan": {...}
      }
    }
  ],
  "count": 2
}
```

### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "ok",
  "service": "Photosphere Labs Agent API",
  "version": "1.0.0"
}
```

---

## Implementation Requirements

### Required Features

1. **WebSocket Connection Management**
   - Connect when user opens chat
   - Handle connection errors and reconnection
   - Show connection status to user
   - Implement exponential backoff for reconnection

2. **Message Handling**
   - Send user queries
   - Receive and display all event types
   - Show real-time progress with visual indicator
   - Display conversation metadata (title, date)
   - Handle errors gracefully

3. **Chat UI Components**
   - Message list (scrollable, auto-scroll to bottom)
   - Input field with send button
   - Progress indicator (progress bar or spinner)
   - Loading states
   - Error messages

4. **Conversation History**
   - List of past conversations
   - Load messages when selecting conversation
   - Create new conversation
   - Display conversation title and date

5. **User Experience**
   - Markdown rendering for assistant responses
   - Typing indicator while processing
   - Copy response button
   - Timestamp display
   - Smooth animations

---

## React/TypeScript Implementation Example

### 1. WebSocket Hook

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
}

interface UseWebSocketReturn {
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(
  userId: string,
  conversationId: string
): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000';
    const url = `${wsUrl}/ws/${userId}/${conversationId}`;

    setConnectionStatus('connecting');
    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('connected');
      reconnectAttemptsRef.current = 0;
    };

    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setLastMessage(message);
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('disconnected');

      // Exponential backoff reconnection
      if (reconnectAttemptsRef.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current += 1;
          connect();
        }, delay);
      }
    };
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionStatus('disconnected');
  };

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  };

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [userId, conversationId]);

  return {
    sendMessage,
    lastMessage,
    connectionStatus,
    connect,
    disconnect,
  };
}
```

### 2. Chat Component

```typescript
// components/Chat.tsx
import { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatProps {
  userId: string;
  conversationId: string;
}

export function Chat({ userId, conversationId }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { sendMessage, lastMessage, connectionStatus } = useWebSocket(
    userId,
    conversationId
  );

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    switch (lastMessage.type) {
      case 'started':
        setIsProcessing(true);
        setProgressMessage(lastMessage.data.message);
        setProgressPercent(lastMessage.data.progress);
        break;

      case 'progress':
        setProgressMessage(lastMessage.data.message);
        setProgressPercent(lastMessage.data.progress);
        break;

      case 'conversation_metadata':
        // Update conversation title in your UI
        console.log('Conversation title:', lastMessage.data.title);
        break;

      case 'completed':
        setIsProcessing(false);
        setProgressMessage('');
        setProgressPercent(100);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: lastMessage.data.response,
            timestamp: lastMessage.timestamp,
          },
        ]);
        break;

      case 'error':
        setIsProcessing(false);
        setProgressMessage('');
        alert(`Error: ${lastMessage.data.message}`);
        break;
    }
  }, [lastMessage]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSend = () => {
    if (!inputValue.trim() || isProcessing) return;

    // Add user message to UI
    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to backend
    sendMessage({
      type: 'query',
      query: inputValue,
      conversation_id: conversationId,
    });

    setInputValue('');
  };

  return (
    <div className="chat-container">
      {/* Connection status */}
      <div className="connection-status">
        {connectionStatus === 'connected' ? (
          <span className="status-connected">● Connected</span>
        ) : (
          <span className="status-disconnected">● Disconnected</span>
        )}
      </div>

      {/* Messages */}
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
            <div className="message-timestamp">
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}

        {/* Processing indicator */}
        {isProcessing && (
          <div className="message message-assistant">
            <div className="processing-indicator">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="progress-message">{progressMessage}</p>
              <p className="progress-percent">{progressPercent}%</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          disabled={isProcessing || connectionStatus !== 'connected'}
        />
        <button
          onClick={handleSend}
          disabled={isProcessing || connectionStatus !== 'connected'}
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

### 3. Environment Configuration

```bash
# .env.development
VITE_WEBSOCKET_URL=ws://localhost:8000
VITE_API_URL=http://localhost:8000

# .env.production
VITE_WEBSOCKET_URL=wss://your-railway-url.railway.app
VITE_API_URL=https://your-railway-url.railway.app
```

---

## Styling Recommendations

### Basic CSS Structure

```css
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 800px;
  margin: 0 auto;
}

.connection-status {
  padding: 8px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.status-connected {
  color: #22c55e;
}

.status-disconnected {
  color: #ef4444;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
}

.message-user {
  background: #3b82f6;
  color: white;
  margin-left: 20%;
}

.message-assistant {
  background: #f3f4f6;
  margin-right: 20%;
}

.processing-indicator {
  padding: 16px;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
}

.progress-message {
  margin-top: 8px;
  font-size: 14px;
  color: #6b7280;
}

.input-container {
  display: flex;
  padding: 16px;
  border-top: 1px solid #ddd;
}

.input-container input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin-right: 8px;
}

.input-container button {
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.input-container button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
```

---

## Testing Guide

### 1. Test WebSocket Connection

```typescript
// In your browser console:
const ws = new WebSocket('wss://your-railway-url.railway.app/ws/test-user/test-session');

ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);

// Send a test query
ws.send(JSON.stringify({
  type: 'query',
  query: 'Show me my top Instagram posts',
  conversation_id: 'test-session'
}));
```

### 2. Test REST Endpoints

```bash
# Health check
curl https://your-railway-url.railway.app/

# Get conversations
curl https://your-railway-url.railway.app/conversations/test-user

# Get messages
curl https://your-railway-url.railway.app/conversations/test-user/conv-123/messages
```

### 3. Manual Testing Checklist

- [ ] WebSocket connects successfully
- [ ] Can send a query
- [ ] Progress updates display correctly
- [ ] Final response appears
- [ ] Markdown renders properly
- [ ] Conversations load
- [ ] Messages load for selected conversation
- [ ] Error handling works (disconnect backend and test)
- [ ] Reconnection works
- [ ] Works on mobile devices
- [ ] Keyboard shortcuts work (Enter to send)

---

## Error Handling Best Practices

### 1. Connection Errors

```typescript
if (connectionStatus === 'error' || connectionStatus === 'disconnected') {
  return (
    <div className="error-state">
      <p>Unable to connect to the server.</p>
      <button onClick={connect}>Retry Connection</button>
    </div>
  );
}
```

### 2. Timeout Handling

```typescript
// Add timeout for long-running queries
const timeoutRef = useRef<NodeJS.Timeout>();

const handleSend = () => {
  // ... send message ...

  // Set 60s timeout
  timeoutRef.current = setTimeout(() => {
    if (isProcessing) {
      setIsProcessing(false);
      alert('Request timed out. Please try again.');
    }
  }, 60000);
};

// Clear timeout on completion
useEffect(() => {
  if (lastMessage?.type === 'completed' || lastMessage?.type === 'error') {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }
}, [lastMessage]);
```

### 3. Retry Logic

```typescript
const [retryCount, setRetryCount] = useState(0);
const MAX_RETRIES = 3;

const handleError = () => {
  if (retryCount < MAX_RETRIES) {
    setRetryCount(prev => prev + 1);
    setTimeout(() => connect(), 2000 * Math.pow(2, retryCount));
  } else {
    // Show permanent error state
    alert('Unable to connect after multiple attempts. Please contact support.');
  }
};
```

---

## Performance Optimization

### 1. Message Virtualization

For long conversations (100+ messages), use virtualization:

```bash
npm install react-window
```

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={100}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <Message message={messages[index]} />
    </div>
  )}
</FixedSizeList>
```

### 2. Debounce Input

```typescript
import { useDebouncedCallback } from 'use-debounce';

const debouncedSend = useDebouncedCallback(
  (value) => {
    sendMessage({
      type: 'query',
      query: value,
      conversation_id: conversationId,
    });
  },
  300
);
```

### 3. Memoization

```typescript
import { memo } from 'react';

export const Message = memo(({ message }) => {
  // Component rendering
}, (prevProps, nextProps) => {
  return prevProps.message.timestamp === nextProps.message.timestamp;
});
```

---

## Accessibility Requirements

### 1. Keyboard Navigation

```typescript
// Add keyboard shortcuts
useEffect(() => {
  const handleKeyboard = (e: KeyboardEvent) => {
    // Ctrl+/ to focus input
    if (e.ctrlKey && e.key === '/') {
      inputRef.current?.focus();
    }

    // Escape to clear input
    if (e.key === 'Escape') {
      setInputValue('');
    }
  };

  window.addEventListener('keydown', handleKeyboard);
  return () => window.removeEventListener('keydown', handleKeyboard);
}, []);
```

### 2. ARIA Labels

```typescript
<div
  role="log"
  aria-live="polite"
  aria-label="Chat messages"
  className="messages"
>
  {/* Messages */}
</div>

<input
  type="text"
  aria-label="Chat input"
  aria-describedby="chat-help-text"
/>
<span id="chat-help-text" className="sr-only">
  Type your question and press Enter to send
</span>
```

### 3. Screen Reader Support

```typescript
// Announce progress updates
const [announcement, setAnnouncement] = useState('');

useEffect(() => {
  if (lastMessage?.type === 'progress') {
    setAnnouncement(
      `${lastMessage.data.message} ${lastMessage.data.progress}% complete`
    );
  }
}, [lastMessage]);

<div role="status" aria-live="polite" className="sr-only">
  {announcement}
</div>
```

---

## Dependencies to Install

```bash
# WebSocket + React basics
npm install react react-dom

# TypeScript
npm install -D typescript @types/react @types/react-dom

# Markdown rendering
npm install react-markdown

# Utilities
npm install uuid
npm install -D @types/uuid

# Optional: UI library (if using shadcn/ui)
npm install @radix-ui/react-dialog @radix-ui/react-scroll-area
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Update `VITE_WEBSOCKET_URL` to Railway production URL
- [ ] Update `VITE_API_URL` to Railway production URL
- [ ] Test all features against production backend
- [ ] Ensure HTTPS/WSS (not HTTP/WS)
- [ ] Add error tracking (Sentry recommended)
- [ ] Add analytics (track query count, errors, latency)
- [ ] Test on multiple devices and browsers
- [ ] Verify accessibility compliance
- [ ] Load test with multiple concurrent users
- [ ] Set up monitoring and alerting

---

## Common Issues & Solutions

### Issue: WebSocket won't connect

**Check:**
1. Railway URL is correct (check `railway status`)
2. Using `wss://` (not `ws://`) for production
3. CORS is configured on backend
4. Firewall/network isn't blocking WebSocket

**Solution:**
```typescript
// Add detailed error logging
ws.onerror = (error) => {
  console.error('WebSocket error details:', {
    readyState: ws.readyState,
    url: ws.url,
    error: error,
  });
};
```

### Issue: Progress not updating

**Check:**
1. Event handler for 'progress' type is set up
2. State is updating correctly
3. Backend is sending progress events (check Network tab)

**Solution:**
```typescript
// Log all messages for debugging
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
  setLastMessage(message);
};
```

### Issue: Messages not displaying

**Check:**
1. Markdown renderer is installed and working
2. CSS is loading correctly
3. Auto-scroll is working

**Solution:**
```typescript
// Add debug rendering
{messages.map((msg, idx) => (
  <div key={idx}>
    <pre>{JSON.stringify(msg, null, 2)}</pre>
  </div>
))}
```

---

## Next Steps

1. **Set up your environment variables** with Railway URL
2. **Create the WebSocket hook** (`useWebSocket.ts`)
3. **Build the Chat component** with message rendering
4. **Test with the production backend**
5. **Add conversation history loading**
6. **Implement error handling and reconnection**
7. **Style and polish the UI**
8. **Add accessibility features**
9. **Performance optimize**
10. **Deploy and test end-to-end**

---

## Support & Questions

If you encounter issues:

1. **Check the backend health endpoint** - `curl https://your-railway-url.railway.app/`
2. **Test WebSocket in browser console** (code above)
3. **Check Network tab** for WebSocket messages
4. **Review error messages** in console
5. **Test with different browsers**

---

## Success Criteria

Your implementation is complete when:

✅ Users can connect and send queries
✅ Real-time progress updates display smoothly
✅ Final responses render with proper markdown formatting
✅ Conversation history loads and displays correctly
✅ Errors are handled gracefully with user-friendly messages
✅ Reconnection works automatically
✅ Works on desktop and mobile
✅ Keyboard shortcuts function properly
✅ Screen readers can navigate the chat
✅ Performance is smooth with 50+ messages

---

**Happy coding! You have everything you need to build an amazing chat interface! 🚀**
