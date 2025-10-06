# Frontend Implementation Questions

## Purpose

These questions will help the backend team better understand your frontend architecture so we can provide more specific integration guidance.

Please initialize Claude in your frontend repo and ask it to answer these questions. Share the answers back so we can:
- Provide framework-specific code examples
- Suggest best practices for your stack
- Identify potential integration issues early
- Optimize the integration for your architecture

---

## 1. Framework & Stack

### 1.1 What frontend framework are you using?
- [ ] React
- [ ] Next.js (App Router)
- [ ] Next.js (Pages Router)
- [ ] Vue.js
- [ ] Svelte
- [ ] Angular
- [ ] Other: _____________

### 1.2 What version?
- Framework version: _____________
- React version (if applicable): _____________

### 1.3 Are you using TypeScript?
- [ ] Yes
- [ ] No

If yes:
- TypeScript version: _____________
- Strict mode enabled? [ ] Yes [ ] No

---

## 2. State Management

### 2.1 What state management solution are you using?
- [ ] React Context
- [ ] Redux
- [ ] Redux Toolkit
- [ ] Zustand
- [ ] Jotai
- [ ] Recoil
- [ ] MobX
- [ ] None (local component state only)
- [ ] Other: _____________

### 2.2 File/folder structure for state management?
```
Example:
src/
├── store/
│   ├── chatSlice.js
│   └── userSlice.js
```

Your structure:
```
(Paste your state management structure here)
```

---

## 3. Routing & Navigation

### 3.1 What routing solution are you using?
- [ ] Next.js built-in routing
- [ ] React Router
- [ ] TanStack Router
- [ ] Other: _____________

### 3.2 Where will the chat interface live?
- URL/route: _____________
- Is it a dedicated page or a component that appears on multiple pages?
  - [ ] Dedicated page (e.g., `/chat`)
  - [ ] Modal/overlay accessible from anywhere
  - [ ] Sidebar on specific pages
  - [ ] Other: _____________

---

## 4. Authentication

### 4.1 What authentication solution are you using?
- [ ] Firebase Auth
- [ ] Auth0
- [ ] NextAuth.js
- [ ] Supabase Auth
- [ ] Clerk
- [ ] Custom auth
- [ ] Other: _____________

### 4.2 How do you access the current user ID?
```javascript
// Example for Firebase:
const userId = auth.currentUser?.uid;

// Example for NextAuth:
const { data: session } = useSession();
const userId = session?.user?.id;
```

Your code:
```javascript
(Paste your user ID access pattern here)
```

### 4.3 Do you have auth guards/protected routes?
- [ ] Yes
- [ ] No

If yes, what library/pattern?
- _____________

---

## 5. UI Components & Styling

### 5.1 What component library are you using (if any)?
- [ ] Material-UI (MUI)
- [ ] Chakra UI
- [ ] Ant Design
- [ ] shadcn/ui
- [ ] Radix UI
- [ ] Tailwind UI
- [ ] None (custom components)
- [ ] Other: _____________

### 5.2 What styling approach?
- [ ] CSS Modules
- [ ] Styled Components
- [ ] Emotion
- [ ] Tailwind CSS
- [ ] SASS/SCSS
- [ ] Plain CSS
- [ ] Other: _____________

### 5.3 Do you have existing chat/messaging UI components?
- [ ] Yes
- [ ] No

If yes, can you provide:
- Component names: _____________
- File locations: _____________

---

## 6. Data Fetching

### 6.1 What data fetching library are you using?
- [ ] Native fetch
- [ ] Axios
- [ ] TanStack Query (React Query)
- [ ] SWR
- [ ] Apollo Client (GraphQL)
- [ ] tRPC
- [ ] Other: _____________

### 6.2 Example of a typical API call in your codebase:
```javascript
(Paste an example of how you currently fetch data)

// Example:
const { data, isLoading } = useQuery({
  queryKey: ['user'],
  queryFn: () => fetch('/api/user').then(r => r.json())
});
```

---

## 7. Real-Time Features

### 7.1 Do you currently use WebSockets anywhere?
- [ ] Yes
- [ ] No

If yes:
- For what features? _____________
- What library/pattern? _____________
- File locations: _____________

### 7.2 Do you use Server-Sent Events (SSE)?
- [ ] Yes
- [ ] No

### 7.3 Do you have any real-time subscriptions (Firestore, Supabase, etc.)?
- [ ] Yes
- [ ] No

If yes:
- What service? _____________
- Example code location: _____________

---

## 8. Build & Development

### 8.1 What's your build tool?
- [ ] Vite
- [ ] Webpack
- [ ] Next.js built-in
- [ ] Create React App
- [ ] Other: _____________

### 8.2 Development server port?
- Default port: _____________
- Typical URL: _____________

### 8.3 Environment variables pattern?
```
Example:
.env.local (development)
.env.production (production)

NEXT_PUBLIC_API_URL=...
```

Your pattern:
```
(Paste your env variables structure)
```

---

## 9. Error Handling & Notifications

### 9.1 How do you show notifications/toasts to users?
- [ ] react-toastify
- [ ] react-hot-toast
- [ ] sonner
- [ ] Custom component
- [ ] Component library built-in
- [ ] Other: _____________

### 9.2 Do you have a global error boundary?
- [ ] Yes
- [ ] No

If yes, file location: _____________

### 9.3 How do you handle loading states?
```javascript
(Paste an example of how you typically show loading states)
```

---

## 10. Conversation/Chat Requirements

### 10.1 Should users be able to see past conversations?
- [ ] Yes - show a list of all past conversations
- [ ] Yes - but only the current conversation
- [ ] No - fresh conversation each time
- [ ] Unsure

