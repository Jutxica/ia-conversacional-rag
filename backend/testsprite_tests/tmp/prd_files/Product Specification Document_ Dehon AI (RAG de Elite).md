# Product Specification Document: Dehon AI (RAG de Elite)

## 1. Visão Geral do Produto
O **Dehon AI** é um sistema avançado de Recuperação e Geração (RAG) especializado no corpus documental de Padre Leão Dehon. O sistema utiliza uma arquitetura de busca híbrida (vetorial e lexical) para fornecer respostas acadêmicas, fluidas e academicamente rigorosas, simulando a experiência de pesquisa do Google NotebookLM.

## 2. Arquitetura Técnica
### 2.1 Backend (Python/FastAPI)
- **Motor de Busca:** Busca Híbrida (HNSW Vector Search + Full Text Search) via Supabase (PostgreSQL/PGVector).
- **Embeddings:** OpenAI `text-embedding-3-large` truncado para 2000 dimensões (Matryoshka Representation).
- **LLM:** GPT-4o / GPT-4o-mini com Prompt de Sistema especializado em "Deep Research".
- **Orquestração:** FastAPI com suporte a filtros de metadados por escopo e sigla.

### 2.2 Frontend (React/TypeScript/Vite)
- **Interface:** Single Page Application (SPA) com foco em legibilidade e experiência de pesquisa.
- **Funcionalidades Chave:**
  - Seletor de Escopo (Geral, Social, Espiritual, Biográfico).
  - Exibição de Resposta Fluida com citações ancoradas.
  - Painel de Fontes com metadados de autoridade.

## 3. Especificações de Dados (Ingestão)
- **Processamento:** Script `ingest_final.py` com chunking temático baseado em bookmarks e parágrafos HTML.
- **Metadados Ricos:**
  - `document_weight`: Pesos de 5 a 30 baseados na autoridade da obra.
  - `language`: Identificação de idioma (PT/FR) para tradução automática.
  - `entities`: Mapeamento de pessoas (destinatários), lugares e conceitos.
  - `sigla`: Identificador único da obra (ex: CSC, 1LD, ASC).

## 4. Fluxos de Teste (TestSprite Focus)

### 4.1 Testes de Backend (API)
- **Endpoint `POST /api/chat`:**
  - **Cenário 1 (Precisão de Escopo):** Validar se ao selecionar o escopo "Social", o sistema retorna apenas fontes de siglas como CSC, MSO.
  - **Cenário 2 (Busca por Destinatário):** Validar se perguntas sobre "André Prévot" recuperam cartas específicas onde ele é o destinatário.
  - **Cenário 3 (Multilinguismo):** Validar se fontes em francês são traduzidas e comentadas conforme o prompt de sistema.
  - **Cenário 4 (Hibridismo):** Validar se termos técnicos exatos (ex: "oblação") elevam o score de similaridade mesmo com baixa proximidade vetorial.

### 4.2 Testes de Frontend (UI/UX)
- **Cenário 1 (Estado de Escopo):** Garantir que a tag de escopo selecionada é enviada corretamente no payload da requisição.
- **Cenário 2 (Renderização de Markdown):** Validar se as citações e referências são renderizadas corretamente (negrito, blocos de citação).
- **Cenário 3 (Tratamento de Erros):** Validar a exibição de mensagens amigáveis quando o backend retorna "Failed to fetch" ou "Confiança 0%".

## 5. Critérios de Aceitação
- **Precisão:** A resposta deve priorizar obras de maior `document_weight`.
- **Rastreabilidade:** Toda afirmação deve ser acompanhada de uma referência (Obra, Sigla, Ano).
- **Performance:** O tempo de resposta da busca híbrida deve ser inferior a 2 segundos para um banco de 10.000 chunks.
- **Confiabilidade:** O sistema deve declarar honestamente quando não encontrar evidências suficientes no escopo selecionado.

## 6. Configuração de Ambiente para Testes
- **Base URL:** `http://localhost:8000` (Backend) / `http://localhost:5173` (Frontend).
- **Database:** Supabase (Schema `documents` com extensão `pgvector`).
- **Variáveis de Ambiente Necessárias:** `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
