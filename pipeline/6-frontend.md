# Fase 6: Frontend Implementation

## 📋 Objetivo
Desenhar arquitetura do frontend React com streaming real-time, histórico conversacional e upload de documentos.

## 🎯 Deliverables

### D6.1 Component Architecture
- [ ] Component hierarchy diagram
- [ ] State management architecture
- [ ] Custom hooks design

### D6.2 UI Mockups
- [ ] Chat interface mockup
- [ ] Document upload interface
- [ ] Admin dashboard mockup

### D6.3 Frontend Starter Code
- [ ] Project setup (Next.js + TypeScript)
- [ ] Main page structure
- [ ] Reusable components
- [ ] API client integration

### D6.4 Streaming Implementation
- [ ] SSE parser
- [ ] Token streaming to DOM
- [ ] Cursor positioning

## 🏗️ Component Structure

```
App
├─ Layout
│  ├─ Navbar (user, settings, logout)
│  └─ Sidebar (conversations list, new chat)
├─ Pages
│  ├─ ChatPage
│  │  ├─ ChatWindow
│  │  │  ├─ MessageList
│  │  │  │  └─ MessageBubble (with citations)
│  │  │  └─ InputBox
│  │  │     └─ DocumentUploader
│  │  └─ ConversationInfo
│  ├─ DocumentsPage
│  │  ├─ DocumentList
│  │  └─ DocumentUploadZone
│  ├─ AdminPage
│  │  ├─ UsageChart
│  │  ├─ ConfigForm
│  │  └─ ModelSelector
│  └─ AuthPage
│     ├─ LoginForm
│     └─ SignupForm
└─ Common
   ├─ Markdown (with syntax highlighting)
   ├─ CodeBlock
   └─ LoadingSpinner
```

## 🎯 State Management (Zustand)

```typescript
// stores/useChat.ts
interface ChatStore {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  loadConversations: () => Promise<void>;
  createConversation: (title: string) => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  cancelStreaming: () => void;
  
  // UI State
  showDocumentUpload: boolean;
  setShowDocumentUpload: (show: boolean) => void;
}
```

## 📡 Streaming Implementation

```typescript
// hooks/useStreamingChat.ts
export function useStreamingChat() {
  const [currentMessage, setCurrentMessage] = useState("");
  const messageRef = useRef<HTMLDivElement>(null);
  
  const streamResponse = async (query: string) => {
    const response = await fetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");
      
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = JSON.parse(line.slice(6));
          
          if (data.type === "token") {
            // Append token to message
            setCurrentMessage((prev) => prev + data.content);
            
            // Scroll to bottom
            if (messageRef.current) {
              messageRef.current.scrollIntoView({ behavior: "smooth" });
            }
          } else if (data.type === "citations") {
            // Store citations for later display
            setCitations(data.citations);
          } else if (data.type === "done") {
            // Finalize message
            addMessageToHistory(currentMessage, data.metadata);
          }
        }
      }
    }
  };
  
  return { streamResponse, currentMessage };
}
```

## 💬 Message Bubble with Streamed Content

```tsx
// components/MessageBubble.tsx
export function MessageBubble({ message }: { message: Message }) {
  return (
    <div className={`message message-${message.role}`}>
      <div className="message-content">
        <Markdown content={message.content} />
      </div>
      
      {message.role === "assistant" && message.citations && (
        <div className="citations">
          <h4>Sources</h4>
          {message.citations.map((citation) => (
            <div key={citation.documentId} className="citation">
              <a href={citation.url} target="_blank">
                {citation.title}
              </a>
              <p>{citation.preview}...</p>
            </div>
          ))}
        </div>
      )}
      
      <div className="message-meta">
        <small>{formatDate(message.createdAt)}</small>
        {message.modelUsed && <small> • {message.modelUsed}</small>}
      </div>
    </div>
  );
}
```

## 📤 Document Upload

```tsx
// components/DocumentUploader.tsx
export function DocumentUploader() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  
  const handleUpload = async (files: File[]) => {
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("tenantId", getCurrentTenantId());
      
      const xhr = new XMLHttpRequest();
      
      // Track progress
      xhr.upload.addEventListener("progress", (e) => {
        const progress = (e.loaded / e.total) * 100;
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: progress,
        }));
      });
      
      // Upload
      xhr.open("POST", "/api/documents/upload");
      xhr.send(formData);
    }
  };
  
  return (
    <div className="uploader">
      <input
        type="file"
        multiple
        accept=".pdf,.docx,.md,.txt"
        onChange={(e) => setFiles(Array.from(e.target.files || []))}
      />
      <button onClick={() => handleUpload(files)}>Upload</button>
      
      {Object.entries(uploadProgress).map(([name, progress]) => (
        <div key={name} className="upload-item">
          <span>{name}</span>
          <ProgressBar value={progress} max={100} />
        </div>
      ))}
    </div>
  );
}
```

## ✅ Checklist de Validação

- [ ] Component structure bem definida
- [ ] State management implementado
- [ ] Streaming SSE testado end-to-end
- [ ] Citations renderizadas corretamente
- [ ] Upload com progress tracking funcional
- [ ] Responsividade em mobile testada
- [ ] Acessibilidade (ARIA labels) implementada

## 📝 Notas

---

**Status:** ⏳ Aguardando implementação de frontend
**Próximo:** Fase 7 — Prompt Engineering & Tuning