### 10.2 Should conversations persist across sessions?
- [ ] Yes - load from backend
- [ ] Yes - save to localStorage
- [ ] No - ephemeral only
- [ ] Unsure

### 10.3 Should users be able to:
- [ ] Start a new conversation while keeping old ones
- [ ] Delete conversations
- [ ] Search through past conversations
- [ ] Share conversations with others
- [ ] Export conversation history

### 10.4 Layout preference for chat interface?

Option A: Full-page chat
```
┌─────────────────────────────────┐
│  [Sidebar]    [Chat Area]       │
│  - Conv 1     User: Hello       │
│  - Conv 2     Agent: Hi...      │
│  - Conv 3                        │
│              [Input....]         │
└─────────────────────────────────┘
```

Option B: Modal/overlay
```
                  ┌──────────────┐
                  │ Chat         │
                  │ User: Hello  │
                  │ Agent: Hi... │
                  │ [Input....]  │
                  └──────────────┘
```

Option C: Sidebar panel
```
┌──────────────────┬─────────────┐
│  Main Content    │ Chat        │
│                  │ User: ...   │
│                  │ Agent: ...  │
│                  │ [Input...]  │
└──────────────────┴─────────────┘
```

Your preference: _____________

---

## 11. Testing

### 11.1 What testing framework?
- [ ] Jest
- [ ] Vitest
- [ ] Other: _____________
- [ ] No tests yet

### 11.2 Do you use component testing?
- [ ] React Testing Library
- [ ] Cypress Component Testing
- [ ] Other: _____________
- [ ] No component tests yet

### 11.3 Do you use E2E testing?
- [ ] Cypress
- [ ] Playwright
- [ ] Other: _____________
- [ ] No E2E tests yet

---

## 12. Performance & Optimization

### 12.1 Do you use code splitting?
- [ ] Yes - route-based
- [ ] Yes - component-based
- [ ] No
- [ ] Unsure

### 12.2 Do you use lazy loading for components?
- [ ] Yes
- [ ] No
- [ ] Sometimes

### 12.3 Are there any performance constraints we should know about?
- Target devices: [ ] Desktop [ ] Mobile [ ] Both
- Performance budget: _____________
- Other constraints: _____________

---

## 13. File Locations

### 13.1 Where should we add the chat components?
Preferred location:
```
src/
├── components/
│   └── Chat/    <- Here?
```

Your preference:
```
(Paste your preferred structure)
```

### 13.2 Where do you keep service/API files?
```
(Paste your services folder structure)
```

### 13.3 Where do you keep hooks?
```
(Paste your hooks folder structure)
```

---

## 14. Deployment

### 14.1 Where will the frontend be deployed?
- [ ] Vercel
- [ ] Netlify
- [ ] AWS (S3 + CloudFront)
- [ ] Custom server
- [ ] Other: _____________

### 14.2 What's the expected production URL?
- Frontend: _____________
- Backend: _____________ (if known)

### 14.3 Will you use a reverse proxy or API gateway?
- [ ] Yes
- [ ] No
- [ ] Unsure

---

## 15. Additional Context

### 15.1 Are there any existing similar features we should match?
- [ ] Yes
- [ ] No

If yes, describe:
```
(What features should we match in terms of UX/UI?)
```

### 15.2 Do you have a design system or design files?
- [ ] Yes - Figma
- [ ] Yes - Other: _____________
- [ ] No - will design as we go

### 15.3 Any accessibility requirements?
- [ ] WCAG 2.1 Level A
- [ ] WCAG 2.1 Level AA
- [ ] WCAG 2.1 Level AAA
- [ ] No specific requirements
- [ ] Other: _____________

### 15.4 Any other constraints or requirements we should know about?
```
(Browser support, mobile requirements, offline support, etc.)
```

---

## How to Answer These Questions

### Option 1: Manual Answers
Simply fill in the blanks above and send back this document.

### Option 2: Use Claude in Your Repo (Recommended)
1. Copy this entire document
2. In your frontend repo, start Claude Code
3. Paste this prompt:
```
Please analyze this codebase and answer the following questions
about our frontend architecture. Be specific and include file paths
and code examples where relevant.

[Paste this FRONTEND_QUESTIONS.md file here]
```
4. Share Claude's responses back to us

---

## What Happens Next?

Once we receive your answers, we'll:

1. **Create framework-specific examples**
   - If you use Next.js App Router, we'll provide Next.js-specific code
   - If you use Redux, we'll show Redux integration patterns
   - etc.

2. **Provide custom integration code**
   - WebSocket hook tailored to your state management
   - Chat components matching your UI library
   - API service matching your data fetching pattern

3. **Identify potential issues**
   - CORS configuration
   - WebSocket proxy setup (for development)
   - Build configuration changes needed

4. **Optimize for your stack**
   - Performance optimizations
   - Bundle size considerations
   - Best practices for your framework

---

## Timeline

Please answer these questions and return them **as soon as possible** so we can:
- Provide you with customized integration code
- Start implementation without delays
- Address any architectural mismatches early

**Estimated time to complete:** 15-30 minutes

---

## Questions?

If any of these questions are unclear or you need clarification, please ask! We want to make sure we have accurate information to provide the best integration guidance.



# ANSWERS

# Frontend Architecture Answers - Photosphere Labs

**Document Date**: 2025-10-06
**Codebase Analyzed**: ps-labs-app (Photosphere Labs Analytics Platform)

---

## 1. Framework & Stack

### 1.1 What frontend framework are you using?
- [x] **React** (standalone, not Next.js)

### 1.2 What version?
- **Framework**: React 18.3.1
- **React version**: 18.3.1 (confirmed in `package.json:92`)
- **React DOM version**: 18.3.1

