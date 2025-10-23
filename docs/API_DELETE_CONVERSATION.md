# Delete Conversation API Documentation

## Overview

This API endpoint allows users to permanently delete a conversation from Firestore. Once deleted, the conversation and all its messages cannot be recovered.

**Endpoint**: `DELETE /conversations/{user_id}/{conversation_id}`

**Deployed**: Production (Railway)

**Base URL**: `https://ps-labs-agent-backend-production.up.railway.app`

---

## API Specification

### Request

**Method**: `DELETE`

**URL Pattern**: `/conversations/{user_id}/{conversation_id}`

**Path Parameters**:
- `user_id` (string, required) - The authenticated user's Firebase Auth ID
- `conversation_id` (string, required) - The unique conversation ID to delete (format: `conv_<uuid>`)

**Headers**:
```
Content-Type: application/json
```

**Body**: None (DELETE requests use path parameters only)

---

### Response Formats

#### Success Response (200 OK)

```json
{
  "message": "Conversation deleted successfully",
  "user_id": "1A24KnVLHxfVv4Qp8rD5fx3tir23",
  "conversation_id": "conv_7ab5a9b5-392c-41f3-a0f4-431316c61542"
}
```

#### Not Found (404)

Returned when the conversation doesn't exist or doesn't belong to the user.

```json
{
  "detail": "Conversation conv_7ab5a9b5-392c-41f3-a0f4-431316c61542 not found for user 1A24KnVLHxfVv4Qp8rD5fx3tir23"
}
```

#### Server Error (500)

```json
{
  "detail": "Failed to delete conversation: <error message>"
}
```

---

## Frontend Integration

### JavaScript/TypeScript Example

```typescript
// Configuration
const BACKEND_URL = 'https://ps-labs-agent-backend-production.up.railway.app';

// Function to delete a conversation
async function deleteConversation(userId: string, conversationId: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${BACKEND_URL}/conversations/${userId}/${conversationId}`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.ok) {
      const data = await response.json();
      console.log('Conversation deleted:', data);
      return true;
    } else if (response.status === 404) {
      console.warn('Conversation not found');
      return false;
    } else {
      const error = await response.json();
      console.error('Delete failed:', error.detail);
      return false;
    }
  } catch (error) {
    console.error('Network error:', error);
    return false;
  }
}

// Usage
const success = await deleteConversation(
  '1A24KnVLHxfVv4Qp8rD5fx3tir23',
  'conv_7ab5a9b5-392c-41f3-a0f4-431316c61542'
);
```

### React Component Example

```tsx
import { useState } from 'react';

interface Conversation {
  id: string;
  title: string;
  // ... other fields
}

