# Fase 2: Architecture Blueprint

## 📋 Objetivo
Desenhar a arquitetura completa do sistema com componentes, fluxos, integrações e trade-offs técnicos documentados.

## 🎯 Deliverables

### D2.1 System Architecture Diagram
- [ ] Diagrama C4 Level 1 (contexto geral)
- [ ] Diagrama C4 Level 2 (containers)
- [ ] Diagrama C4 Level 3 (componentes)
- [ ] Fluxo de dados end-to-end

### D2.2 Component Design Document
- [ ] Lista de componentes principais
- [ ] Responsabilidade de cada componente
- [ ] Interfaces & contracts
- [ ] Dependências entre componentes

### D2.3 Data Flow Document
- [ ] Fluxo de ingestão de documentos
- [ ] Fluxo de query (user message → RAG → LLM → response)
- [ ] Fluxo de sessão & histórico
- [ ] Fluxo de rate limiting & billing

### D2.4 Trade-off Analysis
- [ ] Decisões técnicas justificadas
- [ ] Cada decisão com: Opção A vs Opção B, pros/cons, escolhido & por quê
- [ ] Trade-offs aceptos: qualidade vs. latência, custo vs. escalabilidade, etc.

## 🏗️ Arquitetura Proposta (Alto Nível)

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  React SPA + TypeScript + TanStack Query + WebSocket       │
└────────────────────┬────────────────────────────────────────┘
                     │ REST + WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                   API Gateway Layer                         │
│  (Auth, Rate Limiting, Request Routing, Caching)          │
└────────────────────┬────────────────────────────────────────┘
                     │ 
┌────────────────────▼────────────────────────────────────────┐
│                 Application Services                        │
│  ├─ Chat Service (conversation management)                │
│  ├─ LLM Router (model selection & fallback)               │
│  ├─ RAG Engine (retrieval + reranking)                    │
│  └─ Admin Service (tenant config, document management)    │
└────────────┬──────────────────────┬──────────────────────────┘
             │                      │
    ┌────────▼──────┐     ┌────────▼──────────────┐
    │  Async Jobs   │     │   Cache Layer        │
    │  (Celery)     │     │   (Redis)            │
    └────────┬──────┘     └────────┬──────────────┘
             │                     │
    ┌────────▼──────────────────────▼────────┐
    │         Data Layer                      │
    │  ├─ Vector DB (Pinecone/Qdrant)        │
    │  ├─ PostgreSQL (metadata, sessions)    │
    │  └─ S3/Cloud Storage (documents)       │
    └─────────────────────────────────────────┘
```

## 🔌 Integrações Externas

### LLM Providers
- [ ] OpenAI (GPT-4, GPT-4 Turbo)
- [ ] Anthropic (Claude)
- [ ] Google (Gemini)
- [ ] Fallback: Open-source (Mistral, Llama)

### Vector DB
- [ ] Pinecone (serverless)
- [ ] Qdrant (self-hosted)
- [ ] Weaviate

### Auth
- [ ] OAuth 2.0 (Google, GitHub)
- [ ] Email/Password
- [ ] API Keys

### Observability
- [ ] Logging (ELK, Datadog, CloudWatch)
- [ ] Monitoring (Prometheus, Grafana)
- [ ] Tracing (Jaeger, DataDog)

## 📐 Trade-off Decisions

### 1. Frontend Framework
**Opção A:** React SPA (lightweight, client-side routing)
**Opção B:** Next.js (SSR, SEO, built-in optimization)
**Escolha:** Next.js
**Justificativa:** melhor UX com streaming SSR, SEO para marketing, built-in api routes para proxy

### 2. Backend Language & Framework
**Opção A:** FastAPI (Python, async, fast)
**Opção B:** Node.js + Express/Fastify (JavaScript, lightweight)
**Opção C:** Go/Gin (performance, concurrency)
**Escolha:** Node.js + Fastify
**Justificativa:** rapidez de desenvolvimento, shared JS stack com frontend, ecosystem de LLM maduro

### 3. Real-time Streaming
**Opção A:** Server-Sent Events (simples, HTTP, pull-based)
**Opção B:** WebSocket (duplex, mais complexo)
**Escolha:** SSE com WebSocket fallback
**Justificativa:** SSE é simpler, stateless, melhor com load balancers; WebSocket como fallback

### 4. Vector DB
**Opção A:** Pinecone (SaaS, sem ops, $0.04/1M queries)
**Opção B:** Qdrant (self-hosted, controle, ops overhead)
**Escolha:** Pinecone para MVP, migração futura para Qdrant if needed
**Justificativa:** fast TTM, scale automático, custo previsível; Qdrant para scale posterior se ROI justifier

### 5. Caching Strategy
**Opção A:** Redis (centralizado, TTL, suporta complex types)
**Opção B:** In-memory (Node.js LRU, simples, sem network latency)
**Escolha:** Redis (session, user data) + In-memory LRU (LLM responses, embeddings)
**Justificativa:** hybrid: consistency de session com performance de local cache

### 6. Authentication
**Opção A:** JWT stateless (escalabilidade, sem servidor de session)
**Opção B:** Session-based (revogação instant, mais seguro)
**Escolha:** JWT com refresh tokens + Redis blacklist para revogação
**Justificativa:** melhor escalabilidade, revogação via Redis é rápida

## 🗂️ Folder Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.ts
│   │   │   ├── auth.ts
│   │   │   ├── documents.ts
│   │   │   └── admin.ts
│   │   └── middleware/
│   │       ├── auth.ts
│   │       ├── rate-limit.ts
│   │       └── error-handler.ts
│   ├── services/
│   │   ├── llm-router.ts
│   │   ├── rag-engine.ts
│   │   ├── chat-service.ts
│   │   └── document-service.ts
│   ├── models/
│   │   ├── conversation.ts
│   │   ├── user.ts
│   │   └── document.ts
│   ├── db/
│   │   ├── postgres.ts
│   │   └── pinecone.ts
│   └── config/
│       └── env.ts
├── docker-compose.yml
└── .env.example

frontend/
├── src/
│   ├── pages/
│   │   ├── chat/
│   │   └── admin/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── InputBox.tsx
│   │   ├── Admin/
│   │   └── Common/
│   ├── hooks/
│   │   ├── useChat.ts
│   │   └── useAuth.ts
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── stream-parser.ts
│   └── styles/
└── next.config.js
```

## ⚙️ Configuration & Deployment

- [ ] Environment variables (API keys, DB URLs, LLM model names)
- [ ] Docker images & container registry
- [ ] Kubernetes manifests (if applicable)
- [ ] CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Monitoring & alerting setup
- [ ] Backup & disaster recovery plan

## ✅ Checklist de Validação

- [ ] Arquitetura documentada com diagramas
- [ ] Todos os componentes definidos
- [ ] Fluxos de dados claros
- [ ] Integrações externas listadas
- [ ] Trade-offs justificados
- [ ] Folder structure alinhada
- [ ] User (Arquiteto) aprovou design

## 📝 Notas

*(A ser preenchido durante design)*

---

**Status:** ⏳ Aguardando arquitetura
**Próximo:** Fase 3 — LLM Integration Strategy