### 1.3 Are you using TypeScript?
- [x] **Yes**

**Details**:
- **TypeScript version**: 5.6.3 (confirmed in `package.json:129`)
- **Strict mode enabled**: Yes (based on `tsconfig.json`)
- **Configuration**: `tsconfig.json` at root
- **Path aliases configured**:
  - `@/*` → `./client/src/*`
  - `@shared/*` → `./shared/*`

**TypeScript Config** (`tsconfig.json:4-21`):
```json
{
  "compilerOptions": {
    "strict": true,
    "module": "ESNext",
    "lib": ["esnext", "dom", "dom.iterable"],
    "jsx": "preserve",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "moduleResolution": "node",
    "baseUrl": ".",
    "types": ["node", "vite/client"],
    "paths": {
      "@/*": ["./client/src/*"],
      "@shared/*": ["./shared/*"]
    }
  }
}
```

---

## 2. State Management

### 2.1 What state management solution are you using?
- [x] **TanStack Query (React Query)** - Primary state management for server state
- [x] **React Context** - Used minimally via component providers (TooltipProvider)
- [x] **Local component state** - useState/useEffect for component-level state

**No global state management library** (Redux, Zustand, etc.) - application relies on:
1. **TanStack Query** for server-side data caching and synchronization
2. **React hooks** for local component state
3. **Firebase Auth state** for authentication (managed via Firebase SDK)

### 2.2 File/folder structure for state management?

**Current Structure**:
```
client/src/
├── hooks/                          # Custom React hooks (state + logic)
│   ├── useAuth.ts                  # Authentication state (Firebase + TanStack Query)
│   ├── useFirestoreUser.ts         # Firestore user data state
│   ├── useAIInsights.ts            # AI insights state management
│   ├── useMetaRegionAIInsights.ts  # Meta region insights state
│   ├── useTrendingContentAIInsights.ts
│   ├── usePresignedUrl.ts          # S3 presigned URL state
│   ├── use-toast.ts                # Toast notification state
│   └── use-mobile.tsx              # Mobile detection state
├── lib/
│   ├── queryClient.ts              # TanStack Query client configuration
│   └── firebase.ts                 # Firebase state initialization
└── services/
    └── airbyteService.ts           # Airbyte service state/logic
```

**Key State Management Patterns**:

1. **Server State** (`lib/queryClient.ts:111-124`):
```typescript
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      queryFn: getQueryFn({ on401: "throw" }),
      refetchInterval: false,
      refetchOnWindowFocus: false,
      staleTime: Infinity,
      retry: false,
    },
  },
});
```

2. **Authentication State** (`hooks/useAuth.ts:6-81`):
```typescript
export function useAuth() {
  const [firebaseUser, setFirebaseUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [emailVerificationRequired, setEmailVerificationRequired] = useState(false);

  // Firebase auth state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChange((user) => {
      setFirebaseUser(user);
      // ... email verification logic
    });
    return () => unsubscribe?.();
  }, []);

  // Backend user data via TanStack Query
  const { data: userData } = useQuery({
    queryKey: ["/api/auth/user"],
    enabled: !!firebaseUser,
  });

  return {
    user: userData,
    firebaseUser,
    isLoading,
    isAuthenticated,
    canAccessPlatform,
  };
}
```

---

## 3. Routing & Navigation

### 3.1 What routing solution are you using?
- [x] **Wouter** (lightweight client-side routing, `wouter@3.3.5`)

**Not** React Router or Next.js routing - using Wouter for simplicity.

### 3.2 Where will the chat interface live?

**Current Routes** (`client/src/App.tsx:50-63`):
```typescript
<Switch>
  {!canAccessPlatform ? (
    <Route path="/" component={Landing} />
  ) : (
    <>
      <Route path="/">{() => <Dashboard />}</Route>
      <Route path="/connect">{() => <Dashboard initialView="connect" />}</Route>
    </>
  )}
  <Route path="/privacy-policy" component={PrivacyPolicy} />
  <Route path="/data-agreement" component={DataAgreement} />
  <Route path="/terms-of-service" component={TermsOfService} />
  <Route component={NotFound} />
</Switch>
```

**Recommended Chat Interface Location**:
- **Option 1** (Recommended): Dedicated route `/chat` or `/assistant`
- **Option 2**: Modal/overlay accessible from Dashboard navbar (more integrated UX)
- **Option 3**: Sidebar panel on Dashboard page

**Current Route Structure**:
- `/` - Landing page (unauthenticated) or Dashboard (authenticated)
- `/connect` - Dashboard with "connect" view (data source connections)
- `/privacy-policy`, `/data-agreement`, `/terms-of-service` - Legal pages

**Suggestion**: Add `/chat` route for dedicated chat interface, with option to open in modal from Dashboard.

---

## 4. Authentication

### 4.1 What authentication solution are you using?
- [x] **Firebase Auth** (Firebase 12.2.1)

**Methods Supported**:
- Email/Password authentication (with email verification required)
- Google OAuth sign-in

### 4.2 How do you access the current user ID?

**Client-Side** (`lib/firebase.ts:85-86`):
```typescript
import { auth } from "@/lib/firebase";

// Current user from Firebase
const firebaseUser = auth.currentUser;
const userId = firebaseUser?.uid;

// With React hook (recommended):
import { useAuth } from "@/hooks/useAuth";

function MyComponent() {
  const { firebaseUser, user } = useAuth();
  const userId = firebaseUser?.uid;  // Firebase UID
  const userData = user;              // Backend user data
}
```

