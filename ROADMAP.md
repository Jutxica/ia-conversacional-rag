# Roadmap Dehon AI - Evolução e Próximos Passos

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

## 🎨 Fase de Experiência Imersiva e Design Polido ✅ Concluído

### 9. Checkboxes de Coleção/Escopo na UI ✅
- **O que é:** Filtro de pesquisa semântica na barra lateral do chat.
- **Impacto:** Permite que o pesquisador escolha quais partes do corpus consultar (ex: Obras Espirituais, Obras Sociais, Diários, Correspondência) aplicando a cláusula de filtragem dinâmica no Supabase.

### 10. Login com Imagens Ken Burns e Perfil de Usuário ✅
- **O que é:** Interface imersiva de autenticação com fotos históricas em zoom suave, e modal de perfil para customizar nome, avatar e saudações de boas-vindas.

### 11. GooeyText e Reorganização Ergonômica ✅
- **O que é:** Subtítulo com animação dinâmica e cards de sugestão uniformizados acima da caixa de pesquisa.

### 12. Controle Manual de Referências ✅
- **O que é:** Botão de toggle no cabeçalho das respostas para controle total de referências do Bento-Grid, sem auto-abertura automática para não perturbar a leitura.

### 13. Resiliência do Deploy e CORS ✅
- **O que é:** Limpeza automática de strings corrompidas de ambiente (`get_env_clean`) e liberação CORS para subdomínios do Render e Conventinho (`*.conventinho.org.br`).

---

## 🎯 Próximos Passos (Semana 3-4)

### 14. Re-ranking Híbrido Local (ONNX/WebGPU)
- **O que é:** Mover a execução do re-ranker para o navegador via WebAssembly/ONNX, reduzindo o tempo de resposta e poupando recursos do servidor.

### 15. Visualizador de Embeddings 3D (t-SNE / UMAP)
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
- [x] **Testes Automatizados** suite estendida para **30 testes unitários** no pytest.
- [x] **CRUD de siglario e blessed_answers** endpoints admin.
- [x] **Coleções / Escopo na UI:** Checkboxes de categorias na barra lateral que filtram a busca híbrida.
- [x] **Autenticação Imersiva:** Carrossel de fotos reais do Padre Dehon sob efeito Ken Burns e card glassmorphic.
- [x] **Perfil do Usuário:** Modal de edição de Nome/Avatar e saudação personalizada ("Olá, João") no ScholarlyHome.
- [x] **Refinamentos de UI:** Subtítulo animado GooeyText, Bento-Grid de sugestões reordenadas acima do chat.
- [x] **Controle Manual do Painel de Citações:** Toggle com ícone em cada mensagem do assistente para abrir/fechar o drawer bento-grid de citações, desativando a abertura automática padrão.
- [x] **Resiliência e Deploy:** `get_env_clean` contra variáveis corrompidas, fallbacks de Supabase/OpenAI e CORS para Conventinho e Render.
- [x] **Format de Chat:** Mensagens do usuário em formato bubble à direita e renderização defensiva via `safeRender`.

---
*Documento atualizado em 29/05/2026.*
