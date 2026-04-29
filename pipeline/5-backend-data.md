# Fase 5: Backend & Data Infrastructure

## 📋 Objetivo
Desenhar e especificar backend APIs, data persistence layer, e data ingestion pipeline.

## 🎯 Deliverables

### D5.1 API Specification (OpenAPI 3.0)
- [ ] Endpoints REST com schemas
- [ ] Request/response examples
- [ ] Error codes & handling
- [ ] Rate limiting rules

### D5.2 Database Schema
- [ ] PostgreSQL ERD (users, conversations, documents, sessions)
- [ ] Indexes para performance
- [ ] Retention policies

### D5.3 Vector DB Schema
- [ ] Pinecone namespace structure
- [ ] Metadata filters
- [ ] Indexing strategy

### D5.4 Data Ingestion Pipeline
- [ ] Document upload flow
- [ ] Parsing (PDF → text)
- [ ] Chunking & embedding
- [ ] Vector DB indexing
- [ ] Error handling & recovery

### D5.5 Backend Starter Code
- [ ] Project structure (Node.js/TypeScript)
- [ ] Docker setup
- [ ] Environment configuration
- [ ] Main API routes skeleton

## 🔌 Core API Endpoints

### Chat Endpoints
```
POST /api/conversations
  - Start new conversation
  - Body: { title?: string }
  - Returns: { conversationId, createdAt }

GET /api/conversations
  - List user conversations
  - Query: { limit, offset, sortBy }
  - Returns: { conversations: [], total }

POST /api/conversations/{id}/messages
  - Send message (user or system)
  - Body: { content, role: "user"|"assistant" }
  - Returns: Streaming response (SSE)

GET /api/conversations/{id}
  - Get conversation history
  - Returns: { id, title, messages: [], createdAt }

DELETE /api/conversations/{id}
  - Delete conversation
  - Returns: { success }
```

### Document Management
```
POST /api/documents/upload
  - Upload document (multipart/form-data)
  - Body: { file, knowledgeBaseId, tags? }
  - Returns: { documentId, status, tokensUsed }

GET /api/documents
  - List documents
  - Query: { knowledgeBaseId, limit, offset }
  - Returns: { documents: [], total }

DELETE /api/documents/{id}
  - Delete document (async)
  - Returns: { deleteJobId }

GET /api/documents/{id}/status
  - Get indexing status
  - Returns: { status: "pending"|"indexed"|"failed", progress }
```

### Admin Endpoints
```
GET /api/admin/usage
  - Usage metrics (API calls, tokens, costs)
  - Query: { tenantId, period: "day"|"month" }
  - Returns: { metricsByModel, totalCost }

POST /api/admin/config
  - Update tenant config (preferred LLM model, rate limits)
  - Body: { tenantId, preferredModel, rateLimitPerMin }
  - Returns: { success }

GET /api/admin/logs
  - Debugging logs
  - Query: { level: "error"|"warn"|"info", limit }
  - Returns: { logs: [] }
```

## 🗄️ Database Schema

```sql
-- Users & Auth
CREATE TABLE users (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255),
  api_key VARCHAR(255) UNIQUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Conversations
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  tenant_id UUID,
  title VARCHAR(255),
  model_used VARCHAR(50),
  total_tokens_used INT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_tenant ON conversations(tenant_id);

-- Messages
CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  content TEXT,
  role ENUM('user', 'assistant'),
  model VARCHAR(50),
  tokens_used INT,
  citations JSONB,
  created_at TIMESTAMP
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);

-- Documents
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  tenant_id UUID,
  title VARCHAR(255),
  file_url VARCHAR(511),
  file_size_bytes INT,
  total_chunks INT,
  indexed_chunks INT,
  status ENUM('pending', 'indexing', 'indexed', 'failed'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_status ON documents(status);

-- Vector chunk metadata (for citation tracking)
CREATE TABLE vector_chunks (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  chunk_index INT,
  chunk_content TEXT,
  embedding_id VARCHAR(255), -- reference to vector DB
  created_at TIMESTAMP
);

CREATE INDEX idx_vector_chunks_document ON vector_chunks(document_id);
```

## 📦 Vector DB Schema (Pinecone)

```json
{
  "namespace": "{tenant_id}",
  "vectors": [
    {
      "id": "chunk_doc-001_chunk-05",
      "values": [0.123, 0.456, ...], // 1536-dim embedding
      "metadata": {
        "document_id": "doc_001",
        "document_title": "System Architecture Guide",
        "document_url": "/documents/system-architecture-guide",
        "chunk_index": 5,
        "page_number": 3,
        "content_preview": "The system uses a modular architecture with..."
      }
    }
  ]
}
```

## 📥 Document Ingestion Pipeline

```
1. Upload File
   └─> S3 storage
   └─> job_id returned to client
   
2. Parse Document (async job)
   ├─> Extract text (PDF → text via pdfjs or PyPDF2)
   ├─> Clean & normalize
   └─> Validate encoding
   
3. Segment Document
   ├─> Split into chunks (512 tokens + 50 overlap)
   ├─> Extract metadata (page number, headings)
   └─> Generate chunk IDs
   
4. Generate Embeddings
   ├─> Call OpenAI embeddings API (batch)
   ├─> Store embeddings (Pinecone)
   └─> Store chunk metadata (PostgreSQL)
   
5. Index & Finalize
   ├─> Mark document as "indexed"
   ├─> Trigger webhook (optional)
   └─> Clean temp files
```

### Ingestion Code Skeleton (Node.js)

```typescript
import Bull from "bull";
import PDFParser from "pdf-parse";
import { openai } from "openai";
import { Pinecone } from "@pinecone-database/pinecone";

const ingestionQueue = new Bull("document-ingestion");

ingestionQueue.process(async (job) => {
  const { documentId, fileUrl, tenantId } = job.data;
  
  // 1. Download & parse
  const text = await parseDocument(fileUrl);
  
  // 2. Chunk
  const chunks = chunkDocument(text, 512, 50);
  
  // 3. Embed
  const embeddings = await openai.embeddings.create({
    model: "text-embedding-3-large",
    input: chunks,
  });
  
  // 4. Index
  const pc = new Pinecone();
  const index = pc.Index("conversations");
  
  await index.upsert(
    embeddings.data.map((emb, i) => ({
      id: `${documentId}_${i}`,
      values: emb.embedding,
      metadata: {
        document_id: documentId,
        chunk_index: i,
        content_preview: chunks[i].substring(0, 200),
      },
    })),
    { namespace: tenantId }
  );
  
  // 5. Update DB
  await db.documents.update(documentId, {
    status: "indexed",
    indexed_chunks: chunks.length,
  });
});
```

## ✅ Checklist de Validação

- [ ] OpenAPI spec completo e testável
- [ ] Database schema normalized e performant
- [ ] Vector DB schema com metadata adequado
- [ ] Ingestion pipeline resiliência testada
- [ ] Error handling robusto
- [ ] Batch processing otimizado

## 📝 Notas

---

**Status:** ⏳ Aguardando implementação de backend
**Próximo:** Fase 6 — Frontend Implementation
