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
  - **Estratégia Parent-Child (Dupla Camada):** Ingestão divide documentos em chunks pais (Parent) de ~1000 tokens para contexto e chunks filhos (Child) de ~200 tokens para alta resolução vetorial. Os vetores filhos apontam para o texto do pai nos metadados (`parent_text`). A busca recupera o contexto do pai, com fallback para busca de vizinhos ordenados.
  - **Incremental Record Manager:** Ingestão com verificação de hashes SHA-256 (`file_hash` e `content_hash`). Ignora documentos idênticos (`skipped`) e remove de forma limpa chunks antigos antes de re-processar arquivos modificados.
  - **Semantic Query Cache:** Cache baseado em tempo (TTL) para os embeddings de queries frequentes, mitigando consumo de tokens e latência.
- **Ingestão:** Suporta upload de PDFs e URLs (via Firecrawl, PyMuPDF e BeautifulSoup). Inclui token-aware chunking (com overlap dinâmico e robustez para grandes blocos de texto sem pontuação).
- **Admin:** Endpoints protegidos por JWT para gestão do corpus, CRUD de siglários/respostas validadas, edição direta de chunks via `PUT /api/admin/chunks/{chunk_id}` com re-vetorização e marcação `edited: true`, e stream de logs de ingestão via SSE.

### 2.2 Frontend (React / Vite)
- **Framework:** React com Vite, TypeScript.
- **Estilização:** CSS Vanilla (Foco em Glassmorphism e Variáveis Dinâmicas).
- **Design System:** Estética "The Scholarly Gallery", focada em leitura acadêmica, cores neutras (creme/papel), fontes Lora (Serif) e Inter.
- **Componentização:** A interface apresenta extração modular (ex: `Sidebar`, `ScholarlyHome`, `MessageList`, `CitationGrid`).
- **Funcionalidades RAG UI:** 
  - Painel lateral (Side-Drawer) dinâmico para visualização das fontes de citação em detalhes.
  - Atualização de respostas via SSE (Server-Sent Events) para efeito de digitação em tempo real (Streaming).
  - Indicadores de confiança dinâmica e gestão de histórico através de `conversation_id`.
  - **Painel de Logs SSE (`LiveLogsPanel`):** Visualização em tempo real do progresso de ingestão de arquivos e URLs.
  - **Página de Analytics:** Monitoramento de chats ativos, tamanho do banco de vetores e taxa de acerto do cache de query.
  - **Visualizador e Editor de Chunks:** Interface integrada na aba "Corpus" para inspecionar, editar chunks de texto individualmente com salvamento no backend e exibição de badge `EDITADO`.

## 3. Fluxo de Dados (RAG Flow)
1. **Pergunta:** Usuário envia a query com um "scope" (ex: Geral, Espiritualidade).
2. **Intent Detection:** O backend detecta a intenção e define os pesos (Vector vs FTS).
3. **Retrieval:** O backend busca chunks no Supabase (`hybrid_search_rrf`), usando embeddings.
4. **Context Mapping:** Caso os chunks correspondam a "filhos", o RAG extrai o `parent_text` associado nos metadados. Se indisponível (legados), recupera os chunks vizinhos (`chunk_index ± 1`).
5. **Re-ranking:** Os resultados passam pelo Cross-Encoder, retornando um Score de Confiança exato.
6. **Geração:** O modelo `gpt-4o` gera a resposta baseada exclusivamente nas fontes recuperadas, aplicando regras de citação estritas.
7. **Streaming:** A resposta é transmitida para o Frontend junto com metadados (Citações e Nível de Confiança).

## 4. Estado Atual e Próximos Passos
- **Concluído:** Ingestão de documentos via painel Admin, busca híbrida avançada com RRF, Re-ranking, Intents de Busca, Gestão de Conversas (Histórico), Painel Lateral de citações, layout Bento-Grid, refinamentos tipográficos ("The Scholarly Gallery"), Ingestão Incremental (hashes), Ingestão Parent-Child (dupla camada), Cache Semântico de query, Edição inline de Chunks no Admin com badge, e Ingestão de Logs via SSE.
- **Pendente:**
  1. Suporte a Coleções na UI (checkboxes para restringir escopo de busca).
  2. Reranking Híbrido Local (reduzir latência executando re-ranking no cliente).
  3. Visualizador de Embeddings 3D (representação geométrica dos chunks).