**Getting Firebase ID Token** (`lib/queryClient.ts:18-28`):
```typescript
// In API requests (automatic via apiRequest function):
const auth = await import("./firebase").then(m => m.auth);
const user = auth.currentUser;

if (user) {
  const idToken = await user.getIdToken();
  headers.Authorization = `Bearer ${idToken}`;
}
```

**Complete Auth Pattern** (`hooks/useAuth.ts`):
```typescript
const {
  user,                    // Backend user data object
  firebaseUser,            // Firebase User object
  isLoading,               // Auth state loading
  isAuthenticated,         // Boolean: authenticated + verified
  emailVerificationRequired, // Boolean: needs email verification
  canAccessPlatform        // Boolean: fully authenticated and verified
} = useAuth();

// Access user ID:
const userId = firebaseUser?.uid;
const userEmail = firebaseUser?.email;
```

### 4.3 Do you have auth guards/protected routes?
- [x] **Yes**

**Implementation** (`client/src/App.tsx:16-47`):
```typescript
function Router() {
  const {
    isAuthenticated,
    isLoading,
    firebaseUser,
    emailVerificationRequired,
    canAccessPlatform
  } = useAuth();

  // Loading state
  if (isLoading) {
    return <LoadingSpinner />;
  }

  // Email verification guard
  if (firebaseUser && emailVerificationRequired) {
    return <EmailVerificationModal />;
  }

  // Route protection
  return (
    <Switch>
      {!canAccessPlatform ? (
        <Route path="/" component={Landing} />
      ) : (
        <>
          <Route path="/">{() => <Dashboard />}</Route>
          <Route path="/connect">{() => <Dashboard initialView="connect" />}</Route>
        </>
      )}
      {/* Public routes */}
      <Route path="/privacy-policy" component={PrivacyPolicy} />
      <Route path="/terms-of-service" component={TermsOfService} />
    </Switch>
  );
}
```

**Auth Guard Pattern**: Route-level guards using `canAccessPlatform` flag from `useAuth()` hook.

---

## 5. UI Components & Styling

### 5.1 What component library are you using?
- [x] **shadcn/ui** (built on Radix UI primitives)
- [x] **Radix UI** (low-level primitives - 20+ components installed)

**Full Component List** (from `package.json:34-60`):
- Accordion, Alert Dialog, Aspect Ratio, Avatar, Checkbox, Collapsible
- Context Menu, Dialog, Dropdown Menu, Hover Card, Label, Menubar
- Navigation Menu, Popover, Progress, Radio Group, Scroll Area
- Select, Separator, Slider, Slot, Switch, Tabs, Toast, Toggle, Tooltip

**Location**: `client/src/components/ui/` (50+ component files)

### 5.2 What styling approach?
- [x] **Tailwind CSS** (v3.4.17)

**Additional Styling Tools**:
- `class-variance-authority` (CVA) for component variants
- `clsx` and `tailwind-merge` for conditional class merging
- `tailwindcss-animate` for animations
- Framer Motion (for advanced animations)

**Tailwind Config**: Uses `@tailwindcss/vite` plugin for optimized builds

**Example Component Pattern** (`components/ui/toast.tsx:25-39`):
```typescript
const toastVariants = cva(
  "group pointer-events-auto relative flex w-full items-center...",
  {
    variants: {
      variant: {
        default: "border bg-background text-foreground",
        destructive: "destructive group border-destructive bg-destructive...",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)
```

### 5.3 Do you have existing chat/messaging UI components?
- [ ] **No** - No existing chat components

**Existing UI Components Available for Chat**:
- `Dialog` - For modal chat interface
- `ScrollArea` - For chat message scrolling
- `Avatar` - For user/AI avatars
- `Card` - For message bubbles
- `Input` / `Textarea` - For message input
- `Button` - For send button
- `Toast` - For notifications
- `Tooltip` - For contextual help

**Recommendation**: Build chat components in `client/src/components/chat/` using existing shadcn/ui primitives.

---

## 6. Data Fetching

### 6.1 What data fetching library are you using?
- [x] **TanStack Query (React Query)** v5.60.5
- [x] **Axios** v1.12.2 (available but not primary)
- [x] **Native fetch** (wrapped in custom `apiRequest` function)

**Primary Pattern**: Native fetch wrapped with TanStack Query hooks

### 6.2 Example of a typical API call in your codebase:

**Pattern 1: TanStack Query Hook** (`hooks/useAuth.ts:51-56`):
```typescript
const { data: userData, isLoading, error } = useQuery({
  queryKey: ["/api/auth/user"],
  retry: false,
  refetchOnWindowFocus: false,
  enabled: !!firebaseUser, // Only fetch if user is authenticated
});
```

**Pattern 2: Custom Hook with apiRequest** (`hooks/useAIInsights.ts:38-63`):
```typescript
const generateInsights = async (data: AIInsightsData) => {
  setIsLoading(true);
  setError(null);

  try {
    const response = await apiRequest('POST', '/api/ai/insights', { data });

    if (!response.ok) {
      const errorData = await response.json();
      setError(errorData.error || `Server error: ${response.status}`);
      return;
    }

    const result: AIInsightsResponse = await response.json();
    setInsights(result.insights);
    setMetadata(result.metadata);
  } catch (err) {
    setError(err instanceof Error ? err.message : 'Failed to generate insights');
  } finally {
    setIsLoading(false);
  }
};
```

**apiRequest Function** (`lib/queryClient.ts:11-64`):
```typescript
export async function apiRequest(
  method: string,
  url: string,
  data?: unknown,
  timeoutMs?: number,
): Promise<Response> {
  // Get Firebase auth token
  const auth = await import("./firebase").then(m => m.auth);
  const user = auth.currentUser;
  const headers: Record<string, string> = data ? { "Content-Type": "application/json" } : {};

  if (user) {
    const idToken = await user.getIdToken();
    headers.Authorization = `Bearer ${idToken}`;
  }

  // Timeout handling
  const controller = new AbortController();
  const timeout = timeoutMs || clientConfig.api.timeouts.requestMs;
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(fullUrl, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
      credentials: "include",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    await throwIfResNotOk(res);
    return res;
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  }
}
```

