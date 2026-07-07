# 📗 Volume 2: Nexora AI — Frontend Architecture Deep Dive

> **Focus:** Next.js 15, all 14 components, state management, API calls, routing  
> **Path:** `D:\Nexora-AI\apps\frontend\src\`

---

## 🏛️ Frontend Folder Structure

```
src/
├── app/                          ← Next.js App Router pages
│   ├── layout.tsx                ← Root layout (fonts, metadata)
│   ├── globals.css               ← Global styles + CSS variables
│   ├── page.tsx                  ← Login/Register page (route: /)
│   └── chat/
│       └── page.tsx              ← Main workspace page (route: /chat)
│
├── components/                   ← 14 UI components
│   ├── chat-sidebar.tsx          ← Left panel (conversations, nav)
│   ├── chat-area.tsx             ← Main chat window (send/stream)
│   ├── chat-message.tsx          ← Individual message bubble (markdown)
│   ├── knowledge-area.tsx        ← KB management + document upload
│   ├── analytics-area.tsx        ← Usage charts, metrics
│   ├── agent-studio.tsx          ← Multi-agent control panel
│   ├── ml-area.tsx               ← Fine-tuning, training UI
│   ├── sql-studio.tsx            ← Natural language → SQL
│   ├── python-studio.tsx         ← Python code agent
│   ├── email-studio.tsx          ← AI email composer
│   ├── calendar-studio.tsx       ← Smart calendar
│   ├── eval-dashboard.tsx        ← Model evaluation
│   ├── report-area.tsx           ← Report generation
│   └── agent-metrics.tsx         ← Agent performance metrics
│
├── services/
│   └── api-service.ts            ← ALL backend API calls (326 lines)
│
├── stores/
│   └── chat-store.ts             ← Zustand global state (5985 bytes)
│
└── types/
    └── chat.ts                   ← TypeScript types (User, Message, etc.)
```

---

## 🔀 Routing Architecture (App Router)

```
/                   → page.tsx       ← Login / Register
/chat               → chat/page.tsx  ← Main workspace
```

**Page transition flow:**
```
User opens app → / page
  Token exists in localStorage? → redirect to /chat
  No token? → Show login form
  Login success → store token → redirect to /chat
```

---

## 🗂️ chat/page.tsx — Workspace Orchestrator

```typescript
// Key responsibilities:
1. Token hydration from localStorage on mount
2. Auth guard: if no token → redirect to /
3. Fetch current user + workspaces on load
4. If 0 workspaces → auto-create "My AI Workspace"
5. Fetch folders + conversations for active workspace
6. Render view based on activeView from Zustand store

// activeView controls which component renders:
"chat"      → <ChatArea />
"knowledge" → <KnowledgeArea />
"analytics" → <AnalyticsArea />
"agents"    → <AgentStudio />
"sql"       → <SQLStudio />
"python"    → <PythonStudio />
"email"     → <EmailStudio />
"calendar"  → <CalendarStudio />
"eval"      → <EvalDashboard />
"ml"        → <MLArea />
"report"    → <ReportArea />
```

---

## 💬 chat-area.tsx — Chat Window (Main Component)

```typescript
// State:
inputVal       ← current textarea value
errorMsg       ← error display
kbSelectorOpen ← KB dropdown state

// From Zustand store:
activeConversation, messages, isStreaming
selectedChatKb, groundingEnabled

// handleSend() flow:
1. If no activeConversation → create new conversation (API call)
2. setActiveConversation(newConvo)
3. addMessage({ role: "user", content: prompt })
4. addMessage({ role: "assistant", content: "" })  ← empty placeholder
5. apiService.streamChat(...)
   - onToken: accumulatedText += token → updateLastMessageContent(text)
   - onSources: updateLastMessageSources(sources)
   - onError: setErrorMsg(...)
```

---

## 💬 chat-message.tsx — Message Renderer

```typescript
// Two rendering modes:
isUser = true  → plain <p> tag (user messages)
isUser = false → <ReactMarkdown> with remark-gfm

// ReactMarkdown handles:
✅ # ## ### #### headings
✅ **bold**, *italic*
✅ - bullet lists, 1. numbered lists
✅ | tables |
✅ `inline code`
✅ ```code blocks``` with copy button
✅ > blockquotes
✅ --- horizontal rules

// Custom components:
<pre> → Custom code block with copy button + language label
<code> → Inline code with indigo styling

