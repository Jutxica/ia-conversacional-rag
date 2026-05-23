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

## 🚀 Próxima Fase: Analytics e Refinamento

### 4. WebSocket para Logs/Admin
- Notificar admin quando uma ingestão é concluída ou quando há erros.

### 5. Threshold Dinâmico Auto-ajustável
- Calibrar limites de confiança com base em dados reais de feedback dos usuários.

### 6. Cache de Embeddings Frequentes
- Evitar chamadas repetidas à OpenAI para queries similares.

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
- [x] **Token Guard** no chunking temático.
- [x] **Auditoria de Normalização** (ligaduras, HTML, Unicode).
- [x] **Search Logs & Feedback** endpoint + analytics.
- [x] **Testes Automatizados** (24 testes pytest).
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
*Documento atualizado em 23/05/2026.*