**Key Features**:
- ✅ Automatic Firebase token injection
- ✅ Request timeout handling (default 30s)
- ✅ Error handling with typed responses
- ✅ Credentials included for CORS
- ✅ Centralized error throwing

---

## 7. Real-Time Features

### 7.1 Do you currently use WebSockets anywhere?
- [ ] **No**

### 7.2 Do you use Server-Sent Events (SSE)?
- [ ] **No**

### 7.3 Do you have any real-time subscriptions (Firestore, Supabase, etc.)?
- [x] **Yes** - Firebase Firestore real-time listeners

**Service**: Firebase Firestore
**Example**: `hooks/useAuth.ts:12-48`

```typescript
useEffect(() => {
  const unsubscribe = onAuthStateChange((user) => {
    setFirebaseUser(user);
    setIsLoading(false);
  });

  return () => {
    if (unsubscribe) {
      unsubscribe();
    }
  };
}, []);
```

**Real-Time Use Cases**:
1. **Authentication State** - Firebase Auth state changes (`lib/firebase.ts:96-98`)
2. **Potential Firestore Collections** (not currently active in code review):
   - User profile updates
   - AI insights consumption logs
   - Analytics data updates

**Note**: While Firestore is initialized (`lib/firebase.ts:86`), no active Firestore real-time listeners were found in the current codebase besides auth state.

---

## 8. Build & Development

### 8.1 What's your build tool?
- [x] **Vite** v5.4.19

**Configuration**: `vite.config.ts`

### 8.2 Development server port?
- **Default port**: 5173 (Vite default)
- **Backend API port**: 3001
- **Typical URL**: `http://localhost:5173`

**Scripts** (`package.json:10-12`):
```json
{
  "dev": "NODE_ENV=development tsx server/index.ts",    // Backend only
  "dev:client": "vite",                                  // Frontend only
  "dev:server": "NODE_ENV=development tsx server/index.ts"
}
```

**Recommended Workflow**:
```bash
# Terminal 1: Frontend (Vite dev server)
npm run dev:client      # http://localhost:5173

# Terminal 2: Backend (Express/Vercel dev)
vercel dev              # http://localhost:3001
```

### 8.3 Environment variables pattern?

**Pattern**:
```
.env.local          # Development (gitignored, but CURRENTLY TRACKED - SECURITY ISSUE!)
.env.test           # Test environment
```

**Variable Prefix**: `VITE_` for client-side variables

**Example** (from `.env.local`):
```bash
# Client-side (accessible in frontend)
VITE_FIREBASE_API_KEY="AIzaSyAbNGzZPZntL0RL3QBsQWO-MIbvlG-5XeQ"
VITE_FIREBASE_APP_ID="1:235879909080:web:669c4bc61795fcf40239ad"
VITE_FIREBASE_AUTH_DOMAIN="ps-labs-app-dev.firebaseapp.com"
VITE_FIREBASE_MEASUREMENT_ID="G-86PFW9STGK"
VITE_AIRBYTE_ORGANIZATION_ID="261f939a-5e90-47b8-82b0-f78917a40976"

# Server-side only (NOT accessible in frontend)
OPENAI_API_KEY=sk-proj-...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

**⚠️ CRITICAL SECURITY ISSUE**: `.env.local` is currently tracked in git and contains real secrets! (See `potential_vulns.md` SEC-001)

**Access in Frontend Code**:
```typescript
// ❌ This pattern is NOT used - hardcoded configs instead
const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;

// ✅ Actual pattern - environment-based config selection
const environment = getCurrentEnvironment(); // 'development' | 'staging' | 'production'
const config = firebaseConfigs[environment];  // Hardcoded configs
```

**Environment Detection** (`lib/firebase.ts:6-29`):
```typescript
function getCurrentEnvironment(): 'development' | 'staging' | 'production' {
  // Vercel preview deployments
  if (window.location.hostname.includes('vercel.app')) {
    if (window.location.hostname.includes('-git-')) {
      return 'staging';
    }
    return 'production';
  }

  // Local development
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'development';
  }

  // Custom domain
  if (window.location.hostname.includes('photospherelabs.com')) {
    return 'production';
  }

  return 'development';
}
```

---

## 9. Error Handling & Notifications

### 9.1 How do you show notifications/toasts to users?
- [x] **Radix UI Toast** (custom hook)

**Implementation**:
- Component: `components/ui/toaster.tsx` and `components/ui/toast.tsx`
- Hook: `hooks/use-toast.ts`
- Provider: `<Toaster />` in `App.tsx:72`

**Usage Example**:
```typescript
import { useToast } from "@/hooks/use-toast";

function MyComponent() {
  const { toast } = useToast();

  const showNotification = () => {
    toast({
      title: "Success",
      description: "Your data has been saved",
      variant: "default", // or "destructive"
    });
  };
}
```

### 9.2 Do you have a global error boundary?
- [ ] **No** - No global error boundary currently implemented

**Recommendation**: Add React Error Boundary for production error handling.

### 9.3 How do you handle loading states?

**Pattern 1: TanStack Query Loading State**:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["/api/auth/user"],
});

if (isLoading) {
  return <LoadingSpinner />;
}
```

