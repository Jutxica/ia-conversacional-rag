# Contexto do Sistema: Dehon AI (RAG)

## 1. Visão Geral
O **Dehon AI** é uma inteligência artificial especializada no pensamento, vida e obra do Padre Leão Dehon. Atua como um curador acadêmico, facilitando pesquisas teológicas, históricas e sociais com um alto grau de precisão, usando arquitetura RAG (Retrieval-Augmented Generation).

## 2. Arquitetura do Sistema

O sistema possui duas camadas principais:

### 2.1 Backend (Python / FastAPI)
- **Framework:** FastAPI
- **Banco de Dados:** Supabase (PostgreSQL com `pgvector`).
- **Embedding:** OpenAI `text-embedding-3-large` (reduzido a 2000 dimensões, otimizado para distância de cosseno).
- **LLM:** OpenAI `gpt-4o` para geração de respostas.
- **RAG Engine:** 
  - Busca Híbrida (Vetor + Full Text Search) com RRF (Reciprocal Rank Fusion).
  - Cross-Encoder Re-ranker (`ms-marco-MiniLM-L-6-v2`) para ordenar os melhores resultados.
  - Query Intent Detector (Detecta intenções: Histórica, Teológica, Citação, Geral) para ajustar dinamicamente os pesos da busca.
- **Ingestão:** Suporta upload de PDFs e URLs (via Firecrawl, PyMuPDF e BeautifulSoup). Inclui token-aware chunking (com overlap dinâmico).
- **Admin:** Endpoints protegidos por JWT para gestão do corpus, visualizar métricas de feedback e logs.

### 2.2 Frontend (React / Vite)
- **Framework:** React com Vite, TypeScript.
- **Estilização:** Tailwind CSS e Framer Motion.
- **Design System:** Estética "The Scholarly Gallery", focada em leitura acadêmica, cores neutras (creme/papel), fontes Lora (Serif) e Inter.
- **Componentização:** A interface já apresenta extração modular (ex: `Sidebar`, `ScholarlyHome`, `MessageList`, `CitationGrid`).
- **Funcionalidades RAG UI:** 
  - Painel lateral (Side-Drawer) dinâmico para visualização das fontes de citação em detalhes.
  - Atualização de respostas via SSE (Server-Sent Events) para efeito de digitação em tempo real (Streaming).
  - Indicadores de confiança dinâmica e gestão de histórico através de `conversation_id`.

## 3. Fluxo de Dados (RAG Flow)
1. **Pergunta:** Usuário envia a query com um "scope" (ex: Geral, Espiritualidade).
2. **Intent Detection:** O backend detecta a intenção e define os pesos (Vector vs FTS).
3. **Retrieval:** O backend busca chunks no Supabase (`hybrid_search_rrf`), usando embeddings.
4. **Re-ranking:** Os resultados passam pelo Cross-Encoder, retornando um Score de Confiança exato.
5. **Geração:** O modelo `gpt-4o` gera a resposta baseada exclusivamente nas fontes recuperadas, aplicando regras de citação estritas.
6. **Streaming:** A resposta é transmitida para o Frontend junto com metadados (Citações e Nível de Confiança).

## 4. Estado Atual e Próximos Passos
- **Concluído:** Ingestão de documentos via painel Admin, busca híbrida avançada, Re-ranking, Intents de Busca, Gestão de Conversas (Histórico), Painel Lateral de citações no frontend, otimização global do CSS (`index.css`), layout Bento-Grid e refinamentos tipográficos ("The Scholarly Gallery").
- **Pendente:** Implementação de WebSockets para logs em tempo real, Cache Semântico de embeddings para queries frequentes e Limiares dinâmicos auto-ajustáveis baseados no feedback dos usuários.
