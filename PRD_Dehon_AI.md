# Product Requirements Document (PRD) - Dehon AI

## 1. Visão Geral do Produto
**Nome do Produto:** Dehon AI  
**Descrição:** Uma plataforma de Inteligência Artificial Conversacional baseada em arquitetura RAG (Retrieval-Augmented Generation) desenhada para pesquisa, análise e diálogo com o acervo literário e histórico Dehoniano.  
**Status do Projeto:** 🟢 MVP Funcional / Em Fase de Refinamento.

## 2. Objetivos de Negócio e de Usuário
- **Acesso Democrático e Preciso:** Reduzir o tempo de pesquisa em documentos históricos.
- **Experiência Premium (Scholarly Gallery):** Interface de elite focada na imersão acadêmica (Implementado).
- **Preservação de Contexto Histórico:** Chunking avançado e boosting temático (Implementado).

---

## 5. Funcionalidades e Requisitos

### 5.1. Interface de Conversação (Frontend)
- [x] **Chat em Tempo Real:** Interface fluida com streaming (Implementado).
- [x] **Scholarly Design:** Estética minimalista e sofisticada (Implementado).
- [x] **Gestão de Histórico:** Sidebar funcional com CRUD de conversas (Implementado).
- [ ] **Indicadores de Estado (Agentic UI):** Refinar frases descritivas do processo de busca (Em progresso).
- [ ] **Citações Inline e Side Panel:** Visualização detalhada de fragmentos (Próxima etapa).

### 5.2. Motor de Busca e IA (Backend RAG)
- [x] **Busca Híbrida Inteligente:** Vetores + Keyword via Supabase (Implementado).
- [x] **Chunking com Overlap:** Preservação de semântica entre parágrafos (Implementado).
- [ ] **Etapa de Re-ranking:** Integração de Cross-Encoder (Planejado).
- [x] **Multilinguismo:** Suporte a documentos em Latim/Francês (Implementado via LLM).

---

## 7. Arquitetura Técnica Consolidada

### 7.1. Stack Tecnológico
- **Frontend:** React + TypeScript + Vite. 
- **Estilização:** CSS Vanilla (Foco em Glassmorphism e Variáveis Dinâmicas).
- **Backend:** FastAPI + Python.
- **Banco de Dados / Vector Store:** PostgreSQL + `pgvector` (Supabase).
- **Orquestração de Dev:** **Archon + Claude Code CLI**.

### 7.2. Especificações do Modelo
- **Embedding:** `text-embedding-3-large` (OpenAI).
- **LLM:** Claude 3.5 Sonnet / GPT-4o.

---

## 9. Diretrizes de Design (UI/UX)
- **Palette Midnight:** Cores profundas com acentos Antique Gold.
- **Responsividade:** Layout adaptável para dispositivos móveis com foco em touch-targets.
- **Micro-animações:** Transições suaves de 0.2s em elementos interativos.

---
*Última revisão técnica: 14 de Maio de 2026.*
rvindo apenas como uma camada inteligente de consulta e recuperação referencial.

---
*Este documento é uma entidade viva e deve ser atualizado à medida que o motor RAG avança em precisão e os componentes frontend são escalados.*