function ConversationList({ userId, conversations }: { userId: string; conversations: Conversation[] }) {
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const handleDelete = async (conversationId: string) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      'Are you sure you want to delete this conversation? This action cannot be undone.'
    );

    if (!confirmed) return;

    setIsDeleting(conversationId);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/conversations/${userId}/${conversationId}`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        // Remove from UI
        // You might want to update your state management here
        toast.success('Conversation deleted successfully');

        // If user is viewing this conversation, redirect
        if (window.location.pathname.includes(conversationId)) {
          router.push('/chat'); // Redirect to default/new conversation
        }
      } else if (response.status === 404) {
        toast.error('Conversation not found');
      } else {
        const error = await response.json();
        toast.error(`Failed to delete: ${error.detail}`);
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Network error. Please try again.');
    } finally {
      setIsDeleting(null);
    }
  };

  return (
    <div>
      {conversations.map((conv) => (
        <div key={conv.id} className="conversation-item">
          <span>{conv.title}</span>
          <button
            onClick={() => handleDelete(conv.id)}
            disabled={isDeleting === conv.id}
            className="delete-button"
          >
            {isDeleting === conv.id ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## UI/UX Guidelines

### 1. Delete Button Placement

Place the delete button/icon in the conversation list sidebar:
- **Icon**: Use a trash/delete icon (🗑️)
- **Position**: Right side of each conversation item or in a dropdown menu
- **Visibility**: Show on hover or always visible (your design choice)

### 2. Confirmation Dialog

**REQUIRED**: Always show a confirmation dialog before deleting:

```
Title: "Delete Conversation?"
Message: "Are you sure you want to permanently delete this conversation? This action cannot be undone."
Buttons: [Cancel] [Delete]
```

**Recommended**: Make the "Delete" button red to indicate destructive action.

### 3. Loading States

Show loading indicator while deletion is in progress:
- Disable the delete button
- Show spinner or "Deleting..." text
- Prevent other actions on the same conversation

### 4. Success Feedback

After successful deletion:
- ✅ Show success toast/notification: "Conversation deleted"
- Remove conversation from sidebar immediately
- If currently viewing the deleted conversation, redirect user to:
  - New conversation (recommended), or
  - Most recent conversation, or
  - Home/default view

### 5. Error Handling

Display appropriate error messages:
- **404**: "This conversation no longer exists"
- **500**: "Failed to delete. Please try again."
- **Network error**: "Connection error. Check your internet."

---

## Security Considerations

### User Isolation

- ✅ User ID is part of the request path
- ✅ Backend enforces that conversations can only be deleted by the owning user
- ✅ If user_id doesn't match, conversation won't be found (returns 404)

### CORS

- ✅ CORS is configured on the backend to accept DELETE requests
- ✅ Frontend domains are whitelisted

### Permanent Deletion

- ⚠️ **WARNING**: Deletion is permanent and cannot be undone
- ⚠️ All messages in the conversation are deleted
- ⚠️ No recovery mechanism exists
- ✅ Always require user confirmation before deleting

---

## Testing

### Manual Testing Steps

1. **Test successful deletion**:
   ```bash
   curl -X DELETE \
     https://ps-labs-agent-backend-production.up.railway.app/conversations/YOUR_USER_ID/YOUR_CONVERSATION_ID
   ```
   Expected: 200 OK with success message

2. **Test non-existent conversation**:
   ```bash
   curl -X DELETE \
     https://ps-labs-agent-backend-production.up.railway.app/conversations/YOUR_USER_ID/non_existent_conv
   ```
   Expected: 404 Not Found

3. **Test from browser console**:
   ```javascript
   fetch('https://ps-labs-agent-backend-production.up.railway.app/conversations/YOUR_USER_ID/YOUR_CONVERSATION_ID', {
     method: 'DELETE',
   })
   .then(r => r.json())
   .then(console.log);
   ```

### Integration Testing Checklist

- [ ] Delete button appears on conversations
- [ ] Confirmation dialog shows before deletion
- [ ] Loading state displays during deletion
- [ ] Success toast appears after deletion
- [ ] Conversation removed from sidebar
- [ ] User redirected if viewing deleted conversation
- [ ] Error messages display correctly for failures
- [ ] Cannot delete same conversation twice
- [ ] Other conversations remain unaffected

---

## Implementation Checklist for Frontend Team

### Phase 1: Basic Functionality
- [ ] Add delete icon/button to each conversation in sidebar
- [ ] Implement confirmation dialog
- [ ] Call DELETE API endpoint with correct user_id and conversation_id
- [ ] Handle 200, 404, and 500 responses
- [ ] Remove deleted conversation from UI state

### Phase 2: User Experience
- [ ] Add loading state during deletion
- [ ] Show success toast notification
- [ ] Show error toast for failures
- [ ] Redirect user if viewing deleted conversation
- [ ] Add keyboard shortcut (optional, e.g., Delete key)

### Phase 3: Polish
- [ ] Smooth animation when removing from list
- [ ] Optimistic UI update (remove immediately, revert on error)
- [ ] Accessibility: keyboard navigation and screen reader support
- [ ] Mobile responsive: swipe to delete gesture (optional)

---

## Rollback Plan

If issues occur with the delete feature:

1. **Frontend**: Remove delete button from UI (quick fix)
2. **Backend**: Endpoint can be disabled without breaking existing functionality
3. **Firestore**: Conversations remain in database, no data loss

---

## Support & Questions

- **Backend Repository**: `ps-labs-agent` (this repo)
- **API File**: `api_websocket.py:424-459`
- **Firebase Method**: `utils/firebase_client.py:483-512`
- **Deployment**: Railway (auto-deploys from `smarter_agents` branch)

For questions or issues:
- Check Railway logs: `railway logs --deployment`
- Review this documentation
- Contact: sagnik@photospherelabs.com

---

## Related Endpoints

- `GET /conversations/{user_id}` - List all conversations for a user
- `GET /conversations/{user_id}/{conversation_id}/messages` - Get messages in a conversation
- `POST /ws/{user_id}/{conversation_id}` - WebSocket for real-time chat

---

## Changelog

**2025-01-23** - Initial implementation
- Added `delete_conversation()` method to Firebase client
- Added `DELETE /conversations/{user_id}/{conversation_id}` endpoint
- Deployed to production