**Pattern 2: Custom Hook Loading State** (`hooks/useAIInsights.ts:33-36`):
```typescript
const [isLoading, setIsLoading] = useState(false);

const generateInsights = async (data) => {
  setIsLoading(true);
  try {
    // ... API call
  } finally {
    setIsLoading(false);
  }
};
```

**Pattern 3: Route-Level Loading** (`App.tsx:20-29`):
```typescript
function Router() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }
}
```

**Loading UI Components**:
- Spinner: Tailwind `animate-spin` utility
- Progress bars: Radix UI Progress component available
- Skeleton loaders: Not currently implemented (consider adding)

---

## 10. Conversation/Chat Requirements

### 10.1 Should users be able to see past conversations?
- [ ] **Unsure** - Not currently defined

**Recommendation**: Yes, show list of past conversations for continuity and context.

### 10.2 Should conversations persist across sessions?
- [ ] **Unsure** - Not currently defined

**Recommendation**: Yes, load from backend (Firestore collection: `chat_conversations/{userId}/messages`)

### 10.3 Should users be able to:
- [ ] Start a new conversation while keeping old ones
- [ ] Delete conversations
- [ ] Search through past conversations
- [ ] Share conversations with others
- [ ] Export conversation history

**Recommendation**: Start with basic features (new conversation, view history) then add advanced features based on user feedback.

### 10.4 Layout preference for chat interface?

**Recommendation: Option C - Sidebar Panel**
```
┌──────────────────┬─────────────┐
│  Dashboard       │ Chat        │
│  [Analytics]     │ User: Help  │
│  [Charts]        │ AI: Sure... │
│  [Data]          │             │
│                  │ [Input...]  │
└──────────────────┴─────────────┘
```

**Rationale**:
1. **Context-Aware**: Chat can reference dashboard data
2. **Non-Intrusive**: Doesn't cover main content
3. **Always Accessible**: No need to navigate away
4. **Similar to Existing UI**: Dashboard already has sidebar navigation pattern

**Alternative**: Modal overlay for quick questions, sidebar for extended conversations.

**Implementation Location**:
```
client/src/components/
├── chat/
│   ├── ChatSidebar.tsx          # Main chat container
│   ├── ChatMessageList.tsx      # Message history
│   ├── ChatMessage.tsx          # Individual message bubble
│   ├── ChatInput.tsx            # Message input field
│   └── ConversationList.tsx     # Past conversations
```

---

## 11. Testing

### 11.1 What testing framework?
- [ ] **No tests yet**

**Available but not configured**:
- Vitest would be natural fit (Vite ecosystem)
- Jest compatibility layer available

### 11.2 Do you use component testing?
- [ ] **No component tests yet**

**Recommendation**: React Testing Library + Vitest

### 11.3 Do you use E2E testing?
- [ ] **No E2E tests yet**

**Recommendation**: Playwright (modern, fast, Vercel-compatible)

---

## 12. Performance & Optimization

### 12.1 Do you use code splitting?
- [x] **Yes - route-based** (implicit with Vite)
- [ ] **Component-based** - Not currently implemented

Vite automatically code-splits routes and chunks.

### 12.2 Do you use lazy loading for components?
- [ ] **No** - Not currently implemented

**Recommendation**: Add lazy loading for heavy components:
```typescript
const Dashboard = lazy(() => import("@/pages/dashboard"));
const MetaAdsRegion = lazy(() => import("@/components/meta-ads-region"));
```

### 12.3 Are there any performance constraints we should know about?

**Target devices**:
- [x] Desktop
- [x] Mobile
- [x] Both

**Mobile Optimization**: `hooks/use-mobile.tsx` hook for responsive design

**Performance Considerations**:
- **Charts**: Heavy chart rendering (Recharts) - consider virtualization
- **AI Insights**: Long-running API calls (OpenAI) - implement timeout UX
- **Data Tables**: Large datasets - implement pagination
- **Firestore**: Real-time listeners can accumulate - proper cleanup needed

**Performance Budget**: Not explicitly defined

**Other constraints**:
- Must work on Safari (iOS), Chrome, Firefox
- Tailwind CSS used extensively (CSS bundle size to monitor)
- Many Radix UI components (JS bundle size ~200KB+)

---

## 13. File Locations

### 13.1 Where should we add the chat components?

**Recommended Structure**:
```typescript
client/src/
├── components/
│   ├── chat/                      # ← ADD HERE
│   │   ├── ChatSidebar.tsx        # Main chat container
│   │   ├── ChatMessageList.tsx    # Scrollable message list
│   │   ├── ChatMessage.tsx        # Individual message bubble
│   │   ├── ChatInput.tsx          # Message input with send button
│   │   ├── ConversationList.tsx   # List of past conversations
│   │   ├── ChatHeader.tsx         # Chat title and controls
│   │   └── index.ts               # Barrel export
│   ├── layout/                    # Existing layout components
│   ├── ui/                        # Existing shadcn/ui components
│   ├── meta-ads-region/           # Existing feature components
│   ├── product-performance/       # Existing feature components
│   └── trending-content/          # Existing feature components
```

**Pattern**: Feature-based organization (matches existing structure)

### 13.2 Where do you keep service/API files?

**Current Structure**:
```typescript
client/src/
├── services/
│   └── airbyteService.ts          # Airbyte API calls
├── hooks/                         # Custom hooks (contain API logic)
│   ├── useAIInsights.ts           # AI API calls
│   ├── useMetaRegionAIInsights.ts
│   ├── useTrendingContentAIInsights.ts
│   └── usePresignedUrl.ts         # S3 API calls
└── lib/
    ├── queryClient.ts             # API request utilities
    └── firebase.ts                # Firebase service initialization
```

