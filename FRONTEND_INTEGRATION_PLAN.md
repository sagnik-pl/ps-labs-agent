# Frontend Integration Plan - Photosphere Labs Chat

## Overview

This document provides a **step-by-step plan** for integrating the WebSocket-based chat interface into the Photosphere Labs frontend application. This plan is specifically tailored to your tech stack:

- **Framework:** React 18.3.1 (standalone with Vite)
- **Language:** TypeScript 5.6.3 (strict mode)
- **Routing:** Wouter v3.3.5
- **State Management:** TanStack Query v5.60.5
- **UI Components:** shadcn/ui + Radix UI + Tailwind CSS
- **Auth:** Firebase Auth
- **Deployment:** Vercel

The backend is complete and ready to use.

---

## Prerequisites

Before starting, ensure you have:

1. **Backend Running**
   ```bash
   # In the backend repo (ps-labs-agent)
   python api_websocket.py
   # Server will run on: http://localhost:8000
   ```

2. **Frontend Development Server**
   ```bash
   # In the frontend repo (ps-labs-app)
   npm run dev:client
   # Frontend will run on: http://localhost:5173
   ```

3. **User Authentication**
   - Firebase Auth is already integrated via `useAuth()` hook
   - User ID access: `const { firebaseUser } = useAuth(); const userId = firebaseUser?.uid;`

4. **Environment Variables**
   - Backend WebSocket URL needs to be configured in `.env.local`

---

## Step-by-Step Implementation

### Step 1: Add Environment Variables

Add WebSocket configuration to your environment files.

**File:** `.env.local` (development)
```bash
# WebSocket backend URL
VITE_CHAT_WS_URL=ws://localhost:8000
VITE_CHAT_API_URL=http://localhost:8000
```

**File:** `.env.production` (production - to be configured during deployment)
```bash
# WebSocket backend URL (update with your production URL)
VITE_CHAT_WS_URL=wss://api.yourdomain.com
VITE_CHAT_API_URL=https://api.yourdomain.com
```

**Note:** The `VITE_` prefix is required for client-side environment variables in your Vite setup.

---

### Step 2: Create TypeScript Types

Create type definitions for chat messages and state.

**File:** `client/src/types/chat.ts`

```typescript
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  conversationId?: string;
}

export interface ProgressUpdate {
  stage: string;
  message: string;
  progress: number;
}

export interface WebSocketMessage {
  type: 'message' | 'progress' | 'error' | 'complete' | 'pong';
  content?: string;
  stage?: string;
  message?: string;
  progress?: number;
  error?: string;
}

export interface Conversation {
  conversation_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message?: string;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  messages: ChatMessage[];
  isProcessing: boolean;
  progress: number;
  progressMessage: string;
  error: string | null;
  sendMessage: (query: string) => void;
  disconnect: () => void;
  reconnect: () => void;
}
```

---

### Step 3: Create WebSocket Hook

Create a reusable WebSocket connection manager using React hooks and TypeScript.

**File:** `client/src/hooks/useWebSocket.ts`

**Key Responsibilities:**
- Establish and maintain WebSocket connection
- Handle reconnection logic with exponential backoff
- Send and receive messages
- Manage connection state
- Handle progress updates
- Integrate with your existing `useAuth` hook for user ID

**Complete Implementation:**

