# Roadmap Dehon AI - Próximos 15 Dias

Este documento marca as prioridades absolutas para a evolução do sistema RAG após a migração bem-sucedida para Supabase e indexação do corpus total.

## 🎯 Objetivo Principal
Elevar a confiança do sistema para 95%+ e garantir precisão acadêmica cirúrgica.

---

## 🗓️ Semana 2: Inteligência de Busca e Re-ranking ✅ Concluído

### 1. Cross-Encoder Re-ranker ✅
- **O que é:** Um segundo modelo de IA que re-classifica os 20 melhores resultados da busca híbrida.
- **Implementação:** `cross-encoder/ms-marco-MiniLM-L-6-v2` integrado em `src/rag/reranker.py`.
- **Status:** Funcional com fallback para ordenação original em caso de falha.

### 2. Query Intent (Detecção de Intenção) ✅
- **O que é:** Classificar a pergunta do usuário antes de buscar no banco.
- **Categorias:**
    - `HISTORICAL`: Datas, locais, eventos.
    - `THEOLOGICAL`: Conceitos, reflexões, espiritualidade.
    - `CITATION`: Busca por obras ou siglas específicas.
- **Impacto:** Ajuste dinâmico dos parâmetros de busca (Alpha) para cada tipo de pergunta.
- **Arquivo:** `src/rag/intent_detector.py`

### 3. Dynamic Confidence Score ✅
- **O que é:** Um cálculo de confiança baseado na probabilidade real retornada pelo Re-ranker.
- **Impacto:** Transparência total para o pesquisador sobre a confiabilidade da citação.
- **Implementado em:** `main.py` (`compute_confidence()`)

---

## 🚀 Próxima Fase: Ingestão de Alta Confiança, Edição e Escalabilidade ✅ Concluído

### 4. SSE (Server-Sent Events) para Logs de Ingestão ✅
- **O que é:** Transmissão unidirecional e estável do progresso de processamento de documentos e links do backend para o admin.
- **Implementação:** Stream de logs de progresso e estatísticas de OCR.

### 5. Record Manager e Ingestão Incremental ✅
- **O que é:** Sistema de deduplicação inteligente baseado em SHA-256.
- **Implementação:** Pula arquivos idênticos e reconstrói/remove de forma limpa os modificados.

### 6. Ingestão Parent-Child (Dupla Camada) ✅
- **O que é:** Separação estrutural de chunks de representação semântica (Children de 200 tokens) e chunks de contexto (Parent de 1000 tokens) para máxima acurácia vetorial.

### 7. Edição Inline de Chunks ✅
- **O que é:** Interface visual e endpoint `PUT /api/admin/chunks/{chunk_id}` para corrigir falhas de OCR/transcrição histórica e atualizar o embedding.

### 8. Cache Semântico de queries ✅
- **O que é:** TTLCache para os embeddings das perguntas no backend, minimizando latência e custos.

---

## 🎯 Próximos Passos (Semana 3-4)

### 9. Checkboxes de Coleção/Escopo na UI
- **O que é:** Permitir que o usuário no chat filtre o escopo de busca semântica para obras específicas (ex: Diários, Cartas, Obras Gerais).

### 10. Re-ranking Híbrido Local (ONNX/WebGPU)
- **O que é:** Mover a execução do re-ranker para o navegador via WebAssembly/ONNX, reduzindo o tempo de resposta e poupando recursos do servidor.

### 11. Visualizador de Embeddings 3D (t-SNE / UMAP)
- **O que é:** Uma interface geométrica no painel administrativo para visualizar graficamente a distribuição espacial dos vetores e clusters temáticos do acervo.

---

## ✅ Consolidação Atual
- [x] Migração para Supabase.
- [x] Indexação de ~5.100 fragmentos (Corpus Híbrido).
- [x] Implementação de Busca Híbrida (Vector + Keyword).
- [x] Chunking com sobreposição (5 parágrafos + 1 overlap).
- [x] Threshold dinâmico (Cartas: 80 chars | Outros: 200 chars).
- [x] **RRF (Reciprocal Rank Fusion)** no SQL (`hybrid_search_rrf`).
- [x] **Query Intent Detection** com ajuste dinâmico de pesos.
- [x] **Dynamic Confidence Score** via cross-encoder.
- [x] **Token Guard** no chunking temático com proteção robusta para longos parágrafos sem pontuação.
- [x] **Auditoria de Normalização** (ligaduras, HTML, Unicode).
- [x] **Search Logs & Feedback** endpoint + analytics.
- [x] **Record Manager & Ingestão Incremental** com deduplicação via SHA-256.
- [x] **Estratégia Parent-Child (Dupla Camada)** vinculada a `parent_text` nos metadados.
- [x] **Visualizador e Editor de Chunks** com badge `EDITADO` na interface e re-vetorização.
- [x] **Logs SSE & Analytics** painéis admin integrados no frontend.
- [x] **Cache Semântico** de query embeddings no backend.
- [x] **Testes Automatizados** suite estendida de 24 para **30 testes unitários** no pytest.
- [x] **CRUD de siglario e blessed_answers** endpoints admin.
- [x] **Stress Test** script de validação.
- [x] **Validation Script** para qualidade da ingestão.
- [x] **Frontend:** Painel Lateral (Side-Drawer) dinâmico para exibição de citações.
- [x] **Frontend:** Gestão correta do histórico com `conversation_id`.
- [x] **Frontend:** Streaming de respostas e metadados via SSE implementados.
- [x] **Frontend:** Otimização global de CSS (remoção de ~430 linhas de código morto no `index.css`).
- [x] **Frontend:** Bento-Grid de citações no painel lateral de referências documentais.
- [x] **Frontend:** Refinamentos tipográficos finais ("The Scholarly Gallery") com Lora (serif) no Markdown e textura sutil de papel.

---
*Documento atualizado em 25/05/2026.*