**Recommendation for Chat**:
```typescript
client/src/
├── services/
│   ├── airbyteService.ts
│   └── chatService.ts             # ← ADD: Chat API calls
└── hooks/
    └── useChat.ts                 # ← ADD: Chat state management hook
```

**Pattern**: Services folder for raw API calls, hooks folder for state + API integration.

### 13.3 Where do you keep hooks?

**Location**: `client/src/hooks/`

**Current Hooks**:
```
hooks/
├── useAuth.ts                     # Authentication state
├── useFirestoreUser.ts            # Firestore user data
├── useAIInsights.ts               # Product performance AI
├── useMetaRegionAIInsights.ts     # Meta ads AI
├── useTrendingContentAIInsights.ts# Content AI
├── usePresignedUrl.ts             # S3 URLs
├── use-toast.ts                   # Toast notifications
└── use-mobile.tsx                 # Mobile detection
```

**Add for Chat**:
```
hooks/
└── useChat.ts                     # Chat state and API integration
```

---

## 14. Deployment

### 14.1 Where will the frontend be deployed?
- [x] **Vercel**

**Configuration**: `vercel.json` in root

### 14.2 What's the expected production URL?

**Frontend URLs**:
- **Production**: `https://www.photospherelabs.com`
- **Staging/Preview**: `https://ps-labs-app-git-[branch].vercel.app`
- **Development**: `http://localhost:5173`

**Backend URLs**:
- **Production API**: `https://www.photospherelabs.com/api/*` (same domain, serverless functions)
- **Development API**: `http://localhost:3001/api/*`

**Environment Detection** (`lib/firebase.ts:6-29`):
```typescript
function getCurrentEnvironment(): 'development' | 'staging' | 'production' {
  if (window.location.hostname.includes('vercel.app')) {
    return window.location.hostname.includes('-git-') ? 'staging' : 'production';
  }
  if (window.location.hostname === 'localhost') {
    return 'development';
  }
  if (window.location.hostname.includes('photospherelabs.com')) {
    return 'production';
  }
  return 'development';
}
```

### 14.3 Will you use a reverse proxy or API gateway?
- [x] **Yes** - Vercel rewrites (acts as reverse proxy)

**Vercel Rewrites** (`vercel.json:12-21`):
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Pattern**: All `/api/*` requests are routed to Vercel serverless functions. Frontend served as static SPA with client-side routing fallback.

---

## 15. Additional Context

### 15.1 Are there any existing similar features we should match?
- [x] **Yes**

**AI Insights Feature** (existing):
- User clicks "Get AI Insights" button
- Loading state with spinner
- AI response shown in expandable panel
- Markdown formatting supported
- Token usage metadata displayed

**Pattern to Match for Chat**:
```typescript
// Similar to: components/product-performance/ProductPerformance.tsx
<Card>
  <CardHeader>
    <CardTitle>AI Assistant</CardTitle>
  </CardHeader>
  <CardContent>
    {isLoading && <LoadingSpinner />}
    {insights && <MarkdownContent>{insights}</MarkdownContent>}
    {error && <ErrorMessage>{error}</ErrorMessage>}
  </CardContent>
</Card>
```

**UI Patterns to Match**:
- Card-based layouts
- Indigo/purple color scheme (primary: `indigo-600`)
- Gradient backgrounds for headers
- shadcn/ui component styling
- Responsive mobile design

### 15.2 Do you have a design system or design files?
- [ ] **No** - will design as we go

**Existing Design Tokens** (from Tailwind config):
- **Primary Color**: Indigo (various shades)
- **Typography**: System fonts
- **Spacing**: Tailwind default scale
- **Border Radius**: Moderate (rounded corners)
- **Shadows**: Tailwind default elevation

**Component Library**: shadcn/ui provides consistent design language

### 15.3 Any accessibility requirements?
- [ ] **No specific requirements** mentioned

**Current Accessibility Features**:
- Radix UI primitives (ARIA-compliant)
- Keyboard navigation support (Radix UI default)
- Focus management (Radix UI default)

**Recommendation**: Target WCAG 2.1 Level AA for chat interface:
- Keyboard-accessible message input
- Screen reader announcements for new messages
- Proper ARIA labels for all interactive elements
- Color contrast ratios 4.5:1 minimum

### 15.4 Any other constraints or requirements we should know about?

**Browser Support**:
- Modern browsers (ES2020+)
- Mobile Safari (iOS)
- Chrome, Firefox, Edge

**Offline Support**:
- Not currently implemented
- Firebase Auth has offline token caching
- No service worker or offline-first architecture

**Mobile Requirements**:
- Responsive design (mobile-first)
- Touch-friendly UI (Radix UI optimized)
- Mobile detection hook available (`use-mobile.tsx`)

**Other Constraints**:
- **Firebase Limitations**:
  - Real-time listeners limit (100 concurrent per user)
  - Firestore read/write quotas
- **OpenAI Costs**:
  - Token usage tracking implemented
  - Cost monitoring required for chat (longer conversations = higher costs)
- **Vercel Limits**:
  - Serverless function timeout: 10s (hobby), 60s (pro)
  - Function size limits
  - Edge network limitations

---

## 16. Deployment Strategy

### 16.1 What are the environments for development and deployment?

**Environments**:

1. **Development** (`localhost`)
   - Frontend: `http://localhost:5173` (Vite)
   - Backend: `http://localhost:3001` (Express) or `vercel dev`
   - Firebase: `ps-labs-app-dev` project
   - S3 Bucket: `ps-labs-dev-raw-v1`
   - Data Retention: 30 days

2. **Staging/Preview** (Vercel preview deployments)
   - URL: `https://ps-labs-app-git-[branch].vercel.app`
   - Firebase: `ps-labs-app-prod` project (shared with production)
   - S3 Bucket: `ps-labs-prod-raw-v1`
   - Data Retention: 90 days
   - Trigger: Every git branch push