// Streaming trick:
content = ""    → shows "Thinking..." animation
content = "..." → renders markdown
```

---

## 🏪 chat-store.ts — Zustand Global State

```typescript
// State shape:
{
  // Auth
  token: string | null
  user: User | null
  
  // Workspace
  workspaces: Workspace[]
  activeWorkspace: Workspace | null
  folders: Folder[]
  
  // Conversations
  conversations: Conversation[]
  activeConversation: Conversation | null
  
  // Messages
  messages: Message[]
  isStreaming: boolean
  
  // Knowledge Base
  knowledgeBases: KnowledgeBase[]
  selectedChatKb: KnowledgeBase | null
  groundingEnabled: boolean
  
  // UI
  activeView: string   ← controls which panel shows
  sidebarOpen: boolean
  documents: KnowledgeDocument[]
}

// Key actions:
setToken()              ← save JWT
addMessage()            ← add to messages array
updateLastMessageContent() ← streaming token append
setIsStreaming()        ← loading state
setActiveConversation() ← switch conversation
logout()                ← clear all state + localStorage
```

---

## 🌐 api-service.ts — All API Functions

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL 
  || "https://liking-follow-groggy.ngrok-free.dev"

// Axios client with interceptors:
// - Request: Attach "Authorization: Bearer {token}"
// - Response: 401 → auto logout

// Functions:
register(full_name, email, password)
login(username, password) → returns token
fetchCurrentUser() → User
fetchWorkspaces() → Workspace[]
createWorkspace(name)
fetchFolders(workspaceId) → Folder[]
createFolder(name, workspaceId)
fetchConversations(workspaceId) → Conversation[]
createConversation(title, workspaceId)
deleteConversation(id, workspaceId)
fetchMessages(conversationId) → Message[]

// Main streaming function:
streamChat(
  conversationId, messageText, workspaceId,
  knowledgeBaseId, grounded,
  onToken, onSources, onError
)
  → Uses fetch() not axios (SSE streaming)
  → ReadableStream + TextDecoder
  → Parses "data: {...}" lines
  → Calls onToken for each content token
  → After stream done: fetchMessages() to sync DB state

// Knowledge Base:
fetchKnowledgeBases(workspaceId)
createKnowledgeBase(workspaceId, title, description)
deleteKnowledgeBase(workspaceId, kbId)
fetchDocuments(kbId)
uploadDocument(kbId, file, onProgress)
deleteDocument(kbId, docId)
retrieveSemanticChunks(workspaceId, kbId, query, topK)
```

---

## 🎨 Design System (Tailwind + CSS Variables)

```css
/* globals.css CSS Variables */
--background: #09090b        ← Near-black background
--foreground: #f4f4f5        ← Near-white text
--card: zinc-900             ← Card background
--border: zinc-800           ← Subtle borders
--primary: indigo-600        ← Main accent color
--sidebar-bg: zinc-950       ← Sidebar darker

/* Typography: System fonts */
/* Dark mode: always-on (no toggle needed) */
```

**Key UI patterns:**
- Glassmorphism: `backdrop-blur` on headers
- Micro-animations: `animate-spin`, `transition`
- Code blocks: zinc-950 bg + monospace font
- AI messages: `prose prose-invert` (Tailwind typography)

---

## ⚙️ next.config.ts — Important Config

```typescript
const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    "react-markdown", "remark-gfm", "unified",
    "micromark", "mdast-util-from-markdown",
    // ... 18 ESM packages
  ],
  // WHY: react-markdown is ESM-only.
  // Next.js needs these transpiled to CommonJS.
}
```

---

## 📦 package.json Dependencies

```json
// Core
"next": "15.x",
"react": "19.x",
"typescript": "5.x",

// State & API
"zustand": "^4.x",
"axios": "^1.x",

// UI
"lucide-react": icons,
"tailwindcss": "^3.x",
"@tailwindcss/typography": prose classes,

// Markdown
"react-markdown": "^9.x",   ← ESM only
"remark-gfm": "^4.x",       ← GitHub Flavored Markdown

// Styling
"tailwind-merge": utilities
```

---

## 🔐 .env.local

```bash
NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok-free.app
# Change this every time Colab restarts and ngrok gives new URL
```

---

*Volume 2 of 5 | Next → Volume 3: Backend Architecture*
