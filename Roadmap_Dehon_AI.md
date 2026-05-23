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

---

## Fase 3: Operação Avançada e Escala (A "Sustentabilidade")
**Foco:** Autonomia total e ferramentas de produtividade.

### 3.1. Auditoria e Logs de Busca
- **Painel de Analytics:** Ver quais termos os usuários estão buscando e onde a IA está falhando (respostas com "Polegar para Baixo"), permitindo subir novos documentos para cobrir essas lacunas.

### 3.2. Edição de Embeddings em Tempo Real
- **Refinamento de Resposta:** Permitir que o administrador "corrija" ou adicione notas manuais a um trecho de documento para que a IA aprenda a interpretação correta daquela passagem específica.

### 3.3. Exportação Acadêmica
- **Ferramentas de Citação:** Botão para exportar referências completas em formatos ABNT/APA direto do chat.

---

## 🛠️ Especificação Técnica da Ingestão (Para o Backend)
Para que essa sugestão "crucial" funcione, o backend (FastAPI) deve seguir este fluxo no pipeline:

1. **Recepção:** `POST /api/admin/upload` (Recebe o arquivo PDF com metadados).
2. **Extração:** Firecrawl (primário) ou PyMuPDF (fallback) extrai texto de PDFs.
3. **Normalização:** Expansão de ligaduras, NFC, remoção de HTML residual, padronização de aspas/hífens.
4. **Token-Aware Chunking:** Divisão em blocos de ~1000 tokens com overlap de 150 (tiktoken). Fragmentação de parágrafos gigantes por sentença.
5. **Metadata Injection:** Insere source_id, chunk_index, sigla, entidades e destinatário em cada fragmento.
6. **Vectorization:** OpenAI `text-embedding-3-large` (2000 dimensões).
7. **Storage:** Supabase com `pgvector` + índice HNSW + trigger FTS automático.