3. **Production** (`photospherelabs.com`)
   - URL: `https://www.photospherelabs.com`
   - Firebase: `ps-labs-app-prod` project
   - S3 Bucket: `ps-labs-prod-raw-v1`
   - Data Retention: 365 days
   - Trigger: Merge to `main` branch

**Environment Detection Logic** (`lib/firebase.ts:6-29`):
```typescript
function getCurrentEnvironment(): 'development' | 'staging' | 'production' {
  // Vercel preview: hostname includes 'vercel.app' and '-git-'
  if (window.location.hostname.includes('vercel.app')) {
    if (window.location.hostname.includes('-git-')) {
      return 'staging';
    }
    return 'production';
  }

  // Local development
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'development';
  }

  // Production custom domain
  if (window.location.hostname.includes('photospherelabs.com')) {
    return 'production';
  }

  return 'development';
}
```

### 16.2 What is the deployment and hosting strategy for the webapp?

**Deployment Flow**:
```
Developer → Git Push → Vercel CI/CD → Deploy

Branch Mapping:
├── main              → Production (www.photospherelabs.com)
├── develop           → Preview (ps-labs-app-git-develop.vercel.app)
└── feature/*         → Preview (ps-labs-app-git-feature-*.vercel.app)
```

**Vercel Configuration** (`vercel.json`):
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": "dist/public",
  "installCommand": "npm install",
  "framework": null,
  "functions": {
    "api/**/*.ts": {
      "runtime": "@vercel/node@5.3.24"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/$1"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

**Build Process**:
1. **Frontend Build**: `vite build` → `dist/public/` (static files)
2. **API Functions**: Vercel automatically builds TypeScript serverless functions in `api/`
3. **Static Hosting**: Vercel CDN serves frontend
4. **API Routing**: Vercel routes `/api/*` to serverless functions

**Hosting Architecture**:
- **Frontend**: Static files on Vercel CDN (global edge network)
- **Backend**: Vercel Serverless Functions (Node.js 22.x)
- **Database**: Firebase Firestore (Google Cloud)
- **Storage**: AWS S3 (raw data files)
- **Authentication**: Firebase Auth (Google Cloud)

**Deployment Strategy**:
- **Automatic**: Every git push triggers deployment
- **Preview URLs**: Every branch gets unique URL
- **Rollback**: Instant rollback via Vercel dashboard
- **Environment Variables**: Managed via Vercel dashboard (production) or `.env.local` (development)

**CI/CD**:
- No GitHub Actions currently (Vercel handles all CI/CD)
- ⚠️ Old GitHub workflows exist but are unused (should be deleted - see ARCH-003 in project_management.md)

---

## Summary & Recommendations for Chat Integration

### Technology Match
✅ **Excellent fit for chat integration**:
- Modern React + TypeScript stack
- TanStack Query for server state (perfect for message sync)
- Firebase Auth already integrated (user context)
- Radix UI + shadcn/ui (chat UI components ready)
- Vercel serverless (easy WebSocket/SSE setup)

### Recommended Chat Architecture

**1. Components** (`client/src/components/chat/`):
```typescript
ChatSidebar.tsx          // Main container (sidebar or modal)
ChatMessageList.tsx      // Scrollable message history
ChatMessage.tsx          // Individual message bubble
ChatInput.tsx            // Input field with send button
ConversationList.tsx     // Past conversations sidebar
ChatProvider.tsx         // Context provider for chat state
```

**2. State Management**:
```typescript
// hooks/useChat.ts
export function useChat(conversationId?: string) {
  const { user } = useAuth();

  // TanStack Query for message history
  const { data: messages } = useQuery({
    queryKey: ["/api/chat/messages", conversationId],
    enabled: !!conversationId,
  });

  // Mutation for sending messages
  const sendMessage = useMutation({
    mutationFn: (message: string) =>
      apiRequest('POST', '/api/chat/send', { conversationId, message }),
  });

  return { messages, sendMessage };
}
```

**3. API Integration**:
```typescript
// services/chatService.ts
export async function sendChatMessage(conversationId: string, message: string) {
  return apiRequest('POST', '/api/chat/send', {
    conversationId,
    message,
    userId: auth.currentUser?.uid
  });
}

export async function getConversations() {
  return apiRequest('GET', '/api/chat/conversations');
}
```

**4. Real-Time Updates** (options):
- **Option A**: Polling with TanStack Query (`refetchInterval: 5000`)
- **Option B**: Server-Sent Events (SSE) for streaming responses
- **Option C**: Firestore real-time listeners (leverage existing Firebase)

**5. Data Schema** (Firestore):
```typescript
// collections/chat_conversations/{conversationId}
{
  id: string;
  userId: string;
  title: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

// collections/chat_messages/{messageId}
{
  id: string;
  conversationId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Timestamp;
  tokens?: number;
}
```

### Integration Checklist

- [ ] Add chat components to `client/src/components/chat/`
- [ ] Create `useChat` hook in `client/src/hooks/`
- [ ] Add `chatService.ts` in `client/src/services/`
- [ ] Create backend API endpoints in `api/chat/`
- [ ] Set up Firestore collections for chat data
- [ ] Add route `/chat` or integrate as sidebar in Dashboard
- [ ] Implement real-time message streaming (SSE recommended)
- [ ] Add conversation history persistence
- [ ] Implement token usage tracking (similar to existing AI insights)
- [ ] Add rate limiting for chat API (prevent abuse)
- [ ] Mobile-optimize chat interface
- [ ] Add accessibility features (keyboard nav, ARIA labels)

---


