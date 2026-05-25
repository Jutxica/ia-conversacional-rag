# Roadmap de Evolução: Dehon AI (Atualizado)

## Fase 1: Base de Dados e Pipeline de Ingestão (O "Coração")
**Foco:** Transformar documentos físicos/digitais em conhecimento estruturado para a IA.

### 1.1. Pipeline de Ingestão ✅
- **Upload Centralizado:** Endpoint `POST /api/admin/upload` com suporte a Firecrawl (primário) e PyMuPDF (fallback).
- **Motor de OCR e Limpeza:** Normalização com expansão de ligaduras, NFC, remoção de HTML residual, padronização de aspas/hífens.
- **Estratégia de Chunking Acadêmico:** Token-aware chunking com tiktoken (max 1000 tokens, overlap 150 tokens). Modo Thematic com sub-chunking e Sliding Window para documentos sem bookmarks.

### 1.2. Atribuição e Metadados Obrigatórios
- **Indexação por Fonte:** No momento do upload, o sistema deve exigir metadados (Título, Autor, Ano, Categoria).
- **Citações Clicáveis:** Respostas da IA devem gerar índices [n] vinculados diretamente a esses metadados.

---

## Fase 2: Experiência do Administrador e Qualidade (A "Governança")
**Foco:** Dar controle total sobre o acervo e refinar a busca.

### 2.1. Dashboard Administrativo ✅
- **Gerenciador de Documentos:** Endpoints `GET /api/admin/documents`, `DELETE /api/admin/documents/{source_id}`, `GET /api/admin/stats`, `GET /api/admin/health`.
- **CRUD de Siglas:** `GET/POST /api/admin/siglario`, `DELETE /api/admin/siglario/{sigla}`.
- **CRUD de Respostas Validadas:** `GET /api/admin/blessed`, `DELETE /api/admin/blessed/{id}`, `POST /api/bless`.

### 2.2. Busca Híbrida com Re-ranking ✅
- **Refinamento Semântico:** Cross-Encoder Re-ranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) integrado em `src/rag/reranker.py`.
- **RRF:** Função `hybrid_search_rrf` no Supabase usando Reciprocal Rank Fusion para combinar scores vetoriais e FTS.
- **Query Intent Detection:** Ajuste dinâmico dos pesos vector/FTS conforme a intenção detectada.

## Fase 3: Operação Avançada e Escala (A "Sustentabilidade") ✅ Concluído
**Foco:** Autonomia total e ferramentas de produtividade.

### 3.1. Auditoria e Logs de Ingestão/Busca ✅
- **Painel de Analytics & Logs SSE:** Monitoramento em tempo real do processamento de arquivos via Server-Sent Events. Painel de estatísticas exibindo taxa de acerto do cache semântico de query e métricas de feedback.

### 3.2. Edição de Embeddings em Tempo Real ✅
- **Visualizador e Editor de Chunks:** Permite que o administrador filtre e edite o texto bruto de qualquer fragmento (chunk) na aba "Corpus", re-vetorizando o conteúdo automaticamente via FastAPI PUT endpoint e inserindo a tag `edited: true` nos metadados.

### 3.3. Exportação Acadêmica ✅
- **Ferramentas de Citação:** Geração de citações formatadas nos padrões ABNT e APA, além de exportação no formato de metadados acadêmicos `.ris` para importação direta em ferramentas como Zotero e Mendeley.

---

## 🛠️ Especificação Técnica da Ingestão Avançada (Para o Backend)
Para garantir alta precisão de recuperação semântica e integridade de dados, o backend (FastAPI) segue este fluxo no pipeline:

1. **Recepção:** `POST /api/admin/upload` (Recebe o arquivo PDF com metadados).
2. **Integridade de Documento (Record Manager):** Calcula o hash SHA-256 do arquivo e compara com os já existentes. Se idêntico, a ingestão é pulada (`skipped`).
3. **Extração:** Firecrawl (primário) ou PyMuPDF (fallback) extrai texto de PDFs.
4. **Normalização:** Expansão de ligaduras, NFC, remoção de HTML residual, padronização de aspas/hífens.
5. **Token-Aware Chunking com Fatiamento Dual (Parent-Child):**
   - Cria chunks pais (Parent) de ~1000 tokens para reter o contexto amplo.
   - Cria chunks filhos (Child) menores de ~200 tokens com overlap de 50 tokens.
   - Aplica algoritmo de quebra word-level se blocos de texto sem pontuação estourarem o limite de segurança de tokens.
6. **Metadata Injection:** Cada chunk filho armazena o texto do pai associado nos metadados (`parent_text`), além de `file_hash`, `content_hash`, e metadados originais do documento.
7. **Limpeza Pré-Ingestão:** Remove de forma atômica todos os chunks associados a versões antigas do arquivo caso o hash seja alterado.
8. **Vectorization:** Vetoriza os chunks filhos usando o OpenAI `text-embedding-3-large` (2000 dimensões).
9. **Storage:** Supabase com `pgvector` + índice HNSW + trigger FTS automático.
10. **Busca RAG:** Queries consultam os vetores dos chunks filhos, mas retornam e alimentam o prompt da LLM com o `parent_text` para contexto refinado e robusto. Fallback automático para vizinhos (`chunk_index ± 1`) para corpus legados.