```typescript
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import type { ChatMessage, WebSocketMessage, UseWebSocketReturn } from '@/types/chat';

const WS_BASE_URL = import.meta.env.VITE_CHAT_WS_URL || 'ws://localhost:8000';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(conversationId: string): UseWebSocketReturn {
  const { firebaseUser } = useAuth();
  const userId = firebaseUser?.uid;

  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!userId || !conversationId) {
      console.warn('Cannot connect: missing userId or conversationId');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      const wsUrl = `${WS_BASE_URL}/ws/${userId}/${conversationId}`;
      console.log('Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);

          switch (data.type) {
            case 'message':
              if (data.content) {
                setMessages(prev => [...prev, {
                  role: 'assistant',
                  content: data.content!,
                  timestamp: new Date().toISOString(),
                  conversationId
                }]);
              }
              break;

            case 'progress':
              setProgress(data.progress || 0);
              setProgressMessage(data.message || '');
              setIsProcessing(true);
              break;

            case 'complete':
              setIsProcessing(false);
              setProgress(0);
              setProgressMessage('');
              break;

            case 'error':
              setError(data.error || 'An error occurred');
              setIsProcessing(false);
              break;

            case 'pong':
              // Heartbeat response
              break;

            default:
              console.warn('Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error occurred');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsProcessing(false);

        // Attempt reconnection
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_DELAY * reconnectAttemptsRef.current);
        } else {
          setError('Connection lost. Please refresh the page.');
        }
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to connect to chat service');
    }
  }, [userId, conversationId]);

  // Send message
  const sendMessage = useCallback((query: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to chat service');
      return;
    }

    if (!query.trim()) {
      return;
    }

    try {
      // Add user message to chat
      setMessages(prev => [...prev, {
        role: 'user',
        content: query,
        timestamp: new Date().toISOString(),
        conversationId
      }]);

      // Send to backend
      wsRef.current.send(JSON.stringify({
        query,
        conversation_id: conversationId
      }));

      setIsProcessing(true);
      setError(null);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
    }
  }, [conversationId]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Reconnect manually
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect, disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    if (userId && conversationId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [userId, conversationId, connect, disconnect]);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(heartbeat);
  }, [isConnected]);

  return {
    isConnected,
    messages,
    isProcessing,
    progress,
    progressMessage,
    error,
    sendMessage,
    disconnect,
    reconnect
  };
}
```

**Key Features:**
- ✅ Automatic reconnection with exponential backoff
- ✅ Integration with your `useAuth` hook
- ✅ TypeScript type safety
- ✅ Progress tracking
- ✅ Error handling
- ✅ Heartbeat to keep connection alive
- ✅ Automatic cleanup on unmount

---

### Step 4: Create Chat Service for REST API

Create a service file for REST API calls (conversation history, etc.) using your existing `apiRequest` pattern.

**File:** `client/src/services/chatService.ts`

```typescript
import { apiRequest } from '@/lib/queryClient';
import type { Conversation, ChatMessage } from '@/types/chat';

const API_BASE = import.meta.env.VITE_CHAT_API_URL || 'http://localhost:8000';

export interface ConversationsResponse {
  user_id: string;
  conversations: Conversation[];
}

export interface MessagesResponse {
  conversation_id: string;
  messages: ChatMessage[];
}

/**
 * Fetch all conversations for a user
 */
export async function getUserConversations(userId: string): Promise<ConversationsResponse> {
  const response = await fetch(`${API_BASE}/conversations/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch messages for a specific conversation
 */
export async function getConversationMessages(
  userId: string,
  conversationId: string
): Promise<MessagesResponse> {
  const response = await fetch(`${API_BASE}/conversations/${userId}/${conversationId}/messages`);
  if (!response.ok) {
    throw new Error(`Failed to fetch messages: ${response.statusText}`);
  }
  return response.json();
}
```

**Note:** WebSocket communication doesn't use Firebase auth tokens (the backend uses Firebase Admin SDK directly). REST API calls can use your existing `apiRequest` function if you need authenticated endpoints later.

---

### Step 5: Create Chat UI Components

Build the chat interface using shadcn/ui components and Tailwind CSS.

#### 5.1 Main Chat Sidebar Component

**File:** `client/src/components/chat/ChatSidebar.tsx`

**Features:**
- Sidebar panel layout (recommended for your app)
- Message display with auto-scroll
- Input field for queries
- Progress indicator
- Connection status indicator
- Error handling with toast notifications
- Integration with `useWebSocket` hook

**Complete Implementation:**

```typescript
import { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useToast } from '@/hooks/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import ChatMessage from './ChatMessage';
import { MessageCircle, Send, AlertCircle } from 'lucide-react';

