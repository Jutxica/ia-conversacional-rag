# Product Requirements Document (PRD) - Dehon AI

## 1. Visão Geral do Produto
**Nome do Produto:** Dehon AI  
**Descrição:** Uma plataforma de Inteligência Artificial Conversacional baseada em arquitetura RAG (Retrieval-Augmented Generation) desenhada para pesquisa, análise e diálogo com o acervo literário e histórico Dehoniano.  
**Status do Projeto:** 🟢 MVP Funcional / Em Fase de Refinamento.

## 2. Objetivos de Negócio e de Usuário
- **Acesso Democrático e Preciso:** Reduzir o tempo de pesquisa em documentos históricos.
- **Experiência Premium (Scholarly Gallery):** Interface de elite focada na imersão acadêmica (Implementado).
- **Preservação de Contexto Histórico:** Chunking avançado, fatiamento Parent-Child e boosting temático (Implementado).

---

## 3. Requisitos do Sistema e Ambiente
- **Resiliência a Deploys Cloud:** O backend deve lidar com aspas, whitespaces e strings inválidas (como "undefined") em variáveis de ambiente, comuns em plataformas como Render (Implementado).
- **Conectividade Segura (CORS):** O backend deve permitir apenas conexões de origens conhecidas e autorizadas, abrangendo domínios localhost, subdomínios Render (`.onrender.com`) e os domínios oficiais do Conventinho (`*.conventinho.org.br`) (Implementado).

---

## 4. Funcionalidades e Requisitos

### 4.1. Interface de Conversação (Frontend)
- [x] **Chat em Tempo Real:** Interface fluida com streaming SSE (Implementado).
- [x] **Scholarly Design:** Estética minimalista com creme-papel e fontes Lora/Inter (Implementado).
- [x] **Gestão de Histórico:** Sidebar funcional com CRUD de conversas (Implementado).
- [x] **Coleções e Escopo de Busca:** Checkboxes na barra lateral que permitem filtrar a busca semântica por coleções (ex: Diários, Correspondência, Obras Espirituais) (Implementado).
- [x] **Configuração de Perfil:** Modal de usuário (`ProfileModal.tsx`) para alteração de nome e avatar com saudações personalizadas (Implementado).
- [x] **Carrossel de Autenticação:** Tela de login/registro com carrossel imersivo de fotos históricas de Padre Dehon sob efeito Ken Burns (zoom suave) e card glassmorphic responsivo para mobile (Implementado).
- [x] **Controle Manual de Citações:** Toggles de referências no cabeçalho das respostas da IA para controle de leitura sob demanda. Comportamento auto-abrir desabilitado para evitar distrações (Implementado).
- [x] **Otimização de Carregamento (Splash):** Atraso reduzido para 2s no frontend, removido do admin, e exibição de spinner customizado com pulso de avatar da marca (Implementado).
- [x] **Estilo e Alinhamento do Chat:** Bolhas de mensagens do pesquisador arredondadas e alinhadas à direita com as cores da identidade visual (Implementado).
- [x] **Renderização Defensiva:** Utilização de `safeRender` para evitar quebras por objetos aninhados (React Error 31) (Implementado).

### 4.2. Motor de Busca e IA (Backend RAG)
- [x] **Busca Híbrida Inteligente:** Vetores + Keyword via Supabase (`hybrid_search_rrf`) (Implementado).
- [x] **Filtro Dinâmico por Categorias:** Suporte à filtragem por categorias/siglas passadas pelo frontend no corpo da requisição (Implementado).
- [x] **Etapa de Re-ranking:** Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) e score de confiança dinâmico (Implementado).
- [x] **Incremental Record Manager:** Deduplicação inteligente de arquivos por hash SHA-256 e limpeza de chunks modificados (Implementado).
- [x] **Fatiamento Dual (Parent-Child):** Segmentação em chunks filhos (~200 tokens) para similaridade semântica e chunks pais (~1000 tokens) para alimentação contextual da LLM (Implementado).
- [x] **Segurança e Higienização:** get_env_clean para limpeza automática de variáveis de ambiente e fallbacks de credenciais do Supabase/OpenAI (Implementado).
- [x] **Cache Semântico:** TTLCache para query embeddings no backend (Implementado).
- [x] **Painel de Logs SSE:** Monitoramento visual de uploads e OCR no admin (Implementado).

---

## 5. Arquitetura Técnica Consolidada

### 5.1. Stack Tecnológico
- **Frontend:** React + TypeScript + Vite.
- **Estilização:** CSS Vanilla (Glassmorphism, Bento-Grid e CSS Variables).
- **Backend:** FastAPI + Python.
- **Banco de Dados / Vector Store:** PostgreSQL + `pgvector` (Supabase).
- **Orquestração de Dev:** Archon + Claude Code CLI.

### 5.2. Especificações do Modelo
- **Embedding:** `text-embedding-3-large` (OpenAI), 2000 dimensões.
- **LLM:** GPT-4o / Claude 3.5 Sonnet.
- **Re-ranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (HuggingFace).

---

## 6. Diretrizes de Design (UI/UX)
- **Palette Midnight:** Cores profundas com acentos Antique Gold.
- **Responsividade:** Layout adaptável para dispositivos móveis com foco em touch-targets e fundos adaptativos.
- **Micro-animações:** Transições suaves em elementos interativos e GooeyText para animações fluidas de títulos/subtítulos.

---
*Última revisão técnica: 29 de Maio de 2026.*