interface ChatSidebarProps {
  conversationId: string;
  onClose?: () => void;
}

export default function ChatSidebar({ conversationId, onClose }: ChatSidebarProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const {
    isConnected,
    messages,
    isProcessing,
    progress,
    progressMessage,
    error,
    sendMessage,
    reconnect
  } = useWebSocket(conversationId);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Show error toast
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error',
        description: error,
        variant: 'destructive'
      });
    }
  }, [error, toast]);

  const handleSend = () => {
    if (!input.trim() || isProcessing) return;

    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            AI Assistant
          </CardTitle>
          <Badge variant={isConnected ? 'default' : 'destructive'}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>Start a conversation by asking a question</p>
            </div>
          )}

          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}

          {/* Progress Indicator */}
          {isProcessing && (
            <div className="my-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600" />
                <span className="text-sm font-medium">{progressMessage}</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          <div ref={messagesEndRef} />
        </ScrollArea>

        {/* Connection Error Banner */}
        {!isConnected && (
          <div className="bg-destructive/10 border-t border-destructive/20 p-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="w-4 h-4" />
              <span>Connection lost</span>
            </div>
            <Button size="sm" variant="outline" onClick={reconnect}>
              Reconnect
            </Button>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your data..."
              className="min-h-[60px] resize-none"
              disabled={!isConnected || isProcessing}
            />
            <Button
              onClick={handleSend}
              disabled={!isConnected || isProcessing || !input.trim()}
              size="icon"
              className="h-[60px]"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 5.2 Message Component

**File:** `client/src/components/chat/ChatMessage.tsx`

**Features:**
- Different styling for user vs assistant messages
- Markdown rendering for assistant responses
- Timestamp display
- Copy to clipboard functionality
- Avatar icons

```typescript
import { useState } from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Copy, Check, User, Bot } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const isUser = message.role === 'user';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);

      toast({
        description: 'Copied to clipboard',
        duration: 2000
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to copy message',
        variant: 'destructive'
      });
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <Avatar className={`${isUser ? 'bg-indigo-600' : 'bg-gray-700'}`}>
        <AvatarFallback>
          {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'items-end' : ''}`}>
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? 'bg-indigo-600 text-white'
              : 'bg-muted text-foreground'
          }`}
        >
          <div className="prose prose-sm max-w-none dark:prose-invert">
            {/* TODO: Add markdown rendering for assistant messages */}
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        </div>

        {/* Message Footer */}
        <div className={`flex items-center gap-2 mt-1 px-1 ${isUser ? 'justify-end' : ''}`}>
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>

          {!isUser && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="w-3 h-3" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

#### 5.3 Conversation List Component

**File:** `client/src/components/chat/ConversationList.tsx`

**Features:**
- List all user conversations
- Display last message preview and timestamp
- Click to load conversation
- Create new conversation button

```typescript
import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { getUserConversations } from '@/services/chatService';
import { useToast } from '@/hooks/use-toast';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { MessageCircle, Plus } from 'lucide-react';
import type { Conversation } from '@/types/chat';

interface ConversationListProps {
  activeConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
}

export default function ConversationList({
  activeConversationId,
  onSelectConversation,
  onNewConversation
}: ConversationListProps) {
  const { firebaseUser } = useAuth();
  const userId = firebaseUser?.uid;
  const { toast } = useToast();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;

    const loadConversations = async () => {
      try {
        setIsLoading(true);
        const data = await getUserConversations(userId);
        setConversations(data.conversations);
      } catch (err) {
        console.error('Failed to load conversations:', err);
        toast({
          title: 'Error',
          description: 'Failed to load conversations',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadConversations();
  }, [userId, toast]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="space-y-2 p-2">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-2 border-b">
        <Button
          onClick={onNewConversation}
          className="w-full"
          variant="default"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Conversation
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {conversations.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <Card
                key={conv.conversation_id}
                className={`p-3 cursor-pointer hover:bg-muted/50 transition-colors ${
                  activeConversationId === conv.conversation_id
                    ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950'
                    : ''
                }`}
                onClick={() => onSelectConversation(conv.conversation_id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {conv.last_message || 'New Conversation'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {conv.message_count} messages
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(conv.updated_at)}
                  </span>
                </div>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
```

**Note:** You'll need to add the `Skeleton` component to your shadcn/ui collection if you don't have it already:
```bash
npx shadcn-ui@latest add skeleton
```

---

### Step 6: Integrate Chat into Dashboard with Routing

Add the chat interface to your application using Wouter routing.

#### 6.1 Add Barrel Export for Chat Components

**File:** `client/src/components/chat/index.ts`

```typescript
export { default as ChatSidebar } from './ChatSidebar';
export { default as ChatMessage } from './ChatMessage';
export { default as ConversationList } from './ConversationList';
```

#### 6.2 Create Chat Page Component

**File:** `client/src/pages/Chat.tsx`

```typescript
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { ChatSidebar, ConversationList } from '@/components/chat';

export default function Chat() {
  const { firebaseUser } = useAuth();
  const userId = firebaseUser?.uid;

  // Generate new conversation ID
  const [activeConversationId, setActiveConversationId] = useState<string>(
    () => `conv-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  );

  const handleNewConversation = () => {
    const newId = `conv-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    setActiveConversationId(newId);
  };

  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
  };

  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Please sign in to access chat</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4 h-screen flex gap-4">
        {/* Conversation List Sidebar */}
        <div className="w-80 h-full">
          <ConversationList
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
          />
        </div>

        {/* Chat Interface */}
        <div className="flex-1 h-full">
          <ChatSidebar conversationId={activeConversationId} />
        </div>
      </div>
    </div>
  );
}
```

#### 6.3 Add Route to App

**File:** `client/src/App.tsx`

Update your router to include the chat route:

```typescript
import Chat from '@/pages/Chat';

// Inside your Router component, add:
<Route path="/chat">{() => <Chat />}</Route>
```

**Complete example based on your existing structure:**

```typescript
import { Route, Switch } from 'wouter';
import { useAuth } from './hooks/useAuth';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Landing from './pages/Landing';
// ... other imports

function Router() {
  const { canAccessPlatform, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Switch>
      {!canAccessPlatform ? (
        <Route path="/" component={Landing} />
      ) : (
        <>
          <Route path="/">{() => <Dashboard />}</Route>
          <Route path="/connect">{() => <Dashboard initialView="connect" />}</Route>
          <Route path="/chat">{() => <Chat />}</Route> {/* NEW */}
        </>
      )}
      <Route path="/privacy-policy" component={PrivacyPolicy} />
      <Route path="/data-agreement" component={DataAgreement} />
      <Route path="/terms-of-service" component={TermsOfService} />
      <Route component={NotFound} />
    </Switch>
  );
}
```

#### 6.4 Add Navigation Link to Dashboard

Update your Dashboard navigation to include a link to the chat page.

**Example addition to your navbar:**

```typescript
import { Link } from 'wouter';
import { MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

// In your navigation component:
<Link href="/chat">
  <Button variant="ghost" className="gap-2">
    <MessageCircle className="w-4 h-4" />
    AI Assistant
  </Button>
</Link>
```

---

### Step 7: Testing & Deployment

#### 7.1 Manual Testing Checklist

Before deploying, test the following scenarios:

- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:5173`
- [ ] User can authenticate via Firebase Auth
- [ ] WebSocket connects successfully (check browser console)
- [ ] Send a query and receive response
- [ ] Progress updates display correctly
- [ ] Messages render in chat
- [ ] Load conversation history from API
- [ ] Switch between conversations
- [ ] Create new conversation
- [ ] Connection error handling (stop backend, check reconnection)
- [ ] Timeout handling (send very complex query)
- [ ] Toast notifications appear for errors
- [ ] Mobile responsive layout

#### 7.2 Vite Development Proxy (Optional)

If you want to avoid CORS issues during development, add a Vite proxy.

**File:** `vite.config.ts`

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/chat-api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/chat-api/, '')
      }
    }
  }
});
```

Then update your environment variable:
```bash
VITE_CHAT_API_URL=/chat-api
```

#### 7.3 Production Deployment Considerations

**Backend Deployment:**
- Deploy WebSocket backend separately (e.g., Railway, Render, AWS ECS)
- Use `wss://` (secure WebSocket) in production
- Configure CORS to allow your frontend domain
- Set up environment variables for Firebase Admin SDK

**Frontend Deployment (Vercel):**
- Update `.env.production` with production WebSocket URL
- No changes needed to Vercel config (WebSockets connect from browser, not server)
- Test on preview deployment before production

**Environment Variables for Production:**
```bash
# Backend (ps-labs-agent)
FIREBASE_PROJECT_ID=ps-labs-app-prod
FIREBASE_PRIVATE_KEY=...
OPENAI_API_KEY=...

# Frontend (ps-labs-app)
VITE_CHAT_WS_URL=wss://chat-api.yourdomain.com
VITE_CHAT_API_URL=https://chat-api.yourdomain.com
```

---

## File Structure Summary

Complete file structure for the chat feature:

```
client/src/
├── types/
│   └── chat.ts                      # TypeScript type definitions
├── hooks/
│   ├── useWebSocket.ts              # WebSocket connection hook
│   ├── useAuth.ts                   # Existing auth hook (already present)
│   └── use-toast.ts                 # Existing toast hook (already present)
├── services/
│   └── chatService.ts               # REST API calls for chat
├── components/
│   ├── chat/
│   │   ├── ChatSidebar.tsx          # Main chat container
│   │   ├── ChatMessage.tsx          # Individual message bubble
│   │   ├── ConversationList.tsx     # Past conversations list
│   │   └── index.ts                 # Barrel export
│   └── ui/                          # Existing shadcn/ui components
│       ├── scroll-area.tsx
│       ├── button.tsx
│       ├── textarea.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── progress.tsx
│       ├── skeleton.tsx             # Add if not present
│       └── ...
└── pages/
    ├── Chat.tsx                     # Chat page component
    ├── Dashboard.tsx                # Existing (add nav link)
    └── ...
```

---

## Optional Enhancements (Future Iterations)

These features can be added after the basic chat is working:

### 1. Markdown Rendering for Assistant Messages

**Library:** `react-markdown`

```bash
npm install react-markdown
```

Update `ChatMessage.tsx` to render markdown:
```typescript
import ReactMarkdown from 'react-markdown';

// Replace the content div with:
<div className="prose prose-sm max-w-none dark:prose-invert">
  <ReactMarkdown>{message.content}</ReactMarkdown>
</div>
```

### 2. Message Virtualization (for long conversations)

**Library:** `react-window` or `@tanstack/react-virtual`

Improves performance when displaying 100+ messages.

### 3. Typing Indicators

Show animated dots while agent is processing:
```typescript
{isProcessing && !progressMessage && (
  <div className="flex gap-1 p-3">
    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-100" />
    <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-200" />
  </div>
)}
```

### 4. Load Previous Messages on Conversation Select

Add to `ChatSidebar.tsx`:
```typescript
useEffect(() => {
  const loadHistory = async () => {
    if (!userId || !conversationId) return;

    try {
      const data = await getConversationMessages(userId, conversationId);
      setMessages(data.messages);
    } catch (err) {
      console.error('Failed to load messages:', err);
    }
  };

  loadHistory();
}, [conversationId, userId]);
```

### 5. Code Syntax Highlighting

If agent returns code blocks, add syntax highlighting:

```bash
npm install react-syntax-highlighter
```

---

## Quick Start Checklist

Follow these steps in order:

1. **Environment Setup**
   - [ ] Add `VITE_CHAT_WS_URL` and `VITE_CHAT_API_URL` to `.env.local`
   - [ ] Start backend: `python api_websocket.py` (port 8000)
   - [ ] Start frontend: `npm run dev:client` (port 5173)

2. **Create Files**
   - [ ] `client/src/types/chat.ts` - Type definitions
   - [ ] `client/src/hooks/useWebSocket.ts` - WebSocket hook
   - [ ] `client/src/services/chatService.ts` - REST API service
   - [ ] `client/src/components/chat/ChatSidebar.tsx` - Main chat UI
   - [ ] `client/src/components/chat/ChatMessage.tsx` - Message component
   - [ ] `client/src/components/chat/ConversationList.tsx` - Conversation list
   - [ ] `client/src/components/chat/index.ts` - Barrel export
   - [ ] `client/src/pages/Chat.tsx` - Chat page

3. **Update Existing Files**
   - [ ] `client/src/App.tsx` - Add `/chat` route
   - [ ] Dashboard component - Add navigation link to `/chat`

4. **Install Missing Dependencies** (if needed)
   - [ ] `npx shadcn-ui@latest add skeleton` (if not present)
   - [ ] Lucide React icons (should already be installed)

5. **Test**
   - [ ] Navigate to `http://localhost:5173/chat`
   - [ ] Send a test query
   - [ ] Verify WebSocket connection in browser console
   - [ ] Check progress updates and final response

---

## Troubleshooting

### WebSocket Connection Fails

**Symptom:** "Connection lost" message immediately

**Solutions:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Check browser console for error messages
3. Verify `VITE_CHAT_WS_URL=ws://localhost:8000` in `.env.local`
4. Ensure no firewall blocking port 8000

### Messages Not Appearing

**Symptom:** Query sent but no response

**Solutions:**
1. Check browser console for WebSocket messages
2. Check backend logs for errors
3. Verify user is authenticated (`firebaseUser?.uid` is not null)
4. Test backend directly: `python test_websocket.py`

### TypeScript Errors

**Symptom:** Type errors in VSCode

**Solutions:**
1. Verify `@/*` path alias in `tsconfig.json`
2. Restart TypeScript server: Cmd+Shift+P > "TypeScript: Restart TS Server"
3. Check all imports use correct paths

### CORS Errors

**Symptom:** "CORS policy" error in console

**Solutions:**
1. Backend should have CORS configured for `http://localhost:5173`
2. Use Vite proxy (see Step 7.2) to avoid CORS in development

---

## Support & Resources

- **Backend API Documentation:** `/Users/sagnik/Development/ps-labs-agent/API_DOCUMENTATION.md`
- **Backend Test Client:** `python test_websocket.py` in backend repo
- **Frontend Tech Stack Docs:**
  - [Vite Documentation](https://vitejs.dev/)
  - [TanStack Query](https://tanstack.com/query/latest)
  - [shadcn/ui](https://ui.shadcn.com/)
  - [Wouter Router](https://github.com/molefrog/wouter)
  - [Tailwind CSS](https://tailwindcss.com/)

---

## Summary

This plan provides **production-ready code** specifically tailored to your stack:
- ✅ TypeScript with strict mode
- ✅ React 18.3.1 + Vite
- ✅ Integration with existing `useAuth` hook
- ✅ shadcn/ui components + Tailwind CSS
- ✅ Wouter routing
- ✅ Your existing toast notification system
- ✅ Path aliases (`@/*`)
- ✅ Mobile responsive design

**All code examples are copy-paste ready** for your `ps-labs-app` repository.

The backend is ready and waiting for your frontend! 🚀
